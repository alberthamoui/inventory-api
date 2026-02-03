## General
- DB and table creation is done **by command** (`python -m app.db`, which runs `init_db()` / `createTables()`), not automatically when the API starts. This avoids unexpected schema changes at runtime and keeps API startup lightweight.

## 1) SQLAlchemy access style
**Ambiguity:** the spec mentions SQLAlchemy, but the project also uses `sqlite3` directly.  
**Decision:** use **raw SQL via `sqlite3`** for queries, while using **SQLAlchemy’s engine** only to manage the SQLite connection (`check_same_thread=False`).

## 2) Product delete semantics
**Ambiguity:** `DELETE /products/{id}` is required, but the system also stores movement history, and a `Movement → Product` FK makes hard deletes risky.  
**Decision:** implement **soft delete** by inserting into a `DeletedProduct` table instead of deleting from `Product`.
- Deleted products are excluded from listing, fetching, updating, alerts, and movements.
- This preserves referential integrity and avoids orphan movement rows.

## 3) FK behavior between Movement and Product
**Ambiguity:** what should happen if a product with movements is deleted.  
**Decision:** keep `Movement.product_id` with `ON DELETE RESTRICT` and rely on soft delete for the API behavior (hard delete is intentionally not supported).

## 4) Movement date format and timezone
**Ambiguity:** the spec says “date” (not provided → current date) but does not define format/timezone.  
**Decision:** accept an optional `datetime` (`MovementCreate.date`). If missing, use **current UTC time** and store `Movement.date` as an **ISO-8601 text** string.

## 5) CSV import error handling
**Ambiguity:** how to report partial failures and which status code to use.  
**Decision:** return a structured summary:
- `created`, `ids`, `failed`, and `errors[]`
- Use status codes:
  - **201** if all rows succeed
  - **207** if partially successful
  - **400** if no rows were created

## 6) Update behavior (PUT)
**Ambiguity:** should updates be partial (PATCH-like) or full replacement?  
**Decision:** use PUT as a **full replacement** with the same schema as creation (`ProductCreate`). No partial update endpoint.

## 7) EAN-13 validation
**Ambiguity:** the spec calls it “ean13” but may not specify strict validation rules.  
**Decision:** validate as **exactly 13 characters** at the API layer (Pydantic `min_length=13, max_length=13`) and treat it as **TEXT** in SQLite.

