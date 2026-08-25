import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from backend.app.database import get_connection
from backend.app.tenancy import (
    DEFAULT_PROVIDER_ID,
    DEFAULT_PROVIDER_NAME,
    ensure_tenant_schema,
)

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)


USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@tecja.com",
        "password_salt": "tecja-admin-v1",
        "password_hash": (
            "8781ff34209060d9059df0b6e66c3d3ef7c3c988d14460b01b9644aec657daf7"
        ),
        "role": "admin",
        "name": "Admin User",
        "provider_id": None,
        "provider_name": "All providers",
    },
    "analyst": {
        "username": "analyst",
        "email": "analyst@tecja.com",
        "password_salt": "tecja-analyst-v1",
        "password_hash": (
            "acec57ca451ad8347b41c513e9a40148803980c5893ef61c72942f1de57ccece"
        ),
        "role": "analyst",
        "name": "Analytics User",
        "provider_id": DEFAULT_PROVIDER_ID,
        "provider_name": DEFAULT_PROVIDER_NAME,
    },
    "analyst2": {
        "username": "analyst2",
        "email": "analyst2@tecja.com",
        "password_salt": "tecja-analyst2-v1",
        "password_hash": (
            "6757999e85d50812c59b9c687d2ae00df3532e1f8a0d23fcb0ce1d7dd3059631"
        ),
        "role": "analyst",
        "name": "ISS-2 Analyst",
        "provider_id": "ISP002",
        "provider_name": "AnadoluNet Demo ISP",
    },
}


SESSION_TTL_HOURS = 8
PASSWORD_ITERATIONS = 120_000


bearer_scheme = HTTPBearer(
    auto_error=False
)


def authenticate_user(identifier, password):
    normalized_identifier = identifier.strip().lower()

    user = next(
        (
            candidate
            for candidate in USERS.values()
            if candidate["username"].lower()
            == normalized_identifier
            or candidate["email"].lower()
            == normalized_identifier
        ),
        None,
    )

    if user is None:
        return None

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        user["password_salt"].encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()

    if not hmac.compare_digest(
        password_hash,
        user["password_hash"],
    ):
        return None

    return {
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
        "provider_id": user.get("provider_id"),
        "provider_name": user.get("provider_name"),
    }


def create_session(user):
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(hours=SESSION_TTL_HOURS)
    ).isoformat()

    _ensure_session_table()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO auth_sessions (
                token,
                username,
                email,
                role,
                name,
                provider_id,
                provider_name,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token,
                user["username"],
                user["email"],
                user["role"],
                user["name"],
                user.get("provider_id"),
                user.get("provider_name"),
                expires_at,
            ),
        )

    return token


def get_user_from_token(token):
    if not token:
        return None

    _ensure_session_table()

    with get_connection() as connection:
        session = connection.execute(
            """
            SELECT
                username,
                email,
                role,
                name,
                provider_id,
                provider_name,
                expires_at
            FROM auth_sessions
            WHERE token = ?
            """,
            (token,),
        ).fetchone()

    if session is None:
        return None

    expires_at = session["expires_at"]

    if not expires_at:
        remove_session(token)
        return None

    try:
        expires_at_value = datetime.fromisoformat(
            expires_at
        )
    except ValueError:
        remove_session(token)
        return None

    if expires_at_value <= datetime.now(timezone.utc):
        remove_session(token)
        return None

    return {
        "username": session["username"],
        "email": session["email"],
        "role": session["role"],
        "name": session["name"],
        "provider_id": session["provider_id"],
        "provider_name": session["provider_name"],
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    user = get_user_from_token(
        credentials.credentials
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    return user


def require_admin(
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required.",
        )

    return current_user


def remove_session(token):
    if not token:
        return

    _ensure_session_table()

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM auth_sessions
            WHERE token = ?
            """,
            (token,),
        )


def _ensure_session_table():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                provider_id TEXT,
                provider_name TEXT,
                expires_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        ensure_tenant_schema(connection)

        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(auth_sessions)"
            ).fetchall()
        }

        if "provider_name" not in columns:
            connection.execute(
                "ALTER TABLE auth_sessions "
                "ADD COLUMN provider_name TEXT"
            )

        if "expires_at" not in columns:
            connection.execute(
                "ALTER TABLE auth_sessions "
                "ADD COLUMN expires_at TEXT"
            )

        connection.execute(
            """
            UPDATE auth_sessions
            SET provider_name = ?
            WHERE provider_name IS NULL
            OR TRIM(provider_name) = ''
            """,
            (DEFAULT_PROVIDER_NAME,),
        )

        legacy_expiry = (
            datetime.now(timezone.utc)
            + timedelta(hours=SESSION_TTL_HOURS)
        ).isoformat()

        connection.execute(
            """
            UPDATE auth_sessions
            SET expires_at = ?
            WHERE expires_at IS NULL
            OR TRIM(expires_at) = ''
            """,
            (legacy_expiry,),
        )
