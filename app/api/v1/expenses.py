import logging
from datetime  import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
import jwt
from app.core.config import settings
from app.core.jwt import auth
from app.db.psycopg import get_connection
from app.schemas.expense import(
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseRead,
    ExpenseList
)

router = APIRouter()
logger = logging.getLogger("app.expenses")


@router.get("/expenses", response_model=ExpenseRead, dependencies=[Depends(auth.access_token_required)])
def get_expenses():
    return {"Expenses": "OK"}


@router.post("/expenses", dependencies=[Depends(auth.access_token_required)])
def create_expense(body : ExpenseCreate, request : Request):   #### HARDCODE значение для category_id
                                                    #### добавить в SELECT запрос INNER JOIN main.categories ON users.id = categories.user_id 

    access_token = request.cookies.get("my-access-token")
    if not access_token:
        raise HTTPException(401, "No access token found in cookie")
    
    try:
        payload = jwt.decode(
            access_token, 
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
            options={"require": ["exp", "iat"]},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid access token: {e}") from e
    
    if payload.get("type") != "access":
        raise HTTPException(401, "Not an access token")
    
    email = payload["sub"]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT users.id, accounts.id FROM main.users INNER JOIN main.accounts ON users.id = accounts.user_id 
            WHERE users.email = %s
            """,
            (email, )
        )
        
        row = cur.fetchone()
        user_id, account_id = row

        cur.execute(
            """
            INSERT INTO main.transactions
            (user_id, account_id, category_id, amount, date, description, created_at)
            VALUES(%s, %s, 2, %s, %s, %s, %s)   
            """,
            (user_id, account_id, body.amount, body.date, body.description, datetime.now(timezone.utc))
        )
    logger.info(f"Expense for {email} was created")
    return {"Create expense": "OK"}


@router.get("/expenses/{id}", dependencies=[Depends(auth.access_token_required)])
def get_expense_by_id(id: int):
    return {f"Get expense for {id}": "OK"}


@router.patch("/expenses/{id}", dependencies=[Depends(auth.access_token_required)])
def add_expenses(id: int):
    return {f"Add expense for {id}": "OK"}


@router.delete("/expenses/{id}", dependencies=[Depends(auth.access_token_required)])
def delete_expenses(id: int):
    return {f"Delete expense for {id}": "OK"}
