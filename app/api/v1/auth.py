import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.jwt import auth
from app.db.psycopg import get_connection
from app.schemas.auth import (
    CodeVerifyIn,
    CodeVerifyOut,
    EmailIn,
    LoginIn,
    LogoutIn,
    RefreshIn,
    RequestCodeOut,
    SetPasswordIn,
    TokensOut,
)
from app.utils.mail_sender import send_code
from app.utils.security import hash_code, hash_password, sha256, verify_password

router = APIRouter()
logger = logging.getLogger("app.auth")


def _store_refresh(user_id: int, refresh_token: str, jti: str, exp_utc: datetime) -> None:
    logger.debug(f"Refresh token for {user_id} was stored in DB")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO main.refresh_tokens (user_id, token_hash, jti, expires_at)
            VALUES (%s, %s, %s, %s)
        """,
            (user_id, sha256(refresh_token), jti, exp_utc),
        )


def _decode_refresh_or_401(refresh_token: str) -> dict:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
            options={"require": ["exp", "iat"]},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid refresh token: {e}") from e
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Not a refresh token")
    if "sub" not in payload:
        raise HTTPException(401, "Token without subject")
    return payload


def _revoke_refresh_by_jti(jti: str) -> None:
    logger.debug(f"Revoke the refresh token with jti: {jti}")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("UPDATE main.refresh_tokens SET revoked = TRUE WHERE jti = %s", (jti,))


def _issue_pair_and_store(email: str, user_id: int) -> TokensOut:
    """
    Generate the pair of access/refresh tokens and save refresh-token in DB (hash + jti + expiry)
    """

    jti = secrets.token_urlsafe(16)
    access_token = auth.create_access_token(uid=email)
    refresh_token = auth.create_refresh_token(uid=email, data={"jti": jti})

    exp_utc = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    _store_refresh(user_id=user_id, refresh_token=refresh_token, jti=jti, exp_utc=exp_utc)

    logger.info("Pair (access/refresh) tokens was generated successful")
    return TokensOut(access_token=access_token, refresh_token=refresh_token)


def _is_refresh_active(email: str, refresh_token: str, jti: str) -> tuple[bool, int | None]:
    logger.debug(f"Checking the activeness of refresh token for {email}")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, (NOT rt.revoked) AND (rt.expires_at > now()) AS active
            FROM main.refresh_tokens rt
            JOIN main.users u ON u.id = rt.user_id
            WHERE u.email = %s
              AND rt.jti = %s
              AND rt.token_hash = %s
        """,
            (email, jti, sha256(refresh_token)),
        )
        row = cur.fetchone()
        if not row:
            return (False, None)
        user_id, active = int(row[0]), bool(row[1])
        return (active, user_id if active else None)


@router.post("/request-code", response_model=RequestCodeOut, summary="Send code on email")
def request_code(body: EmailIn):
    email = body.email.lower()
    logger.debug(f"Request code for {email}")
    code = f"{secrets.randbelow(1_000_000):06d}"
    code_h = hash_code(code)
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)

    logger.debug("Insert into 'email_codes' new row")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO main.email_codes 
            (email, code_hash, expires_at, attempts_left, used, verified_at)
            VALUES (%s, %s, %s, 5, FALSE, NULL)
            ON CONFLICT (email) DO UPDATE SET
              code_hash = EXCLUDED.code_hash,
              expires_at = EXCLUDED.expires_at,
              attempts_left = 5,
              used = FALSE,
              verified_at = NULL
        """,
            (email, code_h, expires),
        )

    logger.info(f"[DEV] send code {code} to {email}")
    try:
        send_code(to_email=email, code=str(code))
    except Exception as e:
        logger.error(f"Problems with sending the code: {e}")
    return RequestCodeOut()


@router.post("/verify-code", response_model=CodeVerifyOut, summary="Verify code from email")
def verify_code(body: CodeVerifyIn):
    email = body.email.lower()
    logger.debug(f"Code verification for {email}")
    code_h = hash_code(body.code)
    now = datetime.now(timezone.utc)

    logger.debug("Execute row from 'email_codes'")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT code_hash, expires_at, attempts_left, used
            FROM main.email_codes WHERE email = %s
        """,
            (email,),
        )

        row = cur.fetchone()
        if not row:
            logger.exception("Request the code")
            raise HTTPException(400, "Request the code")
        db_hash, expires_at, attempts_left, used = row
        if used:
            logger.exception("Code have been used")
            raise HTTPException(400, "Code have been used")
        if expires_at < now:
            logger.exception("The code has expired")
            raise HTTPException(400, "The code has expired")
        if attempts_left <= 0:
            logger.exception("The number of attempts has been exceeded")
            raise HTTPException(400, "The number of attempts has been exceeded")
        if code_h != db_hash:
            logger.exception("Invalid code")
            cur.execute(
                "UPDATE main.email_codes SET attempts_left = attempts_left - 1 WHERE email = %s",
                (email,),
            )
            raise HTTPException(400, "Invalid code")

        cur.execute(
            "UPDATE main.email_codes SET used = TRUE, verified_at = %s WHERE email = %s",
            (now, email),
        )

    return CodeVerifyOut(verified=True)


