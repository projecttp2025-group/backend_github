import logging

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger("app.expenses")


@router.get("/expenses")
def get_expenses():
    return {"Expenses": "OK"}


@router.post("/expenses")
def create_expense():
    return {"Create expense": "OK"}


@router.get("/expenses/{id}")
def get_expense_by_id(id: int):
    return {f"Get expense for {id}": "OK"}


@router.patch("/expenses/{id}")
def add_expenses(id: int):
    return {f"Add expense for {id}": "OK"}


@router.delete("/expenses/{id}")
def delete_expenses(id: int):
    return {f"Delete expense for {id}": "OK"}
