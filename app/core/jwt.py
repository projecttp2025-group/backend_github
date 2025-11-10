from datetime import timedelta

from authx import AuthX, AuthXConfig

from app.core.config import settings

config = AuthXConfig(
    JWT_SECRET_KEY=settings.jwt_secret,
    JWT_ALGORITHM=settings.jwt_alg,
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=settings.access_token_expire_min),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=settings.refresh_token_expire_days),
    JWT_ACCESS_COOKIE_NAME=settings.access_token_cookie_name,
    JWT_COOKIE_CSRF_PROTECT=False,
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_COOKIE_SECURE=True,
)

auth = AuthX(config=config)
