from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .routes import router
from .database import init_db
from .blockchain_listener import listen_to_blockchain_events

# Add parent directory to path to import data_sources
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from data_sources.google_mail import main as google_mail_main
except ImportError:
    # If data_sources is not available, create a dummy function
    def google_mail_main():
        print("Warning: data_sources.google_mail not available")
        return None


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

    # ⭐ Initialize database on startup
    @app.on_event("startup")
    async def startup_event():
        init_db()
        # Start blockchain event listener in background
        asyncio.create_task(listen_to_blockchain_events())

    # ⭐ Include router from /routes
    app.include_router(router)

    # ⭐ Add your custom endpoints here
    @app.post("/run-google-mail")
    def run_google_mail():
        google_mail_main()
        return {"status": "ok"}

    @app.get("/uber-earnings", response_class=PlainTextResponse)
    def get_uber_earnings():
        csv_path = Path(__file__).parent.parent.parent / "secrets" / "uber_earnings.csv"
        if csv_path.exists():
            with open(csv_path, "r") as f:
                content = f.read()
            print(">>> /uber-earnings hit")
            return content
        else:
            return "No earnings data available. Connect your Google account in Settings."

    return app


app = create_app()
