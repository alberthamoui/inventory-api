from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine, Connection

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= DATABASE =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
DATABASE_URL = "sqlite+pysqlite:///inventory.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.close()

def createTables(conn: Connection):
    ean13Glob = "[0-9]" * 13

    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS Product (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            ean13           TEXT NOT NULL UNIQUE,
            quantity        INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
            alert_threshold INTEGER NOT NULL DEFAULT 0 CHECK (alert_threshold >= 0),

            CHECK (length(ean13) = 13 AND ean13 GLOB '{ean13Glob}')
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Movement (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type       TEXT NOT NULL CHECK (type IN ('in', 'out')),
            quantity   INTEGER NOT NULL CHECK (quantity > 0),
            date       TEXT NOT NULL DEFAULT (CURRENT_DATE),
            reason     TEXT,

            FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE RESTRICT
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS DeletedProduct (
            product_id INTEGER PRIMARY KEY,
            deleted_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),

            FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
        );
    """))

def init_db():
    # engine.begin() abre transação e dá commit automaticamente
    with engine.begin() as conn:
        createTables(conn)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= FAST API =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def getDb():
    # Uma transação por request (commit no sucesso, rollback no erro)
    with engine.begin() as conn:
        yield conn

def main():
    init_db()
    print("inventory.db initialized.")

if __name__ == "__main__":
    main()
