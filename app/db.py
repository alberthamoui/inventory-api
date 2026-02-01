import sqlite3
from pathlib import Path

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= DATABASE =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
DB_PATH = Path("inventory.db")

def createConnection(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def createTables(conn: sqlite3.Connection): # DUVIDA: relation between quantity/alert_threshold?
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

    conn.commit()

def getConnection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= FAST API =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def getDb():
    conn = getConnection()
    try:
        yield conn
    finally:
        conn.close()

def main():
    conn = createConnection(DB_PATH)
    try:
        createTables(conn)
        print(f"Tabelas criadas com sucesso em: {DB_PATH.resolve()}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
