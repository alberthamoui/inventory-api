import sqlite3
from fastapi import HTTPException
from .schemas import ProductCreate

def createProduct(db: sqlite3.Connection, data: ProductCreate) -> dict:
    try:
        cur = db.execute(
            """
                INSERT INTO Product (name, ean13, quantity, alert_threshold)
                VALUES (?, ?, ?, ?)
            """,
            (data.name, data.ean13, data.quantity, data.alert_threshold),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        # EAN duplicated / CHECK do ean13 / negative quantity
        raise HTTPException(status_code=400, detail="Invalid product or EAN13 already exists") from e

    row = db.execute("SELECT * FROM Product WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)

def listProducts(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT * FROM Product").fetchall()
    return [dict(r) for r in rows]

def getProductById(db, product_id: int) -> dict:
    row = db.execute("SELECT * FROM Product WHERE id = ?",(product_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)

def deleteProductById(db, product_id: int) -> dict:
    row = db.execute("SELECT * FROM Product WHERE id = ?",(product_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    db.execute("DELETE FROM Product WHERE id = ?", (product_id,))
    db.commit()
    return dict(row)


def updateProduct(db: sqlite3.Connection, product_id: int, data: ProductCreate) -> dict:
    row = db.execute("SELECT id FROM Product WHERE id = ?", (product_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        db.execute(
            """
            UPDATE Product
            SET name = ?, ean13 = ?, quantity = ?, alert_threshold = ?
            WHERE id = ?
            """,
            (data.name, data.ean13, data.quantity, data.alert_threshold, product_id),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        # EAN duplicated or CHECK failed
        raise HTTPException(status_code=400, detail="Invalid data or EAN13 already exists") from e

    updated = db.execute("SELECT * FROM Product WHERE id = ?", (product_id,)).fetchone()
    return dict(updated)
