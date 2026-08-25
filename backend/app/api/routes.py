from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from pydantic import BaseModel

from backend.app.auth import (
    authenticate_user,
    create_session,
    get_current_user,
    require_admin,
    remove_session,
    bearer_scheme,
)
from backend.app.database import get_connection
from backend.app.report_email import (
    ReportEmailConfigurationError,
    ReportEmailDeliveryError,
    build_report_pdf,
    normalize_email_address,
    send_report_email,
)
from backend.app.tenancy import (
    DEFAULT_PROVIDER_ID,
    add_provider_condition,
    ensure_tenant_schema,
    provider_id_for_user,
)


router = APIRouter()


def analytics_provider_id_for_user(current_user):
    """Keep dashboard/report analytics on the primary TecJA dataset.

    Admin users can see the cross-provider overview through the dedicated
    provider endpoint, while dashboard and report numbers stay comparable
    with the original 5,000-customer dataset.
    """
    return provider_id_for_user(current_user) or DEFAULT_PROVIDER_ID


def normalized_provider_sql(column="provider_id"):
    """Treat blank provider IDs as the default TecJA provider."""
    escaped_default = DEFAULT_PROVIDER_ID.replace("'", "''")
    return (
        f"COALESCE(NULLIF(TRIM({column}), ''), "
        f"'{escaped_default}')"
    )


def latest_customer_metrics_cte():
    """Return one latest snapshot per normalized provider/customer pair."""
    latest_provider_expression = normalized_provider_sql("provider_id")
    customer_provider_expression = normalized_provider_sql(
        "customer_metrics.provider_id"
    )
    return f"""
    WITH latest_customer_metrics AS (
        SELECT customer_metrics.*
        FROM customer_metrics
        INNER JOIN (
            SELECT
                {latest_provider_expression} AS provider_scope_id,
                customer_id,
                MAX(rowid) AS latest_rowid
            FROM customer_metrics
            GROUP BY
                {latest_provider_expression},
                customer_id
        ) AS latest
            ON latest.provider_scope_id =
                {customer_provider_expression}
            AND latest.customer_id = customer_metrics.customer_id
            AND latest.latest_rowid = customer_metrics.rowid
    )
    """


