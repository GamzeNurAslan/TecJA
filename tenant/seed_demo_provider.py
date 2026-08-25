from backend.app.database import get_connection
from backend.app.tenancy import ensure_tenant_schema


PROVIDER_ID = "ISP002"
PROVIDER_NAME = "AnadoluNet Demo ISP"


DEMO_CUSTOMERS = [
    (
        "C90001",
        "Deniz",
        "Aksoy",
        "Türkiye",
        "İstanbul",
        "Individual",
        "Fiber 1000 Mbps",
        "899",
        "2025-01-12",
        "82",
        "Active",
        "4",
        "1",
        "3",
        "3",
        "1",
        "118.4",
        "1",
        "1",
        "0",
        "1",
        "18.5",
        "68",
        "High",
        PROVIDER_ID,
    ),
    (
        "C90002",
        "Ece",
        "Yalçın",
        "Türkiye",
        "Ankara",
        "Business",
        "Fiber 500 Mbps",
        "599",
        "2024-11-03",
        "61",
        "Active",
        "2",
        "0",
        "2",
        "2",
        "0",
        "74.2",
        "1",
        "0",
        "0",
        "1",
        "9.2",
        "42",
        "Medium",
        PROVIDER_ID,
    ),
    (
        "C90003",
        "Mert",
        "Kaya",
        "Türkiye",
        "İzmir",
        "Individual",
        "Basic",
        "299",
        "2025-05-21",
        "24",
        "Active",
        "1",
        "0",
        "1",
        "1",
        "0",
        "42.8",
        "0",
        "0",
        "0",
        "0",
        "0",
        "18",
        "Low",
        PROVIDER_ID,
    ),
    (
        "C90004",
        "Selin",
        "Demir",
        "Türkiye",
        "Bursa",
        "Individual",
        "Premium",
        "699",
        "2024-08-17",
        "75",
        "Churned",
        "3",
        "2",
        "1",
        "4",
        "2",
        "205.6",
        "2",
        "2",
        "1",
        "1",
        "44.0",
        "79",
        "High",
        PROVIDER_ID,
    ),
    (
        "C90005",
        "Baran",
        "Öztürk",
        "Türkiye",
        "Antalya",
        "Business",
        "Fiber 100 Mbps",
        "449",
        "2025-02-09",
        "38",
        "Active",
        "2",
        "1",
        "1",
        "2",
        "0",
        "91.3",
        "1",
        "0",
        "1",
        "0",
        "0",
        "39",
        "Medium",
        PROVIDER_ID,
    ),
]


CUSTOMER_COLUMNS = (
    "customer_id",
    "first_name",
    "last_name",
    "country",
    "city",
    "customer_type",
    "plan",
    "monthly_fee",
    "signup_date",
    "base_risk_score",
    "status",
    "total_orders",
    "failed_orders",
    "successful_orders",
    "network_events",
    "high_severity_network_events",
    "average_latency_ms",
    "total_tickets",
    "high_priority_tickets",
    "open_tickets",
    "resolved_tickets",
    "average_resolution_hours",
    "risk_score",
    "risk_level",
    "provider_id",
)


