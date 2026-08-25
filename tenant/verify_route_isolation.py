import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path


PROJECT_PATH = Path(r"C:\Users\Lenovo\PycharmProjects\TecJA")
DATABASE_PATH = Path(__file__).with_name("test-isolation.db")
sys.path.insert(0, str(PROJECT_PATH))

from backend.app.api import routes  # noqa: E402
from backend.app.tenancy import ensure_tenant_schema  # noqa: E402


connection = sqlite3.connect(DATABASE_PATH)
connection.row_factory = sqlite3.Row
ensure_tenant_schema(connection)
connection.execute(
    """
    INSERT OR REPLACE INTO providers (provider_id, name, status)
    VALUES ('ISP002', 'Second Test ISP', 'active')
    """
)

source = connection.execute(
    "SELECT * FROM customer_metrics LIMIT 1"
).fetchone()
row = dict(source)
row["customer_id"] = "TENANT_TEST_CUSTOMER"
row["first_name"] = "Tenant"
row["last_name"] = "Test"
row["provider_id"] = "ISP002"

columns = list(row)
quoted_columns = ", ".join(f'"{column}"' for column in columns)
placeholders = ", ".join("?" for _ in columns)
connection.execute(
    f"INSERT OR REPLACE INTO customer_metrics ({quoted_columns}) "
    f"VALUES ({placeholders})",
    [row[column] for column in columns],
)
connection.commit()
connection.close()


@contextmanager
def temporary_connection():
    current = sqlite3.connect(DATABASE_PATH)
    current.row_factory = sqlite3.Row
    try:
        yield current
        current.commit()
    finally:
        current.close()


routes.get_connection = temporary_connection

admin = routes.get_summary(
    {"role": "admin", "provider_id": None}
)
first_provider = routes.get_summary(
    {"role": "analyst", "provider_id": "ISP001"}
)
second_provider = routes.get_summary(
    {"role": "analyst", "provider_id": "ISP002"}
)

print("admin_customers", admin["total_customers"])
print("isp001_customers", first_provider["total_customers"])
print("isp002_customers", second_provider["total_customers"])

assert admin["total_customers"] == 5001
assert first_provider["total_customers"] == 5000
assert second_provider["total_customers"] == 1
print("ROUTE_ISOLATION_OK")
