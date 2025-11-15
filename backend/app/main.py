from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from data_sources.google_mail import main as google_mail_main
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Loan ShArc Backend",
        version="0.1.0",
        description="API gateway for ingesting freelancer payout histories.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # Temporarily disabled Gmail ingestion helper routes; keep for future reuse.
    """
    @app.post("/run-google-mail")
    def run_google_mail():
        google_mail_main()
        return {"status": "ok"}

    @app.get("/uber-earnings", response_class=PlainTextResponse)
    def get_uber_earnings():
        with open("secrets/uber_earnings.csv", "r") as f:
            content = f.read()
        print(">>> /uber-earnings hit")
        return content
    """

    return app


app = create_app()
