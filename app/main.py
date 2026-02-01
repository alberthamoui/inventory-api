from fastapi import FastAPI, Depends
import sqlite3

from .crud import *
from .schemas import ProductCreate
from .db import getDb 

app = FastAPI(title="Inventory API")

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= TEST =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@app.get("/status")
def status(db: sqlite3.Connection = Depends(getDb)):
    db.execute("SELECT 1").fetchone()
    return {"status": "ok", "db": "connected"}

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= PRODUCTS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@app.post("/products")
def post_products(payload: ProductCreate, db: sqlite3.Connection = Depends(getDb)):
    return createProduct(db, payload)

@app.get("/products")
def get_products(db: sqlite3.Connection = Depends(getDb)):
    return listProducts(db)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= PRODUCT BY ID =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@app.get("/products/{product_id}")
def get_product_by_id(product_id: int, db: sqlite3.Connection = Depends(getDb)):
    return getProductById(db, product_id)

@app.delete("/products/{product_id}")
def delete_product_by_id(product_id: int, db: sqlite3.Connection = Depends(getDb)):
    return deleteProductById(db, product_id)

@app.put("/products/{product_id}")
def put_product(product_id: int, payload: ProductCreate, db: sqlite3.Connection = Depends(getDb)):
    return updateProduct(db, product_id, payload)
