## General
- Added automatic DB/table creation on startup to simplify local setup.

## Constraints (extras)
- Enforced `quantity >= 0` and `alert_threshold >= 0` in DB to ensure non-negative values.
- Enforced `movement.quantity > 0`.

## Foreign Keys
- Used `ON DELETE RESTRICT` for `Movement → Product`.
- Prevents deleting products with movement history.

## Movement Date
- Implemented default date at DB level using `CURRENT_DATE`.
- Decided to store only date (not timestamp) for movements.
