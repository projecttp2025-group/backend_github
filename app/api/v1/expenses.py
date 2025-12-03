import logging
from datetime  import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Query
import jwt
from app.core.config import settings
from app.core.jwt import auth
from app.db.psycopg import get_connection
from app.db.database import get_db
from app.db.models import *
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas.expense import(
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseRead,
    ExpenseList
)
from app.api.exceptions import NoAccessTokenFound, AccountNotFound

router = APIRouter()
logger = logging.getLogger("app.expenses")


@router.get("/expenses", dependencies=[Depends(auth.access_token_required)])
def get_expenses(request: Request, account_name: str = Query(), db: Session = Depends(get_db)):
    access_token = request.cookies.get("my-access-token")
    if not access_token:
        raise NoAccessTokenFound()

    logger.info(f"Get list of expenses for account {account_name}")
    account = db.query(Account).filter(Account.name == account_name).first()

    if not account:
        raise AccountNotFound()

    expenses_list = db.query(Transaction).filter(Transaction.account_id == account.id).all()
    if not expenses_list:
        raise AccountNotFound("No transactions for this account")
    
    total_result = db.query(func.sum(Transaction.amount)).filter(Transaction.account_id == account.id).scalar()
    result_expenses = ExpenseList(total=total_result, items=expenses_list)
    return result_expenses


@router.post("/expenses", dependencies=[Depends(auth.access_token_required)])
def create_expense(body : ExpenseCreate, request : Request, db: Session = Depends(get_db)):   
    access_token = request.cookies.get("my-access-token")
    if not access_token:
        raise NoAccessTokenFound()
    
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
    user_data = db.query(User).join(Account, Account.user_id == User.id).filter(User.email == email).first()
    category_data = db.query(Category).filter(Category.name == body.category_name).first()

    new_transaction = Transaction(user_id=user_data.id, account_id=user_data.accounts[0].id, category_id=category_data.id,
                                  amount=body.amount, date=body.date, description=body.description, created_at=datetime.now(timezone.utc))
    db.add(new_transaction)
    db.commit()
    logger.info(f"Expense for {email} was created")
    return {"Create expense": "OK"}


@router.get("/expenses/{id}", dependencies=[Depends(auth.access_token_required)])
def get_expense_by_id(id: int, request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("my-access-token")
    if not access_token:
        raise NoAccessTokenFound()
    logger.debug(f"Get data of expense with id={id}")
    expense = db.query(Transaction).filter(Transaction.id == id).first()
    return expense


@router.patch("/expenses/{id}", dependencies=[Depends(auth.access_token_required)])
def add_expenses(id: int):
    return {f"Add expense for {id}": "OK"}


@router.delete("/expenses/{id}", dependencies=[Depends(auth.access_token_required)])
def delete_expenses(id: int, request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("my-access-token")
    if not access_token:
        raise NoAccessTokenFound()
    logger.debug(f"Delete expense with id={id}")
    expense = db.query(Transaction).filter(Transaction.id == id).first()
    db.delete(expense)
    db.commit()
    return {f"Delete expense for {id}": "OK"}
