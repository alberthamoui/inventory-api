# Inventory Management API

REST API to manage a single pharmacy inventory: products, stock movements, low-stock alerts, and bulk import via CSV.

## Features
- **Products CRUD**
  - `POST /products` create product
  - `GET /products` list active products
  - `GET /products/{id}` get product details
  - `PUT /products/{id}` update product (full replace)
  - `DELETE /products/{id}` soft-delete product
- **Stock movements**
  - `POST /products/{id}/movements` (`in` / `out`) updates product stock
- **Alerts**
  - `GET /alerts` products where `quantity <= alert_threshold`
- **CSV import**
  - `POST /products/import` upload CSV (`name,ean13,quantity,alert_threshold`)
- **Health check**
  - `GET /status`

## Tech stack

- Python 3.10+
- FastAPI
- SQLite
- SQLAlchemy engine
- pytest

## Project structure

```
app/
  main.py      # FastAPI routes
  schemas.py   # Pydantic request schemas
  crud.py      # DB operations + business rules
  db.py        # SQLite engine/connection table creation
tests/
  test_api.py
inventory.db   # local SQLite database (created/used at runtime)
README.md      
DECISIONS.md
requirements.txt
pytest.ini
```

## Setup

### 1) Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Initialize the database

```bash
python -m app.db
```

## Run the API
From the repository root:

```bash
uvicorn app.main:app --reload
```

Open interactive docs:
- Swagger UI: `http://127.0.0.1:8000/docs`

## Running tests

```bash
pytest -v
```

Tests use an in-memory SQLite database (`:memory:`) and override the `getDb` dependency to keep a single connection for the test session.

## Technical choices

See `DECISIONS.md` for the main ambiguities in the spec and how they were resolved.
