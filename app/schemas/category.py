from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal


class CategoryStatistic(BaseModel):
    category_id: int
    category_name: str
    category_type: str
    transaction_count: int
    total_amount: Decimal
    percentage: Decimal

    model_config = ConfigDict(from_attributes=True)


class CategoriesStatsResponse(BaseModel):
    total_expenses: Decimal
    total_income: Decimal
    categories: list[CategoryStatistic]
