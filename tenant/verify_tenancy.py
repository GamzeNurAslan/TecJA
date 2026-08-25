import sqlite3

from tenancy import (
    DEFAULT_PROVIDER_ID,
    ensure_tenant_schema,
    provider_id_for_user,
)


DATABASE_PATH = "test-tecja.db"
TABLES = (
    "customer_metrics",
    "journey_events",
    "tickets",
    "ticket_categories",
    "journey_patterns",
    "risk_summary",
    "customer_actions",
    "auth_sessions",
)


connection = sqlite3.connect(DATABASE_PATH)
connection.row_factory = sqlite3.Row
ensure_tenant_schema(connection)

print("providers", connection.execute("SELECT COUNT(*) FROM providers").fetchone()[0])

for table in TABLES:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    if not exists:
        continue

    total = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    assigned = connection.execute(
        f"SELECT COUNT(*) FROM {table} WHERE provider_id = ?",
        (DEFAULT_PROVIDER_ID,),
    ).fetchone()[0]
    print(table, total, assigned)

print("admin_scope", provider_id_for_user({"role": "admin", "provider_id": None}))
print(
    "analyst_scope",
    provider_id_for_user({"role": "analyst", "provider_id": DEFAULT_PROVIDER_ID}),
)

connection.close()
