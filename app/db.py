import sqlite3
from sqlalchemy import create_engine

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= DATABASE =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
DATABASE_URL = "sqlite:///inventory.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

def createTables(conn: sqlite3.Connection):
    ean13Glob = "[0-9]" * 13

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS Product (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            ean13           TEXT NOT NULL UNIQUE,
            quantity        INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
            alert_threshold INTEGER NOT NULL DEFAULT 0 CHECK (alert_threshold >= 0),

            CHECK (length(ean13) = 13 AND ean13 GLOB '{ean13Glob}')
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Movement (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type       TEXT NOT NULL CHECK (type IN ('in', 'out')),
            quantity   INTEGER NOT NULL CHECK (quantity > 0),
            date       TEXT NOT NULL DEFAULT (CURRENT_DATE),
            reason     TEXT,

            FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE RESTRICT
            
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS DeletedProduct (
            product_id INTEGER PRIMARY KEY,
            deleted_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),

            FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()

def configure_sqlite_conn(conn: sqlite3.Connection):
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

def init_db():
    conn = engine.raw_connection()
    try:
        configure_sqlite_conn(conn)
        createTables(conn)
    finally:
        conn.close()

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= FAST API =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def getDb():
    conn = engine.raw_connection()
    configure_sqlite_conn(conn)
    try:
        yield conn
    finally:
        conn.close()

def main():
    init_db()
    print("inventory.db initialized.")

if __name__ == "__main__":
    main()
