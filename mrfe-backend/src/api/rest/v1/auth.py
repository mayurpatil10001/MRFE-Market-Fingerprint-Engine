"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.rest.v1.schemas import RefreshTokenRequest, TokenRequest, TokenResponse
from src.core.security import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def issue_token(payload: TokenRequest) -> TokenResponse:
    """Issue access and refresh tokens."""
    pair = auth_service.create_token_pair(user_id=payload.user_id, roles=payload.roles)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest) -> TokenResponse:
    """Rotate refresh token."""
    pair = auth_service.rotate_refresh_token(payload.refresh_token, roles=payload.roles)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
    )
