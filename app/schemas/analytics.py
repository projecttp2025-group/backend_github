from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TimeSeriesDataPoint(BaseModel):
    date: datetime
    amount: Decimal


class TimeSeriesResponse(BaseModel):
    total_amount: Decimal
    average_per_day: Decimal
    data_points: list[TimeSeriesDataPoint]


class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    category_type: str
    total_amount: Decimal
    transaction_count: int
    percentage: Decimal


class TimeSeriesByCategoryResponse(BaseModel):
    total_amount: Decimal
    categories: list[CategorySummary]


class MonthlyStats(BaseModel):
    year: int
    month: int
    total_expenses: Decimal
    total_income: Decimal
    net: Decimal
    transaction_count: int
