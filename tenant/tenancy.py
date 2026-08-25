DEFAULT_PROVIDER_ID = "ISP001"
DEFAULT_PROVIDER_NAME = "TecJA Demo ISP"


TENANT_TABLES = (
    "customer_metrics",
    "journey_events",
    "tickets",
    "ticket_categories",
    "journey_patterns",
    "risk_summary",
    "customer_actions",
    "auth_sessions",
)


def _table_exists(connection, table_name):
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def _column_names(connection, table_name):
    rows = connection.execute(
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    return {row["name"] for row in rows}


def ensure_tenant_schema(connection):
    """Add the tenant columns without disturbing existing data."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS providers (
            provider_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO providers (
            provider_id,
            name,
            status
        )
        VALUES (?, ?, 'Active')
        """,
        (DEFAULT_PROVIDER_ID, DEFAULT_PROVIDER_NAME),
    )

    for table_name in TENANT_TABLES:
        if not _table_exists(connection, table_name):
            continue

        if "provider_id" not in _column_names(
            connection,
            table_name,
        ):
            connection.execute(
                f'ALTER TABLE "{table_name}" '
                "ADD COLUMN provider_id TEXT"
            )

        connection.execute(
            f'UPDATE "{table_name}" '
            "SET provider_id = ? "
            "WHERE provider_id IS NULL "
            "OR TRIM(provider_id) = ''",
            (DEFAULT_PROVIDER_ID,),
        )

        connection.execute(
            f"CREATE INDEX IF NOT EXISTS "
            f'"idx_{table_name}_provider_id" '
            f'ON "{table_name}"(provider_id)'
        )


def provider_id_for_user(user):
    if not user or user.get("role") == "admin":
        return None

    return user.get("provider_id") or DEFAULT_PROVIDER_ID


def add_provider_condition(
    conditions,
    parameters,
    user,
    column="provider_id",
):
    provider_id = provider_id_for_user(user)

    if provider_id:
        conditions.append(f"{column} = ?")
        parameters.append(provider_id)

    return provider_id