@router.post("/set-password", response_model=TokensOut, summary="Set password and get JWT")
def set_password(body: SetPasswordIn):
    email = body.email.lower()
    logger.debug(f"Set password for {email}")

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT verified_at FROM main.email_codes WHERE email = %s AND used = TRUE", (email,)
        )
        row = cur.fetchone()

        if not row or row[0] is None:
            logger.exception("At first verify email by code")
            raise HTTPException(400, "At first verify email by code")

        verified_at = row[0]
        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=timezone.utc)

        if (datetime.now(timezone.utc) - verified_at) > timedelta(minutes=5):
            logger.exception("Time to set password expired")
            raise HTTPException(400, "Time to set password expired")

        pwd_hash = hash_password(body.password.get_secret_value())

        cur.execute(
            """
            INSERT INTO main.users (email, password_hash) VALUES (%s, %s)
            ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
            RETURNING id
            """,
            (email, pwd_hash),
        )

        logger.info("New user was added")
        user_id = int(cur.fetchone()[0])

    return _issue_pair_and_store(email=email, user_id=user_id)


@router.post("/login", response_model=TokensOut, summary="Sign in with email and password")
def login(body: LoginIn):
    email = body.email.lower()
    logger.info(f"User with email: {email} is signing in")

    logger.debug("Checking the correctness of creds")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT id, password_hash FROM main.users WHERE email = %s
            """,
            (email,),
        )
        row = cur.fetchone()
        if not row or not row[1]:
            raise HTTPException(401, "Incorrect credentials")
        user_id, pwd_hash = int(row[0]), row[1]
        if not verify_password(body.password.get_secret_value(), pwd_hash):
            raise HTTPException(401, "Incorrect credentials")

    return _issue_pair_and_store(email=email, user_id=user_id)


@router.post(
    "/refresh", response_model=TokensOut, summary="Update access/refresh tokens with refresh"
)
def refresh_tokens(payload: RefreshIn):
    data = _decode_refresh_or_401(payload.refresh_token)
    email: str = data["sub"]
    jti: str | None = data.get("jti")
    logger.debug(f"Update access/refresh tokens for {email} and {jti}")
    if not jti:
        logger.exception("Missing jti in refresh token")
        raise HTTPException(401, "Missing jti in refresh token")

    active, user_id = _is_refresh_active(email, payload.refresh_token, jti)
    if not active or user_id is None:
        logger.exception("Refresh token revoked or expired")
        raise HTTPException(401, "Refresh token revoked or expired")

    _revoke_refresh_by_jti(jti)

    return _issue_pair_and_store(email=email, user_id=user_id)


@router.post("/logout", summary="Revoke refresh token(logout)")
def logout(body: LogoutIn):
    logger.info("User in trying to logout")
    try:
        data = _decode_refresh_or_401(body.refresh_token)
    except Exception:
        logger.exception("Somehing went wrong")
        return {"Ok": True}

    if data.get("type") == "refresh" and "jti" in data:
        _revoke_refresh_by_jti(data["jti"])
    return {"ok": True}
