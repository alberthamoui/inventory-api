## General
- Added automatic DB/table creation on startup to simplify local setup.

## 1) SQLAlchemy access style
- **Raw SQL via `sqlite3`**, while using **SQLAlchemy’s engine** only to manage the SQLite connection with `check_same_thread=False`.

## 2) Product delete semantics
**Ambiguity:** `DELETE /products/{id}` is required, but the system also stores movement history, and a `Movement → Product` FK makes hard deletes tricky.  
**Decision:** implement **soft delete** by inserting into a `DeletedProduct` table instead of deleting from `Product`.
- Deleted products are excluded from listing, fetching, updating, alerts, and movements.
- This preserves referential integrity and avoids orphan movement rows.

## 3) FK behavior between Movement and Product
**Ambiguity:** how to handle deletion when movements exist.  
**Decision:** keep `Movement.product_id` with `ON DELETE RESTRICT` and rely on soft delete for the API behavior. (Hard delete is intentionally not supported by the API.)

## 4) Movement date format and timezone
**Ambiguity:** the spec says “date” (not provided → current date) but does not define format/timezone.  
**Decision:** accept an optional `datetime` (`MovementCreate.date`). If missing, use **current UTC time** and store `Movement.date` as an **ISO-8601 text** string.

## 5) CSV import error handling  
**Decision:** return a structured summary:
- `created`, `ids`, `failed`, and `errors[]`
- Use status codes:
  - **201** if all rows succeed
  - **207** if partially successful
  - **400** if no rows were created

## 6) Update behavior (PUT) 
**Ambiguity:** should updates be partial (PATCH-like) or full replacement? 
**Decision:** use PUT as a **full replacement** with the same schema as creation (ProductCreate). No partial update endpoint.