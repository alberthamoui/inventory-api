import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import createTables
from app.db import getDb

# ======================== TEST DB ========================
def override_get_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    createTables(conn)
    try:
        yield conn
    finally:
        conn.close()


app.dependency_overrides[getDb] = override_get_db

client = TestClient(app)


# ======================== TESTS ========================
def test_create_product_success():
    payload = {
        "name": "Tylenol",
        "ean13": "1234567890123",
        "quantity": 10,
        "alert_threshold": 2
    }

    response = client.post("/products", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["id"] is not None
    assert data["name"] == "Tylenol"
    assert data["quantity"] == 10
