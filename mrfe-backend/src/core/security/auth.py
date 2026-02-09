"""JWT auth, refresh rotation, and RBAC helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, cast
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.core.config.settings import settings

security_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Issued token pair payload."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    """Handles JWT issuing and verification."""

    def __init__(self) -> None:
        self._refresh_store: dict[str, str] = {}
        self._private_key, self._public_key = self._resolve_keys()

    def create_token_pair(self, user_id: str, roles: list[str]) -> TokenPair:
        """Issue access/refresh pair."""
        now = datetime.now(tz=timezone.utc)
        access_payload = {
            "sub": user_id,
            "roles": roles,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        }
        refresh_id = str(uuid4())
        refresh_payload = {
            "sub": user_id,
            "type": "refresh",
            "jti": refresh_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=settings.refresh_token_expire_days)).timestamp()),
        }
        access_token = jwt.encode(access_payload, self._private_key, algorithm=settings.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self._private_key, algorithm=settings.jwt_algorithm)
        self._refresh_store[user_id] = refresh_id
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def rotate_refresh_token(self, refresh_token: str, roles: list[str]) -> TokenPair:
        """Rotate refresh token and issue new pair."""
        payload = self._decode(refresh_token, expected_type="refresh")
        user_id = str(payload["sub"])
        current_jti = str(payload["jti"])
        stored = self._refresh_store.get(user_id)
        if stored != current_jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token replayed")
        return self.create_token_pair(user_id=user_id, roles=roles)

    def decode_access_token(self, token: str) -> dict[str, object]:
        """Decode and validate access token."""
        return self._decode(token, expected_type="access")

    def _decode(self, token: str, expected_type: str) -> dict[str, object]:
        """Decode token and assert type."""
        try:
            payload = cast(
                dict[str, object],
                jwt.decode(token, self._public_key, algorithms=[settings.jwt_algorithm]),
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid token",
            ) from exc
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token type")
        return payload

    @staticmethod
    def _resolve_keys() -> tuple[str, str]:
        """Load configured PEM keys or generate ephemeral RSA keys for local usage."""
        private_key = settings.jwt_private_key
        public_key = settings.jwt_public_key
        if private_key.startswith("-----BEGIN") and public_key.startswith("-----BEGIN"):
            return private_key, public_key
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        public_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        return private_pem, public_pem


auth_service = AuthService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, object]:
    """FastAPI dependency for authenticated user context (JWT or service API key)."""
    if credentials is not None:
        payload = auth_service.decode_access_token(credentials.credentials)
        return payload
    if x_api_key and x_api_key in settings.service_api_keys:
        return {"sub": "service-account", "roles": ["service", "reader", "trader"], "type": "api_key"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing credentials")


def require_role(required_role: str) -> Callable[..., dict[str, object]]:
    """Return dependency requiring a specific RBAC role."""

    def _checker(user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
        roles = user.get("roles", [])
        if not isinstance(roles, list) or required_role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user

    return _checker
