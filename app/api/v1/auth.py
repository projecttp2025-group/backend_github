import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import auth
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
from app.db.models import *
from app.db.database import get_db
from app.api.exceptions import NoRequestCodeSend, InvalidCredentials

router = APIRouter()
logger = logging.getLogger("app.auth")


### HELPER FUNCTIONS
def _store_refresh(user_id: int, refresh_token: str, jti: str, exp_utc: datetime, db: Session) -> None:
    logger.debug(f"Refresh token for {user_id} was stored in DB")
    refresh_token_object = RefreshToken(user_id=user_id, token_hash=sha256(refresh_token), jti=jti, expires_at=exp_utc)
    db.add(refresh_token_object)
    db.commit()


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


def _revoke_refresh_by_jti(jti: str, db: Session) -> None:
    logger.debug(f"Revoke the refresh token with jti: {jti}")
    token_object = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    token_object.revoked = True
    db.commit()
    db.refresh(token_object)


def _issue_pair_and_store(email: str, user_id: int, db: Session) -> TokensOut:
    """
    Generate the pair of access/refresh tokens and save refresh-token in DB (hash + jti + expiry)
    """

    jti = secrets.token_urlsafe(16)
    access_token = auth.create_access_token(uid=email)
    refresh_token = auth.create_refresh_token(uid=email, data={"jti": jti})

    exp_utc = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    _store_refresh(user_id=user_id, refresh_token=refresh_token, jti=jti, exp_utc=exp_utc, db=db)

    logger.info("Pair (access/refresh) tokens was generated successful")
    return TokensOut(access_token=access_token, refresh_token=refresh_token)


def _is_refresh_active(email: str, refresh_token: str, jti: str, db: Session) -> tuple[bool, int | None]:
    logger.debug(f"Checking the activeness of refresh token for {email}")
    refresh_token_object = db.query(RefreshToken).join(User, User.id == RefreshToken.user_id).filter(
        User.email == email, RefreshToken.token_hash == sha256(refresh_token), RefreshToken.jti == jti).first()
    
    if not refresh_token_object:
        return (False, None)
    
    active = False
    if not refresh_token_object.revoked and refresh_token_object.expires_at > datetime.now():
        active = True

    return (active, refresh_token_object.user_id if active else None)


### ENDPOINTS
@router.post("/request-code", response_model=RequestCodeOut, summary="Send code on email")
def request_code(body: EmailIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    logger.debug(f"Request code for {email}")
    code = f"{secrets.randbelow(1_000_000):06d}"
    code_h = hash_code(code)
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)

    logger.debug("Insert into 'email_codes' new row")
    
    existing_row = db.query(EmailCode).filter(EmailCode.email == email).first()

    if existing_row:
        existing_row.code_hash = code_h
        existing_row.expires_at = expires
        existing_row.attempts_left = 5
    else:
        email_code = EmailCode(email=email, code_hash=code_h, expires_at=expires)
        db.add(email_code)

    db.commit()
    if existing_row:
        db.refresh(existing_row)

    logger.info(f"[DEV] send code {code} to {email}")
    try:
        send_code(to_email=email, code=str(code))
    except Exception as e:
        logger.error(f"Problems with sending the code: {e}")
    return RequestCodeOut()


