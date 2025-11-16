from __future__ import annotations
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import ollama
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
        with open("data_sources/uber_earnings.csv", "r") as f:
            content = f.read()
        print(">>> /uber-earnings hit")
        return content
    @app.post("/chat")
    def chat_endpoint(payload: dict):
        message = payload.get("message", "")
        wallet_address = payload.get("wallet_address")

        MAX_LOAN = 50

        print("\n\n================= NEW /chat CALL =================")
        print("User message:", message)
        print("Wallet:", wallet_address)
        print("==================================================\n")

        # -----------------------------------
        # ⭐ Step 1 — Ask LLM to classify intent
        # -----------------------------------
        try:
            print("👉 Calling Ollama classifier...")
            classify = ollama.chat(
                model="gemma3:4b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a loan-intent classifier.\n"
                            "Respond ONLY in JSON like:\n"
                            '{ "is_loan_request": true/false, "amount": number|null }\n'
                            "NO markdown, NO backticks."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
            )

            print("\n👉 classify OBJECT:", classify)
            print("👉 type(classify):", type(classify))

            # Read the actual content from the response
            try:
                content = classify["message"]["content"]
            except Exception as e:
                print("❌ classify['message']['content'] failed:", e)
                content = classify.message["content"]

            print("\n👉 RAW content from LLM (repr):", repr(content))

            # Clean out code fences if they exist
            cleaned = content.replace("```json", "").replace("```", "").strip()
            print("\n👉 After removing ``` fences (repr):", repr(cleaned))

            # If there are literal '\n' sequences, turn them into real newlines
            cleaned = cleaned.replace("\\n", "\n")
            print("\n👉 After unescaping \\n (repr):", repr(cleaned))

            # Parse JSON
            import json
            decision = json.loads(cleaned)
            print("\n🎉 Parsed decision:", decision)

            is_loan_request = bool(decision.get("is_loan_request"))
            amount = decision.get("amount")

            print("👉 is_loan_request:", is_loan_request)
            print("👉 amount:", amount)

        except Exception as e:
            print("\n❌ ERROR DURING CLASSIFY PARSE:", e)
            is_loan_request = False
            amount = None

        print("\n👉 FINAL is_loan_request:", is_loan_request)
        print("👉 FINAL amount:", amount)
        print("==================================================\n")

        # -----------------------------------
        # ⭐ Step 2 — Loan logic (LLM-decided)
        # -----------------------------------
        if is_loan_request:
            if amount is None:
                return {"reply": "How much would you like to borrow?"}

            if amount <= MAX_LOAN:
                try:
                    resp = requests.post(
                        "http://localhost:8000/api/loans/issue",
                        json={
                            "borrower_address": wallet_address,
                            "principal": amount * 1000000,
                            "wait_for_confirmation": False,
                        },
                    )
                    return {
                        "reply": f"Your loan for ${amount} has been issued!",
                        "tx": resp.json(),
                    }

                except Exception as e:
                    return {"reply": f"Error issuing loan: {e}"}

            else:
                return {
                    "reply": f"Sorry, your limit is ${MAX_LOAN}. You asked for ${amount}, which is too high."
                }

        # -----------------------------------
        # ⭐ Step 3 — Normal AI chat
        # -----------------------------------
        try:
            ai = ollama.chat(
                model="gemma3:4b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a short, helpful financial assistant."
                    },
                    {"role": "user", "content": message},
                ],
            )
            reply_text = ai["message"]["content"]
            print("\n👉 Normal chat reply:", repr(reply_text))
            return {"reply": reply_text}

        except Exception as e:
            print("\n❌ ERROR IN NORMAL CHAT:", e)
            return {"reply": f"AI error: {e}"}
    return app


app = create_app()
