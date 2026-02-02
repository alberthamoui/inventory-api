import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import createTables
from app.db import getDb
from io import BytesIO


# ======================== TEST DB ========================
@pytest.fixture
def db_conn():
    # mesma conexão para o teste inteiro
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    createTables(conn)
    yield conn
    conn.close()

@pytest.fixture
def client(db_conn):
    def override_get_db():
        # sempre retorna a MESMA conexão
        return db_conn

    app.dependency_overrides[getDb] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

def createProduct(client, name="Tylenol", ean13="1234567890123", quantity=10, alert_threshold=2):
    payload = {
        "name": name,
        "ean13": ean13,
        "quantity": quantity,
        "alert_threshold": alert_threshold,
    }
    return client.post("/products", json=payload)

# ======================== TESTS POST ========================
def test_create_product_success(client):
    response = createProduct(client)
    data = response.json()

    assert response.status_code == 200
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["name"] == "Tylenol"
    assert data["quantity"] == 10

def test_create_product_invalid_ean13(client):
    response = createProduct(client, ean13="123456789AAA")
    assert response.status_code == 422

def test_create_product_negative_quantity(client):
    response = createProduct(client, quantity=-1)
    assert response.status_code in [400, 422]

def test_create_product_duplicate_ean13(client):
    r1 = createProduct(client, name="A", ean13="1111111111111")
    assert r1.status_code==200

    r2 = createProduct(client, name="B", ean13="1111111111111")
    assert r2.status_code in [400, 409] # Mine returns 400 | 409 is the "official" code for conflict


# ======================== TESTS GET ========================
def test_get_products_lists_created(client):
    createProduct(client, name="Listed", ean13="1111111111111")

    response = client.get("/products")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert any(p["ean13"] == "1111111111111" for p in data)
    assert not any(p["ean13"] == "2222222222222" for p in data)

def test_get_product_by_id(client):
    created = createProduct(client, name="GetMe", ean13="1111111111111").json()
    productId = created["id"]

    response = client.get(f"/products/{productId}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == productId
    assert data["ean13"] == "1111111111111"

    response2 = client.get("/products/2222222222222")
    assert response2.status_code == 404

# ======================== IMPORT TESTS ========================
def make_csv(content: str):
    return {
        "file": ("products.csv", content.encode("utf-8"), "text/csv")
    }

def test_post_products_import_creates_many(client):
    csv_content = (
        "name,ean13,quantity,alert_threshold\n"
        "R1,1111111111111,10,1\n"
        "R2,2222222222222,20,2\n"
        "R3,3333333333333,30,3\n"
    )

    response = client.post("/products/import", files=make_csv(csv_content))
    data = response.json()

    assert response.status_code == 201
    assert data["created"] == 3
    assert data["failed"] == 0
    assert isinstance(data["ids"], list)
    assert len(data["ids"]) == 3

def test_post_products_import_invalid_item(client):
    csv_content = (
        "name,ean13,quantity,alert_threshold\n"
        "R1,1111111111111,1,0\n"
        "R2,AAAAAAAAAAAAA,1,0\n"
    )
    response = client.post("/products/import", files=make_csv(csv_content))
    assert response.status_code==207


# ======================== DELETE TESTS ========================
def test_full_delete(client): # create -> move -> delete -> get
    created = createProduct(client).json()
    productId = created["id"]

    move = client.post(f"/products/{productId}/movements", json={
        "type": "out",
        "quantity": 5,
        "reason": "Testing delete"
    })
    assert move.status_code == 200

    delete = client.delete(f"/products/{productId}")
    assert delete.status_code==200

    get = client.get(f"/products/{productId}")
    assert get.status_code == 404

    delete = client.delete(f"/products/{productId}")
    assert delete.status_code==404


# ======================== MOVEMENT TESTS ========================
def test_movement_stock_negative(client):
    created = createProduct(client, quantity=5).json()
    productId = created["id"]

    response = client.post(f"/products/{productId}/movements", json={
        "type": "out",
        "quantity": 10
    })

    assert response.status_code == 400

def test_deleted_product_movements(client):
    created = createProduct(client).json()
    productId = created["id"]
    client.delete(f"/products/{productId}")

    response = client.post(f"/products/{productId}/movements", json={
        "type": "in",
        "quantity": 1
    })

    assert response.status_code == 404




# ======================== ALERTS TESTS ========================
def test_low_stock_alert(client):
    createProduct(client, name="R1", ean13="1111111111111", quantity=2, alert_threshold=5)
    createProduct(client, name="R2", ean13="2222222222222", quantity=10, alert_threshold=5)

    response = client.get("/alerts")
    data = response.json()

    assert any(p["ean13"] == "1111111111111" for p in data)
    assert not any(p["ean13"] == "2222222222222" for p in data)