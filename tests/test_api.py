import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import createTables
from app.db import getDb

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


# ======================== BATCH TESTS ========================
def test_post_products_batch_creates_many(client):
    payload = [
        {"name": "R1", "ean13": "1111111111111", "quantity": 10, "alert_threshold": 1},
        {"name": "R2", "ean13": "2222222222222", "quantity": 20, "alert_threshold": 2},
        {"name": "R3", "ean13": "3333333333333", "quantity": 30, "alert_threshold": 3},
    ]

    r = client.post("/products/batch", json=payload)
    data = r.json()

    assert r.status_code in (200, 201)
    assert data["created"] == 3
    assert isinstance(data["ids"], list)
    assert len(data["ids"]) == 3

def test_post_products_batch_invalid_item(client):
    payload = [
        {"name": "R1", "ean13": "1111111111111", "quantity": 1, "alert_threshold": 0},
        {"name": "R2", "ean13": "AAAAAAAAAAAAA", "quantity": 1, "alert_threshold": 0},
    ]

    r = client.post("/products/batch", json=payload)
    assert r.status_code==207


# ======================== DELETE TESTS ========================