class LoginRequest(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str


class ActionCreateRequest(BaseModel):
    customer_id: str
    action_type: str
    assigned_to: str = "Operations"
    note: str = ""


class ActionStatusRequest(BaseModel):
    status: str


class ReportEmailRequest(BaseModel):
    recipient: str


@router.post("/auth/login")
def login(payload: LoginRequest):
    identifier = payload.email or payload.username or ""

    user = authenticate_user(
        identifier,
        payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Email or password is incorrect.",
        )

    token = create_session(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/auth/me")
def get_logged_in_user(
    current_user=Depends(get_current_user),
):
    return current_user


@router.post("/auth/logout")
def logout(
    credentials=Depends(bearer_scheme),
):
    if credentials is not None:
        remove_session(
            credentials.credentials
        )

    return {
        "message": "Logged out successfully."
    }


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "TecJA API",
    }


@router.get("/providers")
def get_providers(
    current_user=Depends(get_current_user),
):
    provider_id = provider_id_for_user(current_user)

    query = """
        SELECT
            providers.provider_id,
            providers.name AS provider_name,
            providers.status,
            COUNT(DISTINCT customer_metrics.customer_id)
                AS customer_count,
            SUM(
                CASE
                    WHEN customer_metrics.risk_level = 'High'
                    THEN 1
                    ELSE 0
                END
            ) AS high_risk_customers,
            ROUND(
                AVG(
                    CAST(
                        customer_metrics.risk_score
                        AS REAL
                    )
                ),
                1
            ) AS average_risk_score,
            (
                SELECT COUNT(*)
                FROM journey_events
                WHERE journey_events.provider_id =
                    providers.provider_id
            ) AS journey_event_count,
            (
                SELECT COUNT(*)
                FROM tickets
                WHERE tickets.provider_id =
                    providers.provider_id
            ) AS ticket_count
        FROM providers
        LEFT JOIN customer_metrics
            ON customer_metrics.provider_id =
                providers.provider_id
    """
    parameters = []

    if provider_id:
        query += " WHERE providers.provider_id = ?"
        parameters.append(provider_id)

    query += """
        GROUP BY
            providers.provider_id,
            providers.name,
            providers.status
        ORDER BY provider_name
    """

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["customer_count"] = int(
            item["customer_count"] or 0
        )
        item["high_risk_customers"] = int(
            item["high_risk_customers"] or 0
        )
        item["average_risk_score"] = float(
            item["average_risk_score"] or 0
        )
        item["journey_event_count"] = int(
            item["journey_event_count"] or 0
        )
        item["ticket_count"] = int(
            item["ticket_count"] or 0
        )
        items.append(item)

    return {
        "count": len(items),
        "items": items,
    }


@router.get("/summary")
def get_summary(
    current_user=Depends(get_current_user),
):
    provider_id = analytics_provider_id_for_user(current_user)
    provider_scope = normalized_provider_sql()
    where_clause = f"WHERE {provider_scope} = ?"
    parameters = [provider_id]

    with get_connection() as connection:
        customer_summary = connection.execute(
            f"""
            {latest_customer_metrics_cte()}
            SELECT
                COUNT(*) AS total_customers,

                SUM(
                    CASE
                        WHEN status = 'Active'
                        THEN 1
                        ELSE 0
                    END
                ) AS active_customers,

                SUM(
                    CASE
                        WHEN status = 'Churned'
                        THEN 1
                        ELSE 0
                    END
                ) AS churned_customers,

                SUM(
                    CASE
                        WHEN risk_level = 'High'
                        THEN 1
                        ELSE 0
                    END
                ) AS high_risk_customers,

                SUM(
                    CASE
                        WHEN
                            CAST(failed_orders AS INTEGER) > 0
                            OR CAST(open_tickets AS INTEGER) > 0
                            OR CAST(
                                high_severity_network_events
                                AS INTEGER
                            ) > 0
                        THEN 1
                        ELSE 0
                    END
                ) AS problematic_customers,

                AVG(
                    CASE
                        WHEN CAST(
                            average_resolution_hours
                            AS REAL
                        ) > 0
                        THEN CAST(
                            average_resolution_hours
                            AS REAL
                        )
                    END
                ) AS average_resolution_hours

            FROM latest_customer_metrics
            {where_clause}
            """,
            parameters,
        ).fetchone()

        journey_count = connection.execute(
            f"""
            SELECT COUNT(*) AS total_journey_events
            FROM journey_events
            {where_clause}
            """,
            parameters,
        ).fetchone()

        ticket_count = connection.execute(
            f"""
            SELECT COUNT(*) AS total_tickets
            FROM tickets
            {where_clause}
            """,
            parameters,
        ).fetchone()

    return {
        "total_customers": int(
            customer_summary["total_customers"] or 0
        ),
        "active_customers": int(
            customer_summary["active_customers"] or 0
        ),
        "churned_customers": int(
            customer_summary["churned_customers"] or 0
        ),
        "high_risk_customers": int(
            customer_summary["high_risk_customers"] or 0
        ),
        "problematic_customers": int(
            customer_summary["problematic_customers"] or 0
        ),
        "total_journey_events": int(
            journey_count["total_journey_events"] or 0
        ),
        "total_tickets": int(
            ticket_count["total_tickets"] or 0
        ),
        "average_resolution_hours": round(
            float(
                customer_summary[
                    "average_resolution_hours"
                ]
                or 0
            ),
            1,
        ),
    }


@router.get("/customer-metrics")
def get_customer_metrics(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    risk_level: str | None = Query(
        default=None,
        max_length=20,
    ),
    current_user=Depends(get_current_user),
):
    conditions = []
    parameters = []

    if search and search.strip():
        search_value = (
            f"%{search.strip().lower()}%"
        )

        conditions.append(
            """
            LOWER(
                COALESCE(customer_id, '') || ' ' ||
                COALESCE(first_name, '') || ' ' ||
                COALESCE(last_name, '') || ' ' ||
                COALESCE(city, '') || ' ' ||
                COALESCE(country, '')
            ) LIKE ?
            """
        )

        parameters.append(search_value)

    if risk_level and risk_level.strip():
        conditions.append(
            "LOWER(risk_level) = ?"
        )

        parameters.append(
            risk_level.strip().lower()
        )

    conditions.append(f"{normalized_provider_sql()} = ?")
    parameters.append(
        analytics_provider_id_for_user(current_user)
    )

    where_clause = ""

    if conditions:
        where_clause = (
            " WHERE " + " AND ".join(conditions)
        )

    count_query = f"""
        {latest_customer_metrics_cte()}
        SELECT COUNT(*) AS total_count
        FROM latest_customer_metrics
        {where_clause}
    """

    data_query = f"""
        {latest_customer_metrics_cte()}
        SELECT *
        FROM latest_customer_metrics
        {where_clause}
        ORDER BY CAST(risk_score AS INTEGER) DESC
        LIMIT ? OFFSET ?
    """

    with get_connection() as connection:
        total_result = connection.execute(
            count_query,
            parameters,
        ).fetchone()

        rows = connection.execute(
            data_query,
            parameters + [limit, offset],
        ).fetchall()

    total_count = int(
        total_result["total_count"] or 0
    )

    items = [
        dict(row)
        for row in rows
    ]

    total_pages = max(
        1,
        (total_count + limit - 1) // limit,
    )

    return {
        "count": len(items),
        "total_count": total_count,
        "page": (offset // limit) + 1,
        "page_size": limit,
        "total_pages": total_pages,
        "items": items,
    }


@router.get("/journey-patterns")
def get_journey_patterns(
    limit: int = Query(
        default=10,
        ge=1,
        le=1000,
    ),
    current_user=Depends(get_current_user),
):
    provider_id = analytics_provider_id_for_user(current_user)
    where_clause = ""
    parameters = []

    if provider_id:
        where_clause = "WHERE provider_id = ?"
        parameters.append(provider_id)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM journey_patterns
            {where_clause}
            ORDER BY CAST(customer_count AS INTEGER)
            DESC
            LIMIT ?
            """,
            parameters + [limit],
        ).fetchall()

    items = [
        dict(row)
        for row in rows
    ]

    return {
        "count": len(items),
        "items": items,
    }


@router.get("/risk-summary")
def get_risk_summary(
    current_user=Depends(get_current_user),
):
    provider_id = analytics_provider_id_for_user(current_user)
    conditions = [
        "risk_level IN ('High', 'Medium', 'Low')",
        f"{normalized_provider_sql()} = ?",
    ]
    parameters = [provider_id]

    where_clause = "WHERE " + " AND ".join(conditions)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            {latest_customer_metrics_cte()}
            SELECT
                risk_level,
                COUNT(*) AS customer_count,
                SUM(
                    CASE
                        WHEN LOWER(TRIM(COALESCE(status, ''))) = 'churned'
                        THEN 1
                        ELSE 0
                    END
                ) AS churned_customers,
                ROUND(
                    AVG(CAST(NULLIF(risk_score, '') AS REAL)),
                    1
                ) AS average_risk_score
            FROM latest_customer_metrics
            {where_clause}
            GROUP BY risk_level
            ORDER BY CASE risk_level
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END
            """,
            parameters,
        ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["customer_count"] = int(
            item["customer_count"] or 0
        )
        item["churned_customers"] = int(
            item["churned_customers"] or 0
        )
        item["average_risk_score"] = round(
            float(item["average_risk_score"] or 0),
            1,
        )
        items.append(item)

    return {
        "items": items,
    }


@router.get("/ticket-categories")
def get_ticket_categories(
    current_user=Depends(get_current_user),
):
    provider_id = analytics_provider_id_for_user(current_user)
    where_clause = ""
    parameters = []

    if provider_id:
        where_clause = "WHERE provider_id = ?"
        parameters.append(provider_id)

    with get_connection() as connection:
        total_result = connection.execute(
            f"""
            SELECT COUNT(*) AS total_tickets
            FROM ticket_categories
            {where_clause}
            """,
            parameters,
        ).fetchone()

        rows = connection.execute(
            f"""
            SELECT
                COALESCE(
                    predicted_category,
                    'Other'
                ) AS category,
                COUNT(*) AS ticket_count,
                AVG(
                    CAST(confidence AS REAL)
                ) AS average_confidence
            FROM ticket_categories
            {where_clause}
            GROUP BY predicted_category
            ORDER BY ticket_count DESC
            """,
            parameters,
        ).fetchall()

    items = []

    for row in rows:
        items.append(
            {
                "category": row["category"],
                "ticket_count": int(
                    row["ticket_count"] or 0
                ),
                "average_confidence": round(
                    float(
                        row["average_confidence"]
                        or 0
                    ),
                    3,
                ),
            }
        )

    return {
        "total_tickets": int(
            total_result["total_tickets"] or 0
        ),
        "items": items,
    }


@router.get("/customers/{customer_id}/journey")
def get_customer_journey(
    customer_id: str,
    current_user=Depends(get_current_user),
):
    provider_id = provider_id_for_user(current_user)
    provider_clause = ""
    parameters = [customer_id]

    if provider_id:
        provider_clause = "AND provider_id = ?"
        parameters.append(provider_id)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM journey_events
            WHERE customer_id = ?
            {provider_clause}
            ORDER BY event_time
            """,
            parameters,
        ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Customer journey not found.",
        )

    events = [
        dict(row)
        for row in rows
    ]

    return {
        "customer_id": customer_id,
        "event_count": len(events),
        "events": events,
    }


@router.get("/notifications")
def get_notifications(
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    current_user=Depends(get_current_user),
):
    provider_id = provider_id_for_user(current_user)
    provider_clause = ""
    provider_parameters = []

    if provider_id:
        provider_clause = "AND provider_id = ?"
        provider_parameters.append(provider_id)

    with get_connection() as connection:
        high_risk_customers = connection.execute(
            f"""
            SELECT *
            FROM customer_metrics
            WHERE LOWER(risk_level) = 'high'
            {provider_clause}
            ORDER BY CAST(risk_score AS INTEGER)
            DESC
            LIMIT ?
            """,
            provider_parameters + [limit],
        ).fetchall()

        notifications = []

        for customer in high_risk_customers:
            notifications.append(
                {
                    "id": (
                        f"risk-"
                        f"{customer['customer_id']}"
                    ),
                    "type": "risk",
                    "title": (
                        "High-risk customer "
                        "detected"
                    ),
                    "message": (
                        f"{customer['customer_id']} - "
                        f"{customer['first_name']} "
                        f"{customer['last_name']} "
                        f"has a risk score of "
                        f"{customer['risk_score']}."
                    ),
                    "time": "Risk analysis",
                    "customer_id": customer[
                        "customer_id"
                    ],
                    "read": False,
                }
            )

        remaining_limit = max(
            limit - len(notifications),
            0,
        )

        if remaining_limit > 0:
            open_tickets = connection.execute(
                f"""
                SELECT *
                FROM tickets
                WHERE LOWER(status)
                    IN ('open', 'in progress')
                {provider_clause}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                provider_parameters + [remaining_limit],
            ).fetchall()

            for ticket in open_tickets:
                created_at = ticket["created_at"] or ""

                notifications.append(
                    {
                        "id": (
                            f"ticket-"
                            f"{ticket['ticket_id']}"
                        ),
                        "type": "ticket",
                        "title": (
                            "Open support ticket"
                        ),
                        "message": (
                            f"Ticket "
                            f"{ticket['ticket_id']} "
                            f"requires attention. "
                            f"Category: "
                            f"{ticket['category']}."
                        ),
                        "time": created_at.replace(
                            "T",
                            " ",
                        )[:16],
                        "ticket_id": ticket[
                            "ticket_id"
                        ],
                        "customer_id": ticket[
                            "customer_id"
                        ],
                        "read": False,
                    }
                )

    return {
        "count": len(notifications),
        "unread_count": len(notifications),
        "items": notifications,
    }


@router.get("/ai-insights")
def get_ai_insights(
    current_user=Depends(get_current_user),
):
    provider_id = analytics_provider_id_for_user(current_user)
    where_clause = ""
    parameters = []

    if provider_id:
        where_clause = "WHERE provider_id = ?"
        parameters.append(provider_id)

    with get_connection() as connection:
        total_result = connection.execute(
            f"""
            SELECT COUNT(*) AS total_tickets
            FROM ticket_categories
            {where_clause}
            """,
            parameters,
        ).fetchone()

        category_rows = connection.execute(
            f"""
            SELECT
                COALESCE(
                    predicted_category,
                    'Other'
                ) AS category,
                COUNT(*) AS ticket_count,
                AVG(
                    CAST(confidence AS REAL)
                ) AS average_confidence,
                COUNT(
                    DISTINCT customer_id
                ) AS affected_customers
            FROM ticket_categories
            {where_clause}
            GROUP BY predicted_category
            ORDER BY ticket_count DESC
            """,
            parameters,
        ).fetchall()

    total_tickets = int(
        total_result["total_tickets"] or 0
    )

    if not category_rows or total_tickets == 0:
        return {
            "detected_issue": "No Data",
            "ticket_count": 0,
            "affected_customers": 0,
            "confidence_percent": 0,
            "impact": "Low",
            "ticket_share_percent": 0,
            "recommended_action": (
                "No ticket data available."
            ),
            "total_tickets": 0,
        }

    top_category = category_rows[0]

    ticket_count = int(
        top_category["ticket_count"] or 0
    )

    affected_customers = int(
        top_category["affected_customers"] or 0
    )

    average_confidence = float(
        top_category["average_confidence"] or 0
    )

    ticket_share_percent = round(
        ticket_count
        / total_tickets
        * 100
    )

    confidence_percent = round(
        average_confidence * 100
    )

    if ticket_share_percent >= 30:
        impact = "High"
    elif ticket_share_percent >= 15:
        impact = "Medium"
    else:
        impact = "Low"

    category = top_category["category"]

    recommendations = {
        "Network Instability": (
            "Network bölgesindeki arıza ve "
            "latency kayıtları incelenmeli."
        ),
        "Activation Problem": (
            "Provisioning ve aktivasyon "
            "süreçleri kontrol edilmeli."
        ),
        "Slow Internet": (
            "Bölgesel internet hızı ve ağ "
            "kapasitesi analiz edilmeli."
        ),
        "Modem Problem": (
            "Modem restart ve cihaz arıza "
            "kayıtları incelenmeli."
        ),
        "Billing Problem": (
            "Faturalandırma ve ödeme süreçleri "
            "kontrol edilmeli."
        ),
    }

    recommended_action = recommendations.get(
        category,
        (
            "Ticket açıklamaları ve müşteri "
            "journey kayıtları incelenmeli."
        ),
    )

    return {
        "detected_issue": category,
        "ticket_count": ticket_count,
        "affected_customers": (
            affected_customers
        ),
        "confidence_percent": (
            confidence_percent
        ),
        "impact": impact,
        "ticket_share_percent": (
            ticket_share_percent
        ),
        "recommended_action": (
            recommended_action
        ),
        "total_tickets": total_tickets,
    }


@router.post("/simulation/tick")
def simulation_tick(
    current_user=Depends(require_admin),
):
    import random
    from datetime import datetime, timezone

    scenarios = [
        {
            "event_type": "Network Degradation",
            "category": "Network Instability",
            "priority": "High",
            "severity": "High",
            "details": (
                "Live simulation network degradation "
                "detected."
            ),
        },
        {
            "event_type": "High Latency",
            "category": "Slow Internet",
            "priority": "Medium",
            "severity": "Medium",
            "details": (
                "Live simulation high latency "
                "detected."
            ),
        },
        {
            "event_type": "Provisioning Failed",
            "category": "Activation Problem",
            "priority": "High",
            "severity": "High",
            "details": (
                "Live simulation provisioning "
                "failure detected."
            ),
        },
        {
            "event_type": "Connection Drop",
            "category": "Network Instability",
            "priority": "High",
            "severity": "High",
            "details": (
                "Live simulation connection drop "
                "detected."
            ),
        },
    ]

    scenario = random.choice(scenarios)

    now = datetime.now(
        timezone.utc
    ).replace(microsecond=0)

    created_at = now.isoformat()

    provider_id = provider_id_for_user(current_user)
    customer_where_clause = ""
    customer_parameters = []

    if provider_id:
        customer_where_clause = "WHERE provider_id = ?"
        customer_parameters.append(provider_id)

    with get_connection() as connection:
        customer = connection.execute(
            f"""
            SELECT *
            FROM customer_metrics
            {customer_where_clause}
            ORDER BY RANDOM()
            LIMIT 1
            """,
            customer_parameters,
        ).fetchone()

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="No customers found.",
            )

        next_event_number = connection.execute(
            """
            SELECT COALESCE(
                MAX(
                    CAST(
                        SUBSTR(
                            journey_event_id,
                            2
                        ) AS INTEGER
                    )
                ),
                0
            ) + 1 AS next_number
            FROM journey_events
            """
        ).fetchone()["next_number"]

        journey_event_id = (
            f"J{int(next_event_number):07d}"
        )

        next_ticket_number = connection.execute(
            """
            SELECT COALESCE(
                MAX(
                    CAST(
                        SUBSTR(
                            ticket_id,
                            2
                        ) AS INTEGER
                    )
                ),
                0
            ) + 1 AS next_number
            FROM tickets
            """
        ).fetchone()["next_number"]

        ticket_id = (
            f"T{int(next_ticket_number):06d}"
        )

        customer_id = customer["customer_id"]
        provider_id = (
            customer["provider_id"]
            or DEFAULT_PROVIDER_ID
        )
        city = customer["city"]
        country = customer["country"]

        event_latency = random.randint(
            120,
            480,
        )

        event_details = (
            f"{scenario['details']} "
            f"Latency: {event_latency} ms."
        )

        connection.execute(
            """
            INSERT INTO journey_events (
                journey_event_id,
                customer_id,
                event_time,
                event_type,
                source_id,
                status,
                severity,
                city,
                details,
                provider_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                journey_event_id,
                customer_id,
                created_at,
                scenario["event_type"],
                ticket_id,
                "Open",
                scenario["severity"],
                city,
                event_details,
                provider_id,
            ),
        )

        confidence = round(
            random.uniform(
                0.72,
                0.94,
            ),
            4,
        )

        description = (
            f"{city} bölgesinde canlı simülasyon "
            f"sonucu {scenario['category']} "
            f"olayı tespit edildi. "
            f"Gecikme {event_latency} ms."
        )

        connection.execute(
            """
            INSERT INTO tickets (
                ticket_id,
                customer_id,
                created_at,
                country,
                city,
                category,
                priority,
                description,
                status,
                resolution_hours,
                related_event_id,
                _ingested_at,
                _source_file,
                _cleaned_at,
                provider_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                customer_id,
                created_at,
                country,
                city,
                scenario["category"],
                scenario["priority"],
                description,
                "Open",
                "",
                journey_event_id,
                created_at,
                "live_simulation",
                created_at,
                provider_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO ticket_categories (
                ticket_id,
                customer_id,
                city,
                priority,
                status,
                original_category,
                predicted_category,
                confidence,
                description,
                provider_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                customer_id,
                city,
                scenario["priority"],
                "Open",
                scenario["category"],
                scenario["category"],
                confidence,
                description,
                provider_id,
            ),
        )

        old_risk_score = int(
            customer["risk_score"] or 0
        )

        risk_increase = (
            7
            if scenario["severity"] == "High"
            else 4
        )

        new_risk_score = min(
            100,
            old_risk_score + risk_increase,
        )

        if new_risk_score >= 70:
            new_risk_level = "High"
        elif new_risk_score >= 40:
            new_risk_level = "Medium"
        else:
            new_risk_level = "Low"

        new_network_events = (
            int(customer["network_events"] or 0)
            + 1
        )

        new_high_severity_events = (
            int(
                customer[
                    "high_severity_network_events"
                ]
                or 0
            )
            + (
                1
                if scenario["severity"] == "High"
                else 0
            )
        )

        new_total_tickets = (
            int(customer["total_tickets"] or 0)
            + 1
        )

        new_open_tickets = (
            int(customer["open_tickets"] or 0)
            + 1
        )

        new_high_priority_tickets = (
            int(
                customer[
                    "high_priority_tickets"
                ]
                or 0
            )
            + (
                1
                if scenario["priority"] == "High"
                else 0
            )
        )

        connection.execute(
            """
            UPDATE customer_metrics
            SET
                network_events = ?,
                high_severity_network_events = ?,
                total_tickets = ?,
                open_tickets = ?,
                high_priority_tickets = ?,
                risk_score = ?,
                risk_level = ?
            WHERE customer_id = ?
              AND provider_id = ?
            """,
            (
                new_network_events,
                new_high_severity_events,
                new_total_tickets,
                new_open_tickets,
                new_high_priority_tickets,
                new_risk_score,
                new_risk_level,
                customer_id,
                provider_id,
            ),
        )

    return {
        "simulation": "tick",
        "event": {
            "journey_event_id": journey_event_id,
            "event_type": scenario[
                "event_type"
            ],
            "severity": scenario[
                "severity"
            ],
            "city": city,
            "created_at": created_at,
        },
        "ticket": {
            "ticket_id": ticket_id,
            "category": scenario[
                "category"
            ],
            "priority": scenario[
                "priority"
            ],
        },
        "customer": {
            "customer_id": customer_id,
            "name": (
                f"{customer['first_name']} "
                f"{customer['last_name']}"
            ),
            "risk_score": new_risk_score,
            "risk_level": new_risk_level,
        },
        "changes": {
            "new_journey_event": 1,
            "new_ticket": 1,
            "risk_score_changed": True,
        },
    }


def ensure_action_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_actions (
            action_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            status TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            provider_id TEXT NOT NULL
        )
        """
    )

    ensure_tenant_schema(connection)

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_customer_actions_customer_id
        ON customer_actions(customer_id)
        """
    )


