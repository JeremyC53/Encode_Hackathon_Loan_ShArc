from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .routes import router
from data_sources.google_mail import main as google_mail_main


def create_app() -> FastAPI:
    """
    Application factory so we can import the app in tests or ASGI servers.
    """

    app = FastAPI(
        title="Loan ShArc Backend",
        version="0.1.0",
        description="API gateway for ingesting freelancer payout histories.",
    )

    # ⭐ Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # or ["http://localhost:5173"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ⭐ Include router from /routes
    app.include_router(router)

    # ⭐ Add your custom endpoints here
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

    return app


app = create_app()