JOURNEY_EVENTS = [
    ("J900001", "C90001", "2026-08-01T09:00:00", "Order Created", "O90001", "Completed", "Low", "İstanbul", "Fiber subscription order created.", PROVIDER_ID),
    ("J900002", "C90001", "2026-08-01T09:10:00", "Provisioning Started", "O90001", "In Progress", "Low", "İstanbul", "Provisioning started for the new line.", PROVIDER_ID),
    ("J900003", "C90001", "2026-08-01T09:35:00", "Provisioning Failed", "O90001", "Failed", "High", "İstanbul", "Provisioning failed because no suitable port was available.", PROVIDER_ID),
    ("J900004", "C90001", "2026-08-01T10:00:00", "Ticket Created", "T90001", "Open", "High", "İstanbul", "Activation issue ticket created.", PROVIDER_ID),
    ("J900005", "C90001", "2026-08-01T12:00:00", "Activated", "O90001", "Completed", "Low", "İstanbul", "Service activated after a provisioning retry.", PROVIDER_ID),
    ("J900006", "C90002", "2026-08-03T09:00:00", "Order Created", "O90002", "Completed", "Low", "Ankara", "Business fiber order created.", PROVIDER_ID),
    ("J900007", "C90002", "2026-08-03T09:20:00", "Activated", "O90002", "Completed", "Low", "Ankara", "Business line activated successfully.", PROVIDER_ID),
    ("J900008", "C90002", "2026-08-04T14:30:00", "Network Degradation", "N90002", "Problem", "Medium", "Ankara", "Short periods of network degradation detected.", PROVIDER_ID),
    ("J900009", "C90002", "2026-08-04T15:00:00", "Ticket Created", "T90002", "Open", "Medium", "Ankara", "Network quality ticket created.", PROVIDER_ID),
    ("J900010", "C90003", "2026-08-05T09:00:00", "Order Created", "O90003", "Completed", "Low", "İzmir", "Basic plan order created.", PROVIDER_ID),
    ("J900011", "C90003", "2026-08-05T10:00:00", "Activated", "O90003", "Completed", "Low", "İzmir", "Basic plan activated successfully.", PROVIDER_ID),
    ("J900012", "C90004", "2026-08-06T09:00:00", "Order Created", "O90004", "Completed", "Low", "Bursa", "Premium subscription order created.", PROVIDER_ID),
    ("J900013", "C90004", "2026-08-06T09:30:00", "Provisioning Failed", "O90004", "Failed", "High", "Bursa", "Premium line provisioning failed.", PROVIDER_ID),
    ("J900014", "C90004", "2026-08-06T10:00:00", "Ticket Created", "T90004", "Open", "High", "Bursa", "Repeated provisioning failure ticket created.", PROVIDER_ID),
    ("J900015", "C90005", "2026-08-07T09:00:00", "Order Created", "O90005", "Completed", "Low", "Antalya", "Business internet order created.", PROVIDER_ID),
    ("J900016", "C90005", "2026-08-07T10:00:00", "Network Degradation", "N90005", "Problem", "Medium", "Antalya", "Network degradation detected in the service area.", PROVIDER_ID),
    ("J900017", "C90005", "2026-08-07T11:00:00", "Ticket Created", "T90005", "In Progress", "Medium", "Antalya", "Network degradation ticket is being handled.", PROVIDER_ID),
]


JOURNEY_EVENT_COLUMNS = (
    "journey_event_id",
    "customer_id",
    "event_time",
    "event_type",
    "source_id",
    "status",
    "severity",
    "city",
    "details",
    "provider_id",
)


TICKETS = [
    ("T90001", "C90001", "2026-08-01T10:00:00", "Türkiye", "İstanbul", "Activation Problem", "High", "İstanbul bölgesinde aktivasyon tamamlanamadı.", "Open", "0", "J900003", "2026-08-01T10:00:00", "demo_isp002", PROVIDER_ID),
    ("T90002", "C90002", "2026-08-04T15:00:00", "Türkiye", "Ankara", "Network Instability", "Medium", "Ankara bölgesinde bağlantı kalitesi dalgalanıyor.", "Resolved", "12", "J900008", "2026-08-04T15:00:00", "demo_isp002", PROVIDER_ID),
    ("T90003", "C90003", "2026-08-05T10:30:00", "Türkiye", "İzmir", "Slow Internet", "Low", "İzmir hattında kısa süreli hız düşüşü bildirildi.", "Resolved", "6", "J900011", "2026-08-05T10:30:00", "demo_isp002", PROVIDER_ID),
    ("T90004", "C90004", "2026-08-06T10:00:00", "Türkiye", "Bursa", "Activation Problem", "High", "Bursa premium hattında provisioning tekrar başarısız oldu.", "Open", "0", "J900013", "2026-08-06T10:00:00", "demo_isp002", PROVIDER_ID),
    ("T90005", "C90005", "2026-08-07T11:00:00", "Türkiye", "Antalya", "Network Instability", "Medium", "Antalya bölgesinde ağ kararsızlığı tespit edildi.", "In Progress", "0", "J900016", "2026-08-07T11:00:00", "demo_isp002", PROVIDER_ID),
]


TICKET_COLUMNS = (
    "ticket_id",
    "customer_id",
    "created_at",
    "country",
    "city",
    "category",
    "priority",
    "description",
    "status",
    "resolution_hours",
    "related_event_id",
    "_ingested_at",
    "_source_file",
    "provider_id",
)


