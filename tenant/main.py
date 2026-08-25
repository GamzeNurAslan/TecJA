from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import router
from backend.app.auth import get_user_from_token
from backend.app.database import get_connection
from backend.app.tenancy import ensure_tenant_schema


@asynccontextmanager
async def lifespan(app):
    with get_connection() as connection:
        ensure_tenant_schema(connection)

    yield


app = FastAPI(
    title="TecJA API",
    description="Telecom Customer Journey Analytics API",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PUBLIC_PATHS = {
    "/",
    "/api/health",
    "/api/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}


@app.middleware("http")
async def authentication_middleware(
    request: Request,
    call_next,
):
    path = request.url.path

    if request.method == "OPTIONS":
        return await call_next(request)

    if (
        path in PUBLIC_PATHS
        or path.startswith("/docs")
        or path.startswith("/redoc")
    ):
        return await call_next(request)

    authorization = request.headers.get(
        "Authorization",
        "",
    )

    if not authorization.startswith(
        "Bearer "
    ):
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Authentication required."
            },
        )

    token = authorization.removeprefix(
        "Bearer "
    ).strip()

    user = get_user_from_token(token)

    if user is None:
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Invalid or expired token."
            },
        )

    if (
        path == "/api/simulation/tick"
        and user["role"] != "admin"
    ):
        return JSONResponse(
            status_code=403,
            content={
                "detail": (
                    "Only admin users can run "
                    "the live simulation."
                )
            },
        )

    request.state.user = user

    return await call_next(request)


app.include_router(
    router,
    prefix="/api",
)


@app.get("/")
def root():
    return {
        "message": "TecJA API is running.",
    }
