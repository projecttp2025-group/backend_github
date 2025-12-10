import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.core.jwt import auth
from app.db.database import get_db
from app.db.models import Transaction, User, Category
from app.schemas.category import CategoriesStatsResponse, CategoryStatistic
from app.api.exceptions import NoAccessTokenFound

router = APIRouter()
logger = logging.getLogger("app.categories")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Получить текущего пользователя из JWT токена"""
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
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    return user


@router.get("/categories", dependencies=[Depends(auth.access_token_required)])
def get_statistic( request: Request, db: Session = Depends(get_db), category_type: Optional[str] = Query(None)):
    """
    Получить статистику по всем категориям пользователя (Доходы, Расходы).
    """

    user = get_current_user(request, db)
    logger.debug(f"Categories endpoint activated for user {user.email}")
    
    query = db.query(Transaction).filter(Transaction.user_id == user.id)
    transactions = query.all()
    
    total_expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Category.type == "Расход"
    ).join(Category, Transaction.category_id == Category.id).scalar() or 0
    
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Category.type == "Доход"
    ).join(Category, Transaction.category_id == Category.id).scalar() or 0
    

    category_stats = {}
    for transaction in transactions:
        cat_id = transaction.category_id
        cat_type = transaction.category.type
        
        if category_type and cat_type != category_type:
            continue
        
        if cat_id not in category_stats:
            category_stats[cat_id] = {
                "category_id": cat_id,
                "category_name": transaction.category.name,
                "category_type": cat_type,
                "amount": 0,
                "count": 0
            }
        category_stats[cat_id]["amount"] += transaction.amount
        category_stats[cat_id]["count"] += 1
    
    total_filtered = total_expenses if category_type == "Расход" else (
        total_income if category_type == "Доход" else (total_expenses + total_income)
    )
    
    categories = []
    for cat_data in category_stats.values():
        percentage = (cat_data["amount"] / total_filtered * 100) if total_filtered != 0 else 0
        categories.append(CategoryStatistic(
            category_id=cat_data["category_id"],
            category_name=cat_data["category_name"],
            category_type=cat_data["category_type"],
            total_amount=cat_data["amount"],
            transaction_count=cat_data["count"],
            percentage=percentage
        ))
    
    categories.sort(key=lambda x: x.total_amount, reverse=True)
    
    return CategoriesStatsResponse(
        total_expenses=total_expenses,
        total_income=total_income,
        categories=categories
    )
