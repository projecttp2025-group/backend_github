from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import date, datetime
from decimal import Decimal

class ExpenseCreate(BaseModel):
    category_name : Optional[str] = None
    type: Literal['Расход', 'Доход'] = 'Расход'
    amount : Decimal = Field(gt=0, max_digits=7, decimal_places=2)
    date : date
    description : Optional[str] = Field(default=None, max_length=512)

class ExpenseUpdate(BaseModel):
    account_id : int
    category_id : Optional[int] = None
    amount : Decimal = Field(gt=0, max_digits=7, decimal_places=2)
    date : date
    description : Optional[str] = Field(default=None, max_length=512)

class ExpenseRead(BaseModel):
    id : int
    user_id : int
    account_id : int
    category_id : Optional[int]
    amount : Decimal
    date : date
    description : Optional[str]
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)

class ExpenseList(BaseModel):
    total : Decimal
    items : list[ExpenseRead]