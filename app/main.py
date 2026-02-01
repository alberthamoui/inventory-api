from fastapi import FastAPI, Depends
import sqlite3
from .db import getDb

app = FastAPI(title="Inventory API")

@app.get("/status")
def status(db: sqlite3.Connection = Depends(getDb)):
    db.execute("SELECT 1").fetchone()
    return {"status": "ok", "db": "connected"}