def action_row_to_dict(row):
    return {
        "action_id": row["action_id"],
        "customer_id": row["customer_id"],
        "customer_name": row["customer_name"],
        "risk_score": int(row["risk_score"] or 0),
        "risk_level": row["risk_level"],
        "action_type": row["action_type"],
        "status": row["status"],
        "assigned_to": row["assigned_to"],
        "note": row["note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/actions")
def get_actions(
    customer_id: str | None = Query(
        default=None,
        max_length=20,
    ),
    limit: int = Query(
        default=30,
        ge=1,
        le=100,
    ),
    current_user=Depends(get_current_user),
):
    with get_connection() as connection:
        ensure_action_table(connection)

        conditions = []
        parameters = []

        if customer_id and customer_id.strip():
            conditions.append("a.customer_id = ?")
            parameters.append(customer_id.strip())

        add_provider_condition(
            conditions,
            parameters,
            current_user,
            column="a.provider_id",
        )

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        rows = connection.execute(
            f"""
            SELECT
                a.*,
                TRIM(
                    COALESCE(c.first_name, '') || ' ' ||
                    COALESCE(c.last_name, '')
                ) AS customer_name,
                COALESCE(c.risk_score, 0) AS risk_score,
                COALESCE(c.risk_level, 'Unknown') AS risk_level
            FROM customer_actions a
            LEFT JOIN customer_metrics c
                ON c.customer_id = a.customer_id
                AND c.provider_id = a.provider_id
            {where_clause}
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            parameters + [limit],
        ).fetchall()

    items = [action_row_to_dict(row) for row in rows]

    return {
        "count": len(items),
        "items": items,
    }


@router.post("/actions")
def create_action(
    payload: ActionCreateRequest,
    current_user=Depends(get_current_user),
):
    allowed_action_types = {
        "Create support ticket",
        "Assign retention call",
        "Start investigation",
    }

    if payload.action_type not in allowed_action_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported action type.",
        )

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()

    with get_connection() as connection:
        ensure_action_table(connection)

        provider_id = provider_id_for_user(current_user)
        customer_provider_clause = ""
        customer_parameters = [payload.customer_id]

        if provider_id:
            customer_provider_clause = "AND provider_id = ?"
            customer_parameters.append(provider_id)

        customer = connection.execute(
            f"""
            SELECT customer_id, provider_id
            FROM customer_metrics
            WHERE customer_id = ?
            {customer_provider_clause}
            """,
            customer_parameters,
        ).fetchone()

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found.",
            )

        next_number = connection.execute(
            """
            SELECT COALESCE(
                MAX(
                    CAST(
                        SUBSTR(action_id, 2)
                        AS INTEGER
                    )
                ),
                0
            ) + 1 AS next_number
            FROM customer_actions
            """
        ).fetchone()["next_number"]

        action_id = f"A{int(next_number):06d}"

        connection.execute(
            """
            INSERT INTO customer_actions (
                action_id,
                customer_id,
                action_type,
                status,
                assigned_to,
                note,
                created_at,
                updated_at,
                provider_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action_id,
                payload.customer_id,
                payload.action_type,
                "Pending",
                payload.assigned_to,
                payload.note,
                now,
                now,
                customer["provider_id"],
            ),
        )

        row = connection.execute(
            """
            SELECT
                a.*,
                TRIM(
                    COALESCE(c.first_name, '') || ' ' ||
                    COALESCE(c.last_name, '')
                ) AS customer_name,
                COALESCE(c.risk_score, 0) AS risk_score,
                COALESCE(c.risk_level, 'Unknown') AS risk_level
            FROM customer_actions a
            LEFT JOIN customer_metrics c
                ON c.customer_id = a.customer_id
                AND c.provider_id = a.provider_id
            WHERE a.action_id = ?
            """,
            (action_id,),
        ).fetchone()

    return action_row_to_dict(row)


@router.patch("/actions/{action_id}/status")
def update_action_status(
    action_id: str,
    payload: ActionStatusRequest,
    current_user=Depends(get_current_user),
):
    allowed_statuses = {
        "Pending",
        "In Progress",
        "Resolved",
    }

    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Unsupported action status.",
        )

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()

    with get_connection() as connection:
        ensure_action_table(connection)

        provider_id = provider_id_for_user(current_user)
        provider_clause = ""
        parameters = [payload.status, now, action_id]

        if provider_id:
            provider_clause = "AND provider_id = ?"
            parameters.append(provider_id)

        result = connection.execute(
            f"""
            UPDATE customer_actions
            SET status = ?, updated_at = ?
            WHERE action_id = ?
            {provider_clause}
            """,
            parameters,
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Action not found.",
            )

        row_parameters = [action_id]
        row_provider_clause = ""

        if provider_id:
            row_provider_clause = "AND a.provider_id = ?"
            row_parameters.append(provider_id)

        row = connection.execute(
            f"""
            SELECT
                a.*,
                TRIM(
                    COALESCE(c.first_name, '') || ' ' ||
                    COALESCE(c.last_name, '')
                ) AS customer_name,
                COALESCE(c.risk_score, 0) AS risk_score,
                COALESCE(c.risk_level, 'Unknown') AS risk_level
            FROM customer_actions a
            LEFT JOIN customer_metrics c
                ON c.customer_id = a.customer_id
                AND c.provider_id = a.provider_id
            WHERE a.action_id = ?
            {row_provider_clause}
            """,
            row_parameters,
        ).fetchone()

    return action_row_to_dict(row)


