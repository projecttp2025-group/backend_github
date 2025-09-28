import psycopg
from fastapi import APIRouter, HTTPException
from app.core.config import settings


router = APIRouter()

@router.get("/health")
def health():
    return {"Health" : "OK"}

@router.get("/health/db")
def db_health():
    try:
        with psycopg.connect(
            host=settings.db_host,
            port=int(settings.db_port),
            user=settings.db_user,
            password=settings.db_password,
            dbname=settings.db_name
        ) as connection:
            with  connection.cursor() as cursor:
                cursor.execute(
                    """SELECT
                  (to_regclass('main.users')    IS NOT NULL) AS users_exists,
                  (to_regclass('main.accounts') IS NOT NULL) AS accounts_exists,
                  (to_regclass('main.transactions')    IS NOT NULL) AS transactions_exists,
                  (to_regclass('main.receipts') IS NOT NULL) AS receipts_exists,
                  (to_regclass('main.categories')   IS NOT NULL) AS categories_exists;
                  """
                )
                users_exists, accounts_exists, transactions_exists, receipts_exists, categories_exists = cursor.fetchone()
            return {
            "schema": "main",
            "users_exists": bool(users_exists),
            "accounts_exists": bool(accounts_exists),
            "transactions_exists": bool(transactions_exists),
            "receipts_exists": bool(receipts_exists),
            "categories_exists": bool(categories_exists),
        }

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"DB check failed: {ex}")
 




@router.get("/readiness")
def readiness():
    return {"Readiness" : "OK"}

