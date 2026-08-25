import csv
import shutil

from backend.app.config import (
    DATABASE_PATH,
    GOLD_DIR,
    SILVER_DIR,
)

from backend.app.database import get_connection
from backend.app.tenancy import (
    DEFAULT_PROVIDER_ID,
    ensure_tenant_schema,
)


ANALYTICS_DIR = GOLD_DIR.parent / "analytics"


TABLE_SOURCES = {
    "customer_metrics": GOLD_DIR / "customer_metrics.csv",
    "journey_events": GOLD_DIR / "journey_events.csv",
    "tickets": SILVER_DIR / "tickets.csv",
    "ticket_categories": (
        ANALYTICS_DIR / "ticket_categories.csv"
    ),
    "journey_patterns": (
        ANALYTICS_DIR / "journey_patterns.csv"
    ),
    "risk_summary": (
        ANALYTICS_DIR / "risk_summary.csv"
    ),
}


TABLE_KEYS = {
    "customer_metrics": "customer_id",
    "journey_events": "journey_event_id",
    "tickets": "ticket_id",
    "ticket_categories": "ticket_id",
    "journey_patterns": "journey_pattern",
    "risk_summary": "risk_level",
}


PRESERVE_TABLES = {
    "journey_events",
    "tickets",
    "ticket_categories",
}


def quote_identifier(value):
    escaped_value = value.replace('"', '""')
    return f'"{escaped_value}"'


def table_exists(connection, table_name):
    result = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return result is not None


