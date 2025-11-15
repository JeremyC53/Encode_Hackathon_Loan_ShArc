from __future__ import annotations

from fastapi import FastAPI

from .routes import router


def create_app() -> FastAPI:
    """
    Application factory so we can import the app in tests or ASGI servers.
    """
    app = FastAPI(
        title="Loan ShArc Backend",
        version="0.1.0",
        description="API gateway for ingesting freelancer payout histories.",
    )
    app.include_router(router)
    return app


app = create_app()
