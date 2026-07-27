"""
Ghana Tourism Guide — FastAPI backend.

Replaces the old Gradio-only main.py. The React frontend talks to these
endpoints:

  POST /auth/signup     — create account
  POST /auth/login      — get JWT token
  GET  /auth/me         — current user (requires Bearer token)
  POST /api/chat        — send a message to the AI guide (requires Bearer token)
"""

import asyncio
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chatbot.auth import (
    authenticate_user,
    create_token,
    create_user,
    get_user_by_id,
    verify_token,
)
from chatbot.responder import generate_response

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Ghana Tourism Guide API")

# Allow the Netlify frontend + localhost for dev.
# NOTE: allow_credentials=True means origins must be explicit, not "*"
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,https://ghana-guide.netlify.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Auth dependency — extracts the current user from the Authorization header.
# ---------------------------------------------------------------------------

async def get_current_user(authorization: str = Header(...)):
    """Extract and verify the Bearer token, return the user dict."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/signup")
def signup(body: SignUpRequest):
    """Register a new account. Returns the created user + JWT token."""
    try:
        user = create_user(body.name, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Server config error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {e}")
    token = create_token(user["id"], user["email"])
    return {"user": user, "token": token}


@app.post("/auth/login")
def login(body: LoginRequest):
    """Authenticate and return a JWT token."""
    try:
        user = authenticate_user(body.email, body.password)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Server config error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"], user["email"])
    return {"user": user, "token": token}


@app.get("/auth/me")
def me(user=Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return {"user": user}


# ---------------------------------------------------------------------------
# Chat route — requires a valid JWT token.
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    history: list[list[str]] = []


@app.post("/api/chat")
async def chat(body: ChatRequest, user=Depends(get_current_user)):
    """Send a message to the Ghana tourism AI and get a reply."""
    reply = await generate_response(body.message)
    return {"reply": reply}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entry point for local dev (python main.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
