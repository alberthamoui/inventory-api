from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from .schemas import ProductCreate, MovementCreate
from datetime import datetime, timezone

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= PRODUCTS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def createProduct(db: Connection, data: ProductCreate) -> dict:
    try:
        result = db.execute(
            text("""
                INSERT INTO Product (name, ean13, quantity, alert_threshold)
                VALUES (:name, :ean13, :quantity, :alert_threshold)
            """),
            {
                "name": data.name,
                "ean13": data.ean13,
                "quantity": data.quantity,
                "alert_threshold": data.alert_threshold,
            }
        )
    except IntegrityError as e:
        msg = str(e.orig).lower()

        if "unique" in msg:
            raise HTTPException(status_code=400, detail="EAN already exists")

        if "check" in msg:
            raise HTTPException(status_code=400, detail="Invalid value (negative or bad EAN)")

        raise HTTPException(status_code=400, detail="Invalid data") from e

    row = db.execute(
        text("SELECT * FROM Product WHERE id = :id"),
        {"id": result.lastrowid},
    ).mappings().one()

    return dict(row)

def listProducts(db: Connection) -> list[dict]:
    rows = db.execute(text("""
        SELECT Product.* FROM Product
        LEFT JOIN DeletedProduct ON Product.id = DeletedProduct.product_id
        WHERE DeletedProduct.product_id IS NULL
    """)).mappings().all()
    return [dict(r) for r in rows]

def getProductById(db: Connection, product_id: int) -> dict:
    row = db.execute(text("""
        SELECT Product.*
        FROM Product
        LEFT JOIN DeletedProduct ON Product.id = DeletedProduct.product_id
        WHERE DeletedProduct.product_id IS NULL
        AND Product.id = :id
    """), {"id": product_id}).mappings().one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)

def deleteProductById(db: Connection, product_id: int) -> dict:
    row = db.execute(text("""
        SELECT Product.*
        FROM Product
        LEFT JOIN DeletedProduct ON Product.id = DeletedProduct.product_id
        WHERE DeletedProduct.product_id IS NULL
        AND Product.id = :id
    """), {"id": product_id}).mappings().one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        db.execute(
            text("INSERT INTO DeletedProduct (product_id) VALUES (:id)"),
            {"id": product_id},
        )
    except IntegrityError:
        raise HTTPException(status_code=404, detail="Product not found (already deleted)")

    return dict(row)

def updateProduct(db: Connection, product_id: int, data: ProductCreate) -> dict:
    exists = db.execute(text("""
        SELECT Product.id
        FROM Product
        LEFT JOIN DeletedProduct ON Product.id = DeletedProduct.product_id
        WHERE DeletedProduct.product_id IS NULL
        AND Product.id = :id
    """), {"id": product_id}).mappings().one_or_none()

    if not exists:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        db.execute(text("""
            UPDATE Product
            SET name = :name, ean13 = :ean13, quantity = :quantity, alert_threshold = :alert_threshold
            WHERE id = :id
        """), {
            "name": data.name,
            "ean13": data.ean13,
            "quantity": data.quantity,
            "alert_threshold": data.alert_threshold,
            "id": product_id,
        })
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Invalid data or EAN13 already exists") from e

    updated = db.execute(
        text("SELECT * FROM Product WHERE id = :id"),
        {"id": product_id},
    ).mappings().one()

    return dict(updated)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= MOVEMENTS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def createMovement(db: Connection, product_id: int, data: MovementCreate) -> dict:
    product = db.execute(text("""
        SELECT Product.id, Product.quantity
        FROM Product
        LEFT JOIN DeletedProduct ON Product.id = DeletedProduct.product_id
        WHERE DeletedProduct.product_id IS NULL
        AND Product.id = :id
    """), {"id": product_id}).mappings().one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    currentQnt = product["quantity"]

    if data.type == "out" and currentQnt - data.quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    dateValue = data.date.isoformat() if data.date else datetime.now(timezone.utc).isoformat()

    try:
        result = db.execute(text("""
            INSERT INTO Movement (product_id, type, quantity, date, reason)
            VALUES (:product_id, :type, :quantity, :date, :reason)
        """), {
            "product_id": product_id,
            "type": data.type,
            "quantity": data.quantity,
            "date": dateValue,
            "reason": data.reason,
        })

        newQnt = currentQnt + data.quantity if data.type == "in" else currentQnt - data.quantity

        db.execute(
            text("UPDATE Product SET quantity = :q WHERE id = :id"),
            {"q": newQnt, "id": product_id},
        )

    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Invalid movement") from e

    row = db.execute(
        text("SELECT * FROM Movement WHERE id = :id"),
        {"id": result.lastrowid},
    ).mappings().one()

    return dict(row)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= EXTRAS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def listAlerts(db: Connection) -> list[dict]:
    rows = db.execute(text("""
        SELECT Product.*
        FROM Product
        LEFT JOIN DeletedProduct ON Product.id = DeletedProduct.product_id
        WHERE DeletedProduct.product_id IS NULL
        AND Product.quantity <= Product.alert_threshold
    """)).mappings().all()
    return [dict(r) for r in rows]

def importProducts(db: Connection, rows: list[dict]) -> dict:
    created = 0
    failed = 0
    errors = []
    ids = []

    for idx, row in enumerate(rows, start=2):
        try:
            product_data = {
                "name": row["name"],
                "ean13": row["ean13"],
                "quantity": int(row["quantity"]),
                "alert_threshold": int(row["alert_threshold"])
            }
            new_id = createProduct(db, ProductCreate(**product_data))["id"]
            created += 1
            ids.append(new_id)

        except HTTPException as e:
            failed += 1
            errors.append({"line": idx, "ean13": row.get("ean13"), "error": e.detail})

        except Exception:
            failed += 1
            errors.append({"line": idx, "ean13": row.get("ean13"), "error": "Invalid data format"})

    return {"created": created, "ids": ids, "failed": failed, "errors": errors}
