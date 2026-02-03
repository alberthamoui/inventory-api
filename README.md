# Inventory Management API

REST API to manage a single pharmacy inventory: products, stock movements, low-stock alerts, and bulk import via CSV.

## Features

- **Products CRUD**
  - `POST /products` — create product
  - `GET /products` — list active products
  - `GET /products/{id}` — get product details
  - `PUT /products/{id}` — update product (full replace)
  - `DELETE /products/{id}` — soft-delete product
- **Stock movements**
  - `POST /products/{id}/movements` — register stock movement (`in` / `out`)
- **Alerts**
  - `GET /alerts` — list products where `quantity <= alert_threshold`
- **CSV import**
  - `POST /products/import` — bulk upload CSV (`name,ean13,quantity,alert_threshold`)
- **Health check**
  - `GET /status` — API health check

---

## Tech Stack

- Python 3.10+
- FastAPI
- SQLite
- SQLAlchemy (engine only)
- pytest

---

## Project Structure

```
app/
  main.py      # FastAPI routes
  schemas.py   # Pydantic request/response schemas
  crud.py      # DB operations + business rules
  db.py        # SQLite engine/connection + table creation
tests/
  test_api.py  # API integration tests
inventory.db   # SQLite database (created at runtime)
README.md
DECISIONS.md   # Technical decisions and ambiguities resolved
requirements.txt
pytest.ini
```

---

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize the database

```bash
python -m app.db
```

This creates `inventory.db` with the required tables (`Product`, `Movement`, `DeletedProduct`).

---

## Running the API

From the repository root:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

**Interactive documentation:**
- Swagger UI: `http://127.0.0.1:8000/docs`

---

## Running Tests

```bash
pytest -v
```

Tests use an in-memory SQLite database (`:memory:`) and override the `getDb` dependency to maintain a single connection throughout the test session.

---

## API Reference

### HTTP Status Codes

| Code    | Name                 | When it occurs |
|---------|----------------------|----------------|
| **200** | OK                   | Successful GET/POST/PUT/DELETE operations |
| **201** | Created              | `POST /products/import` — all CSV products created successfully |
| **207** | Multi-Status         | `POST /products/import` — partial success (some products created, some failed). Response includes: `created`, `ids`, `failed`, `errors` |
| **400** | Bad Request          | Invalid file type; invalid CSV headers; no products created; duplicate EAN13; invalid values (negative quantities, malformed EAN); insufficient stock for `out` movement |
| **404** | Not Found            | Product not found or soft-deleted; attempting to delete an already deleted product |
| **422** | Unprocessable Entity | FastAPI/Pydantic validation error: malformed JSON, missing required fields, wrong types, EAN13 length ≠ 13 |

---

## Usage Examples

### Health Check

```bash
curl -X GET http://127.0.0.1:8000/status
```

### Products

**List all active products:**
```bash
curl -X GET http://127.0.0.1:8000/products
```

**Get product by ID:**
```bash
curl -X GET http://127.0.0.1:8000/products/1
```

**Create product:**
```bash
curl -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Paracetamol 500mg", "ean13": "7891234567890", "quantity": 100, "alert_threshold": 10}'
```

**Update product (full replacement):**
```bash
curl -X PUT http://127.0.0.1:8000/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Paracetamol 500mg (updated)", "ean13": "7891234567890", "quantity": 80, "alert_threshold": 15}'
```

**Soft-delete product:**
```bash
curl -X DELETE http://127.0.0.1:8000/products/1
```

### Stock Movements

**Register stock entry:**
```bash
curl -X POST http://127.0.0.1:8000/products/1/movements \
  -H "Content-Type: application/json" \
  -d '{"type": "in", "quantity": 50, "reason": "Supplier receipt"}'
```

**Register stock exit:**
```bash
curl -X POST http://127.0.0.1:8000/products/1/movements \
  -H "Content-Type: application/json" \
  -d '{"type": "out", "quantity": 5, "reason": "Sale"}'
```

**Movement with optional date (ISO 8601):**
```bash
curl -X POST http://127.0.0.1:8000/products/1/movements \
  -H "Content-Type: application/json" \
  -d '{"type": "in", "quantity": 10, "date": "2025-02-03T12:00:00Z", "reason": "Adjustment"}'
```

### Alerts

**List low-stock products:**
```bash
curl -X GET http://127.0.0.1:8000/alerts
```

### CSV Import

**Import products from CSV:**
```bash
curl -X POST http://127.0.0.1:8000/products/import \
  -F "file=@products.csv"
```

**CSV file format:**

The file must have exactly these columns (first line = header):

```csv
name,ean13,quantity,alert_threshold
Paracetamol 500mg,7891234567890,100,10
Ibuprofen 400mg,7891234567891,50,5
Dipyrone 500mg,7891234567892,200,20
Vitamin C 1g,7891234567893,80,15
```

**Column validation:**
- `name`: text, product name
- `ean13`: exactly 13 digits (0–9)
- `quantity`: integer ≥ 0
- `alert_threshold`: integer ≥ 0

---

## Technical Details

### Soft Delete

The API implements **soft delete** to preserve data integrity and movement history:

**How it works:**
- `DELETE /products/{id}` does NOT remove the record from the `Product` table
- Instead, it inserts the `product_id` into the `DeletedProduct` table
- The `Product` record remains in the database

**Implementation:**
- Table: `DeletedProduct(product_id PRIMARY KEY, deleted_at TIMESTAMP)`
- Foreign key: `product_id` → `Product(id)` with `ON DELETE CASCADE`

**Effect:**
All queries for "active" products use `LEFT JOIN DeletedProduct` and filter `WHERE DeletedProduct.product_id IS NULL`. Soft-deleted products are excluded from:
- `GET /products`
- `GET /products/{id}`
- `PUT /products/{id}`
- `POST /products/{id}/movements`
- `GET /alerts`

**Behavior:**
- Attempting to delete an already deleted product returns `404` with message: `"Product not found (already deleted)"`

### EAN-13 Format

**EAN-13** (European Article Number) is a 13-digit barcode standard.

**Validation rules:**
- **Length:** exactly 13 characters
- **Characters:** only digits (0–9)
- **Uniqueness:** each EAN13 must be unique across all products

**Implementation:**
- **Pydantic schema:** `ean13: str = Field(min_length=13, max_length=13)`
- **Database constraint:** `CHECK (length(ean13) = 13 AND ean13 GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]')`
- **Unique constraint:** `UNIQUE(ean13)`

**Examples:**
- ✅ Valid: `7891234567890`, `0000000000001`
- ❌ Invalid: `789123456789` (12 digits), `78912345678901` (14 digits), `789123456789A` (contains letter)

---

## Technical Decisions

See `DECISIONS.md` for detailed explanations.

---