def read_csv_rows(csv_path):
    if not csv_path.exists():
        return [], []

    with csv_path.open(
        mode="r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    return fieldnames, rows


def create_table(
    connection,
    table_name,
    fieldnames,
):
    quoted_table = quote_identifier(table_name)

    quoted_columns = [
        quote_identifier(column)
        for column in fieldnames
    ]

    column_definitions = ", ".join(
        f"{column} TEXT"
        for column in quoted_columns
    )

    connection.execute(
        f"CREATE TABLE {quoted_table} "
        f"({column_definitions})"
    )


def insert_rows(
    connection,
    table_name,
    fieldnames,
    rows,
):
    if not rows:
        return

    quoted_table = quote_identifier(table_name)

    quoted_columns = [
        quote_identifier(column)
        for column in fieldnames
    ]

    placeholders = ", ".join(
        "?"
        for _ in fieldnames
    )

    insert_sql = (
        f"INSERT INTO {quoted_table} "
        f"({', '.join(quoted_columns)}) "
        f"VALUES ({placeholders})"
    )

    values = [
        tuple(
            row.get(column, "")
            for column in fieldnames
        )
        for row in rows
    ]

    connection.executemany(
        insert_sql,
        values,
    )


def read_existing_rows(
    connection,
    table_name,
):
    if not table_exists(connection, table_name):
        return []

    rows = connection.execute(
        f"SELECT * FROM "
        f"{quote_identifier(table_name)}"
    ).fetchall()

    return [dict(row) for row in rows]


def as_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def is_simulation_override(
    existing_row,
    incoming_row,
):
    counter_fields = [
        "network_events",
        "high_severity_network_events",
        "total_tickets",
        "open_tickets",
        "high_priority_tickets",
    ]

    for field in counter_fields:
        existing_value = as_number(
            existing_row.get(field)
        )

        incoming_value = as_number(
            incoming_row.get(field)
        )

        if existing_value > incoming_value:
            return True

    return False


def rows_to_preserve(
    table_name,
    existing_rows,
    incoming_rows,
):
    if not existing_rows:
        return []

    key = TABLE_KEYS[table_name]

    incoming_keys = {
        row.get(key)
        for row in incoming_rows
    }

    if table_name in PRESERVE_TABLES:
        return [
            row
            for row in existing_rows
            if (
                row.get("provider_id")
                and row.get("provider_id") != DEFAULT_PROVIDER_ID
            )
            or row.get(key) not in incoming_keys
        ]

    if table_name == "customer_metrics":
        incoming_by_key = {
            row.get(key): row
            for row in incoming_rows
        }

        overrides = []

        for existing_row in existing_rows:
            row_key = existing_row.get(key)
            incoming_row = incoming_by_key.get(row_key)

            if incoming_row is None:
                continue

            if is_simulation_override(
                existing_row,
                incoming_row,
            ):
                overrides.append(existing_row)

        incoming_keys = {
            row.get(key)
            for row in incoming_rows
        }

        # Keep records belonging to a non-default provider. These are
        # intentionally not part of the generated CSV pipeline and must
        # survive a later migration.
        provider_rows = [
            row
            for row in existing_rows
            if (
                row.get("provider_id")
                and row.get("provider_id")
                != DEFAULT_PROVIDER_ID
                and row.get(key) not in incoming_keys
            )
        ]

        return [*overrides, *provider_rows]

    return [
        row
        for row in existing_rows
        if (
            row.get("provider_id")
            and row.get("provider_id") != DEFAULT_PROVIDER_ID
        )
    ]


def merge_rows(
    table_name,
    incoming_rows,
    preserved_rows,
):
    key = TABLE_KEYS[table_name]

    if table_name == "customer_metrics":
        preserved_by_key = {
            row.get(key): row
            for row in preserved_rows
        }

        merged_rows = []

        for incoming_row in incoming_rows:
            row_key = incoming_row.get(key)

            if row_key in preserved_by_key:
                merged_rows.append(
                    preserved_by_key[row_key]
                )
            else:
                merged_rows.append(incoming_row)

        incoming_keys = {
            row.get(key)
            for row in incoming_rows
        }

        preserved_only_rows = [
            row
            for row in preserved_rows
            if row.get(key) not in incoming_keys
        ]

        return [
            *merged_rows,
            *preserved_only_rows,
        ]

    return [
        *incoming_rows,
        *preserved_rows,
    ]


def migrate_table(
    connection,
    table_name,
    csv_path,
):
    fieldnames, incoming_rows = read_csv_rows(csv_path)

    if not fieldnames:
        print(
            f"Skipped {table_name}: "
            "file not found or empty."
        )
        return 0

    existing_rows = read_existing_rows(
        connection,
        table_name,
    )

    if "provider_id" not in fieldnames:
        fieldnames = [*fieldnames, "provider_id"]

    existing_provider_by_key = {
        row.get(TABLE_KEYS[table_name]): (
            row.get("provider_id")
            or DEFAULT_PROVIDER_ID
        )
        for row in existing_rows
    }

    for row in incoming_rows:
        row["provider_id"] = (
            existing_provider_by_key.get(
                row.get(TABLE_KEYS[table_name])
            )
            or DEFAULT_PROVIDER_ID
        )

    preserved_rows = rows_to_preserve(
        table_name,
        existing_rows,
        incoming_rows,
    )

    final_rows = merge_rows(
        table_name,
        incoming_rows,
        preserved_rows,
    )

    quoted_table = quote_identifier(table_name)

    connection.execute(
        f"DROP TABLE IF EXISTS {quoted_table}"
    )

    create_table(
        connection,
        table_name,
        fieldnames,
    )

    insert_rows(
        connection,
        table_name,
        fieldnames,
        final_rows,
    )

    print(
        f"{table_name}: "
        f"{len(final_rows)} records migrated "
        f"({len(preserved_rows)} live records preserved)."
    )

    return len(final_rows)


def create_indexes(connection):
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_customer_metrics_customer_id
        ON customer_metrics(customer_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_customer_metrics_risk_level
        ON customer_metrics(risk_level)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_journey_events_customer_id
        ON journey_events(customer_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_ticket_categories_customer_id
        ON ticket_categories(customer_id)
        """
    )


def migrate_database():
    if DATABASE_PATH.exists():
        backup_path = DATABASE_PATH.with_suffix(
            ".db.backup"
        )

        shutil.copy2(
            DATABASE_PATH,
            backup_path,
        )

        print(
            f"Database backup created: "
            f"{backup_path}"
        )

    total_records = 0

    with get_connection() as connection:
        for table_name, csv_path in (
            TABLE_SOURCES.items()
        ):
            total_records += migrate_table(
                connection,
                table_name,
                csv_path,
            )

        ensure_tenant_schema(connection)
        create_indexes(connection)

    print()
    print(
        f"SQLite database updated: "
        f"{DATABASE_PATH}"
    )

    print(
        f"Total migrated records: "
        f"{total_records}"
    )


if __name__ == "__main__":
    migrate_database()