@router.post("/reports/email")
def email_customer_journey_report(
    payload: ReportEmailRequest,
    current_user=Depends(get_current_user),
):
    try:
        recipient = normalize_email_address(
            payload.recipient
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    from datetime import datetime, timezone

    report_data = {
        "generated_at": datetime.now(
            timezone.utc
        ).astimezone().strftime(
            "%d.%m.%Y %H:%M"
        ),
        "generated_by": (
            current_user.get("name")
            or current_user.get("email")
            or "TecJA user"
        ),
        "summary": get_summary(current_user),
        "risk_summary": get_risk_summary(current_user),
        "journey_patterns": get_journey_patterns(
            limit=5,
            current_user=current_user,
        ),
        "ai_insights": get_ai_insights(current_user),
        "ticket_categories": (
            get_ticket_categories(current_user)
        ),
    }

    try:
        pdf_bytes = build_report_pdf(report_data)
        send_report_email(
            recipient,
            pdf_bytes,
            report_data=report_data,
        )
    except ReportEmailConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except ReportEmailDeliveryError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "message": (
            "PDF raporu başarıyla e-posta ile "
            f"gönderildi: {recipient}"
        ),
        "recipient": recipient,
        "attachment_size_bytes": len(pdf_bytes),
    }
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from pydantic import BaseModel