@router.post("/verify-code", response_model=CodeVerifyOut, summary="Verify code from email")
def verify_code(body: CodeVerifyIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    logger.debug(f"Code verification for {email}")
    code_h = hash_code(body.code)
    now = datetime.now(timezone.utc)

    logger.debug("Execute row from 'email_codes'")
    email_code = db.query(EmailCode).filter(EmailCode.email == email).first()
    
    if not email_code:
        logger.exception("Request the code")
        raise NoRequestCodeSend("Request the code")
    if email_code.used:
        logger.exception("Code have been used")
        raise NoRequestCodeSend("Code have been used")
    if email_code.expires_at < now:
        logger.exception("The code has expired")
        raise NoRequestCodeSend("The code has expired")
    if email_code.attempts_left <= 0:
        logger.exception("The number of attempts has been exceeded")
        raise NoRequestCodeSend("The number of attempts has been exceeded")
    if email_code.code_hash != code_h:
        logger.exception("Invalid code")
        email_code.attempts_left -= 1
        db.commit()
        db.refresh(email_code)
        raise HTTPException(400, "Invalid code")
    
    email_code.used = True
    email_code.verified_at = now
    db.commit()
    db.refresh(email_code)

    return CodeVerifyOut(verified=True)


@router.post("/set-password", response_model=TokensOut, summary="Set password and get JWT")
def set_password(body: SetPasswordIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    logger.debug(f"Set password for {email}")
        
    email_code = db.query(EmailCode).filter(EmailCode.email == email).first()

    if email_code is None:
        logger.exception("At first verify email by code")
        raise HTTPException(400, "At first verify email by code")

    if email_code.verified_at.tzinfo is None:
        verified_at = verified_at.replace(tzinfo=timezone.utc)

    if (datetime.now(timezone.utc) - email_code.verified_at) > timedelta(minutes=5):
        logger.exception("Time to set password expired")
        raise HTTPException(400, "Time to set password expired")

    pwd_hash = hash_password(body.password.get_secret_value())

    user_from_db = db.query(User).filter(User.email == email).first()
    if user_from_db:
        user_from_db.password_hash = pwd_hash
        db.refresh(user_from_db)
    else:
        user_object = User(email=email, password_hash=pwd_hash)
        db.add(user_object)

    db.commit()

    new_user = db.query(User).filter(User.email == email).first()

    account_from_db = db.query(Account).filter(Account.id == new_user.id).first()
    if account_from_db is None:
        account = Account(user_id=new_user.id, name=email, currency='BYN', created_at=datetime.now(timezone.utc))
        db.add(account)
    db.commit()

    logger.info("New user was added")
    return _issue_pair_and_store(email=email, user_id=new_user.id, db=db)


@router.post("/login", response_model=TokensOut, summary="Sign in with email and password")
def login(body: LoginIn, response : Response, db: Session = Depends(get_db)):
    email = body.email.lower()
    logger.info(f"User with email: {email} is signing in")

    logger.debug("Checking the correctness of creds")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise InvalidCredentials()
    
    if not verify_password(body.password.get_secret_value(), user.password_hash):
        raise InvalidCredentials()

    tokens_pair : TokensOut = _issue_pair_and_store(email=email, user_id=user.id, db=db)
    response.set_cookie(auth.config.JWT_ACCESS_COOKIE_NAME, tokens_pair.access_token)
    return tokens_pair


@router.post("/refresh", response_model=TokensOut, summary="Update jwt tokens with refresh")
def refresh_tokens(payload: RefreshIn, db: Session = Depends(get_db)):
    data = _decode_refresh_or_401(payload.refresh_token)
    email: str = data["sub"]
    jti: str | None = data.get("jti")
    logger.debug(f"Update access/refresh tokens for {email} and {jti}")
    if not jti:
        logger.exception("Missing jti in refresh token")
        raise HTTPException(401, "Missing jti in refresh token")

    active, user_id = _is_refresh_active(email, payload.refresh_token, jti, db)
    if not active or user_id is None:
        logger.exception("Refresh token revoked or expired")
        raise HTTPException(401, "Refresh token revoked or expired")

    _revoke_refresh_by_jti(jti, db)

    return _issue_pair_and_store(email=email, user_id=user_id, db=db)


@router.post("/logout", summary="Revoke refresh token(logout)")
def logout(body: LogoutIn, db: Session = Depends(get_db)):
    logger.info("User in trying to logout")
    try:
        data = _decode_refresh_or_401(body.refresh_token)
    except Exception:
        logger.exception("Somehing went wrong")
        return {"Ok": True}

    if data.get("type") == "refresh" and "jti" in data:
        _revoke_refresh_by_jti(data["jti"], db)
    return {"ok": True}
