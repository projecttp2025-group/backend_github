import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.core.jwt import auth
from app.db.database import get_db
from app.db.models import Transaction, User, Category
from app.schemas.analytics import (
    TimeSeriesDataPoint,
    TimeSeriesResponse,
    CategorySummary,
    TimeSeriesByCategoryResponse
)
from app.api.exceptions import NoAccessTokenFound

router = APIRouter()
logger = logging.getLogger("app.analytics")


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


@router.get("/analytics/timeseries", dependencies=[Depends(auth.access_token_required)])
def get_timeserie(
    request: Request,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Начальная дата в формате ISO"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата в формате ISO")
):
    """
    Получить временной ряд расходов и доходов пользователя.
    """
    user = get_current_user(request, db)
    logger.debug(f"Analytics/timeseries endpoint activated for user {user.email}")
    
    query = db.query(Transaction).filter(Transaction.user_id == user.id)
    
    # Применяем фильтры по датам если указаны
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.order_by(Transaction.date).all()
    
    if not transactions:
        return TimeSeriesResponse(
            total_amount=0,
            average_per_day=0,
            data_points=[]
        )
    
    # Считаем общую сумму (expenses как отрицательные, income как положительные)
    total_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id
    )
    if start_date:
        total_result = total_result.filter(Transaction.date >= start_date)
    if end_date:
        total_result = total_result.filter(Transaction.date <= end_date)
    
    total_amount = total_result.scalar() or 0
    
    # Преобразуем в список точек данных
    data_points = [
        TimeSeriesDataPoint(date=t.date, amount=t.amount)
        for t in transactions
    ]
    
    # Считаем среднее по дням (количество уникальных дат)
    unique_dates = len(set(t.date.date() if t.date else None for t in transactions))
    average_per_day = total_amount / unique_dates if unique_dates > 0 else 0
    
    return TimeSeriesResponse(
        total_amount=total_amount,
        average_per_day=average_per_day,
        data_points=data_points
    )


@router.get("/analytics/by-category", dependencies=[Depends(auth.access_token_required)])
def get_timeserie_by_category(
    request: Request,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Начальная дата в формате ISO"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата в формате ISO")
):
    """
    Получить расходы/доходы разбитые по категориям.
    """
    user = get_current_user(request, db)
    logger.debug(f"Analytics/by-category endpoint activated for user {user.email}")
    
    query = db.query(Transaction).filter(Transaction.user_id == user.id)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.all()
    
    # Считаем общую сумму
    total_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id
    )
    if start_date:
        total_amount = total_amount.filter(Transaction.date >= start_date)
    if end_date:
        total_amount = total_amount.filter(Transaction.date <= end_date)
    
    total = total_amount.scalar() or 0
    
    # Группируем по категориям
    category_stats = {}
    for transaction in transactions:
        cat_id = transaction.category_id
        if cat_id not in category_stats:
            category_stats[cat_id] = {
                "category_id": cat_id,
                "category_name": transaction.category.name,
                "category_type": transaction.category.type,
                "amount": 0,
                "count": 0
            }
        category_stats[cat_id]["amount"] += transaction.amount
        category_stats[cat_id]["count"] += 1
    
    # Формируем список категорий с процентами
    categories = []
    for cat_data in category_stats.values():
        percentage = (cat_data["amount"] / total * 100) if total != 0 else 0
        categories.append(CategorySummary(
            category_id=cat_data["category_id"],
            category_name=cat_data["category_name"],
            category_type=cat_data["category_type"],
            total_amount=cat_data["amount"],
            transaction_count=cat_data["count"],
            percentage=percentage
        ))
    
    # Сортируем по сумме (убывание)
    categories.sort(key=lambda x: x.total_amount, reverse=True)
    
    return TimeSeriesByCategoryResponse(
        total_amount=total,
        categories=categories
    )
