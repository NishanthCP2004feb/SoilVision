from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import HTTPException, status

from app.core.config import settings


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt_value, digest_value = encoded.split("$")
        candidate = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt_value), n=2**14, r=8, p=1)
        return hmac.compare_digest(candidate, base64.urlsafe_b64decode(digest_value))
    except (ValueError, TypeError):
        return False


def issue_token(user_id: str, lifetime_seconds: int = 3600) -> str:
    payload = json.dumps({"sub": user_id, "exp": int(time.time()) + lifetime_seconds}, separators=(",", ":")).encode()
    encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
    signature = hmac.new(settings.secret_key.encode(), encoded, hashlib.sha256).digest()
    return (encoded + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode()


def token_subject(token: str) -> str:
    try:
        encoded, signature = token.encode().split(b".")
        expected = hmac.new(settings.secret_key.encode(), encoded, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, base64.urlsafe_b64decode(signature + b"=" * (-len(signature) % 4))):
            raise ValueError("bad signature")
        payload = json.loads(base64.urlsafe_b64decode(encoded + b"=" * (-len(encoded) % 4)))
        if int(payload["exp"]) < time.time():
            raise ValueError("expired")
        return str(payload["sub"])
    except (KeyError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
