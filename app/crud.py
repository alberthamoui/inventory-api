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