TICKET_CATEGORIES = [
    ("T90001", "C90001", "İstanbul", "High", "Open", "Service Activation", "Activation Problem", "0.94", TICKETS[0][7], PROVIDER_ID),
    ("T90002", "C90002", "Ankara", "Medium", "Resolved", "Network Quality", "Network Instability", "0.89", TICKETS[1][7], PROVIDER_ID),
    ("T90003", "C90003", "İzmir", "Low", "Resolved", "Internet Speed", "Slow Internet", "0.86", TICKETS[2][7], PROVIDER_ID),
    ("T90004", "C90004", "Bursa", "High", "Open", "Service Activation", "Activation Problem", "0.96", TICKETS[3][7], PROVIDER_ID),
    ("T90005", "C90005", "Antalya", "Medium", "In Progress", "Network Quality", "Network Instability", "0.91", TICKETS[4][7], PROVIDER_ID),
]


TICKET_CATEGORY_COLUMNS = (
    "ticket_id",
    "customer_id",
    "city",
    "priority",
    "status",
    "original_category",
    "predicted_category",
    "confidence",
    "description",
    "provider_id",
)


JOURNEY_PATTERNS = [
    ("Order Created → Provisioning Failed → Ticket Created", "2", "2", "1", "73.5", PROVIDER_ID),
    ("Order Created → Activated → Network Degradation", "2", "0", "0", "30.5", PROVIDER_ID),
    ("Order Created → Activated", "1", "0", "0", "18.0", PROVIDER_ID),
]


JOURNEY_PATTERN_COLUMNS = (
    "journey_pattern",
    "customer_count",
    "high_risk_customers",
    "churned_customers",
    "average_risk_score",
    "provider_id",
)


RISK_SUMMARY = [
    ("High", "2", "1", "73.5", PROVIDER_ID),
    ("Medium", "2", "0", "40.5", PROVIDER_ID),
    ("Low", "1", "0", "18.0", PROVIDER_ID),
]


RISK_SUMMARY_COLUMNS = (
    "risk_level",
    "customer_count",
    "churned_customers",
    "average_risk_score",
    "provider_id",
)


def insert_if_empty(connection, table_name, columns, rows):
    existing_count = connection.execute(
        f"SELECT COUNT(*) AS count FROM {table_name} WHERE provider_id = ?",
        (PROVIDER_ID,),
    ).fetchone()["count"]

    if existing_count:
        return 0

    placeholders = ", ".join("?" for _ in columns)
    connection.executemany(
        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
        rows,
    )
    return len(rows)


def seed_demo_provider():
    with get_connection() as connection:
        ensure_tenant_schema(connection)

        connection.execute(
            """
            INSERT OR IGNORE INTO providers (
                provider_id,
                name,
                status
            )
            VALUES (?, ?, 'Active')
            """,
            (PROVIDER_ID, PROVIDER_NAME),
        )

        existing_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM customer_metrics
            WHERE provider_id = ?
            """,
            (PROVIDER_ID,),
        ).fetchone()["count"]

        if existing_count == 0:
            placeholders = ", ".join("?" for _ in CUSTOMER_COLUMNS)
            connection.executemany(
                f"""
                INSERT INTO customer_metrics ({', '.join(CUSTOMER_COLUMNS)})
                VALUES ({placeholders})
                """,
                DEMO_CUSTOMERS,
            )

        inserted_counts = {
            "journey_events": insert_if_empty(
                connection,
                "journey_events",
                JOURNEY_EVENT_COLUMNS,
                JOURNEY_EVENTS,
            ),
            "tickets": insert_if_empty(
                connection,
                "tickets",
                TICKET_COLUMNS,
                TICKETS,
            ),
            "ticket_categories": insert_if_empty(
                connection,
                "ticket_categories",
                TICKET_CATEGORY_COLUMNS,
                TICKET_CATEGORIES,
            ),
            "journey_patterns": insert_if_empty(
                connection,
                "journey_patterns",
                JOURNEY_PATTERN_COLUMNS,
                JOURNEY_PATTERNS,
            ),
            "risk_summary": insert_if_empty(
                connection,
                "risk_summary",
                RISK_SUMMARY_COLUMNS,
                RISK_SUMMARY,
            ),
        }

    print(
        f"{PROVIDER_ID} seeded: {len(DEMO_CUSTOMERS)} demo customers, "
        f"{inserted_counts['journey_events']} journey events, "
        f"{inserted_counts['tickets']} tickets, "
        f"{inserted_counts['journey_patterns']} journey patterns."
    )
    print(
        "Login: analyst2@tecja.com / analyst2123"
    )


if __name__ == "__main__":
    seed_demo_provider()
