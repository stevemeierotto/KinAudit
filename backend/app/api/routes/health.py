from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database.session import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready() -> JSONResponse:
    if check_database_connection():
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "database": "reachable"},
        )
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "database": "unreachable"},
    )
