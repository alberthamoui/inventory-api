from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection

import csv
from typing import List

from .crud import *
from .schemas import ProductCreate, MovementCreate
from .db import getDb

app = FastAPI(title="Inventory API")

@app.get("/status")
def status(db: Connection = Depends(getDb)):
    db.execute(text("SELECT 1")).fetchone()
    return {"status": "ok", "db": "connected"}

@app.post("/products/import")
async def post_products_import(file: UploadFile = File(...), db: Connection = Depends(getDb)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")

    content = await file.read()
    decoded = content.decode("utf-8").splitlines()

    reader = csv.DictReader(decoded)

    required_fields = {"name", "ean13", "quantity", "alert_threshold"}
    if set(reader.fieldnames) != required_fields:
        raise HTTPException(status_code=400, detail="Invalid CSV headers")

    rows = list(reader)
    result = importProducts(db, rows)
    created = result["created"]
    failed = result["failed"]
    if created == 0:
        return JSONResponse(status_code=400, content=result)
    elif failed > 0 and created > 0:
        return JSONResponse(status_code=207, content=result)
    return JSONResponse(status_code=201, content=result)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= PRODUCTS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@app.post("/products")
def post_products(payload: ProductCreate, db: Connection = Depends(getDb)):
    return createProduct(db, payload)

@app.get("/products")
def get_products(db: Connection = Depends(getDb)):
    return listProducts(db)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= PRODUCT BY ID =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@app.get("/products/{product_id}")
def get_product_by_id(product_id: int, db: Connection = Depends(getDb)):
    return getProductById(db, product_id)

@app.delete("/products/{product_id}")
def delete_product_by_id(product_id: int, db: Connection = Depends(getDb)):
    return deleteProductById(db, product_id)

@app.put("/products/{product_id}")
def put_product(product_id: int, payload: ProductCreate, db: Connection = Depends(getDb)):
    return updateProduct(db, product_id, payload)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= MOVEMENTS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@app.post("/products/{id}/movements")
def post_product_movements(id: int, payload: MovementCreate, db: Connection = Depends(getDb)):
    return createMovement(db, id, payload)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= EXTRAS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@app.get("/alerts")
def get_alerts(db: Connection = Depends(getDb)):
    return listAlerts(db)