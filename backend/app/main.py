from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    from app.db.session import engine

    await engine.dispose()


limiter = Limiter(key_func=get_remote_address)

_prod = settings.is_production
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=None if _prod else f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=None if _prod else f"{settings.API_V1_PREFIX}/docs",
    redoc_url=None if _prod else f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"], include_in_schema=False)
async def health_check(request: Request) -> JSONResponse:
    from sqlalchemy import text
    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return JSONResponse({"status": "healthy", "database": "ok"})
    except Exception as exc:
        return JSONResponse(
            {"status": "unhealthy", "database": str(exc)},
            status_code=503,
        )
