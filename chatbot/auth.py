"""
Authentication module — MongoDB + JWT + bcrypt.

Handles user registration, login, password hashing, and token verification.
The MongoDB connection string is read from MONGODB_URI env var.
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pymongo import MongoClient

# --- Configuration ---
MONGODB_URI = os.getenv("MONGODB_URI", "")
JWT_SECRET = os.getenv("JWT_SECRET", "ghana-guide-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72

# --- MongoDB connection (lazy, connects on first use) ---
_client: MongoClient | None = None
_db = None


def _get_db():
    """Return the database handle, connecting to MongoDB on first call."""
    global _client, _db
    if _db is not None:
        return _db
    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI is not set")
    _client = MongoClient(
        MONGODB_URI,
        tls=True,
        tlsAllowInvalidCertificates=True,
    )
    _db = _client["ghana_guide"]
    return _db


def _get_users():
    """Return the users collection."""
    return _get_db()["users"]


# --- Password hashing ---

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# --- JWT tokens ---

def create_token(user_id: str, email: str) -> str:
    """Create a signed JWT token for the given user."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Decode and verify a JWT token. Returns the payload or None if invalid."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# --- User CRUD ---

def create_user(name: str, email: str, password: str) -> dict:
    """Register a new user. Raises ValueError if email already exists."""
    users = _get_users()

    if users.find_one({"email": email}):
        raise ValueError("An account with this email already exists")

    hashed = hash_password(password)
    user = {
        "name": name,
        "email": email,
        "password": hashed,
        "created_at": datetime.now(timezone.utc),
    }
    result = users.insert_one(user)
    return {"id": str(result.inserted_id), "name": name, "email": email}


def authenticate_user(email: str, password: str) -> dict | None:
    """Verify credentials and return user dict (without password) or None."""
    users = _get_users()
    user = users.find_one({"email": email})
    if not user or not check_password(password, user["password"]):
        return None
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}


def get_user_by_id(user_id: str) -> dict | None:
    """Look up a user by their MongoDB ObjectId string."""
    from bson import ObjectId

    users = _get_users()
    try:
        user = users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    if not user:
        return None
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}
