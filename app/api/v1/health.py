import logging

from fastapi import APIRouter, HTTPException
from app.db.psycopg import get_connection
from app.db.models import *
from app.db.database import database_engine
from sqlalchemy import inspect

router = APIRouter()
logger = logging.getLogger("app.health")


@router.get("/health")
def health():
    logger.debug("Health endpoint activated")
    return {"Health": "OK"}


@router.get("/health/db")
def db_health():
    try:
        logger.debug("Checking DB tables")
        inspector = inspect(database_engine)
        tables = inspector.get_table_names(schema='main')

        return {
            'users_exists': 'users' in tables,
            'accounts_exists': 'accounts' in tables,
            'transactions_exists': 'transactions' in tables,
            'receipts_exists': 'receipts' in tables,
            'categories_exists': 'categories' in tables,
            'email_codes_exists': 'email_codes' in tables,
            'refresh_tokens_exists': 'refresh_tokens' in tables
        }
    except Exception as ex:
        logger.exception("DB_existing_tables:ERROR")
        raise HTTPException(status_code=500, detail=f"DB check failed: {ex}") from ex


@router.get("/health/db/auth/email_codes")
def check_auth_email_codes():
    try:
        logger.debug("Checking 'email_codes' table in DB")
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT email, code_hash, expires_at, attempts_left, used, verified_at 
                    FROM main.email_codes
                    """
            )
            row = cur.fetchone()
            email, code_hash, expires_at, attempts_left, used, verified_at = row
            logger.info("Table 'email_codes' tables exist")
            return {
                "schema": "main",
                "email": email,
                "code_hash": code_hash,
                "expires_at": expires_at,
                "attempts_left": attempts_left,
                "used": used,
                "verified_at": verified_at,
            }

    except Exception as ex:
        logger.exception("DB 'email_codes' table:ERROR")
        raise HTTPException(status_code=500, detail=f"DB check failed: {ex}") from ex


@router.get("/health/db/auth/refresh_tokens")
def check_auth_refresh_tokens():
    try:
        logger.debug("Checking 'refresh_tokens' table in DB")
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT id, user_id, token_hash, jti, created_at, expires_at, revoked 
                    FROM main.refresh_tokens
                    """
            )
            row = cur.fetchone()
            id, user_id, token_hash, jti, created_at, expires_at, revoked = row
            logger.info("Table 'refresh_tokens' tables exist")
            return {
                "schema": "main",
                "token_id": id,
                "user_id": user_id,
                "token_hash": token_hash,
                "jti": jti,
                "created_at": created_at,
                "expires_at": expires_at,
                "revoked": revoked,
            }

    except Exception as ex:
        logger.exception("DB 'refresh_tokens' table:ERROR")
        raise HTTPException(status_code=500, detail=f"DB check failed: {ex}") from ex


@router.get("/health/db/auth/users")
def check_auth_users():
    try:
        logger.debug("Checking 'users' table in DB")
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT id, email, password_hash, created_at, is_admin FROM main.users
                    """
            )
            row = cur.fetchone()
            id, email, password_hash, created_at, is_admin = row
            logger.info("Table 'users' tables exist")
            return {
                "schema": "main",
                "user_id": id,
                "email": email,
                "password_hash": password_hash,
                "created_at": created_at,
                "is_admin": is_admin
            }

    except Exception as ex:
        logger.exception("DB 'users' table:ERROR")
        raise HTTPException(status_code=500, detail=f"DB check failed: {ex}") from ex


@router.get("/health/readiness")
def readiness():
    logger.debug("Readiness endpoint activated")
    return {"Readiness": "OK"}
