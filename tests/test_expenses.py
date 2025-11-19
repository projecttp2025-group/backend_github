import os
import sqlite3
import sys
from pathlib import Path
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request


_env_defaults = {
    "app_env": "test",
    "app_port": "8000",
    "db_host": "localhost",
    "db_user": "user",
    "db_password": "password",
    "db_name": "test_db",
    "db_port": "5432",
    "database_url": "sqlite:///./test.db",
    "smtp_login": "smtp@example.com",
    "smtp_password": "smtp-password",
}
for key, value in _env_defaults.items():
    os.environ.setdefault(key, value)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.v1 import expenses as expenses_module  
from app.db.models import Account, Base, Category, Transaction, User  
from app.schemas.expense import ExpenseCreate 

sqlite3.register_adapter(Decimal, lambda value: float(value))


engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def db_session() -> Session:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _create_user_with_relations(session: Session):
    user = User(email="user@example.com", password_hash="hash")
    account = Account(name="Main account", currency="USD", user=user)
    category = Category(name="Groceries", type="expense", user=user)
    session.add_all([user, account, category])
    session.commit()
    session.refresh(user)
    session.refresh(account)
    session.refresh(category)
    return user, account, category


def _create_transaction(session: Session, user: User, account: Account, category: Category, amount: int):
    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        amount=amount,
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        description="Seed transaction",
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def _build_request(cookie_value: str | None = None) -> Request:
    headers = []
    if cookie_value is not None:
        headers.append((b"cookie", f"my-access-token={cookie_value}".encode()))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/expenses",
        "raw_path": b"/api/v1/expenses",
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 5000),
        "server": ("testserver", 80),
    }

    async def receive():
        return {"type": "http.request"}

    return Request(scope, receive)


def test_get_expenses_returns_items_and_total(db_session: Session):
    user, account, category = _create_user_with_relations(db_session)
    _create_transaction(db_session, user, account, category, amount=100)
    _create_transaction(db_session, user, account, category, amount=250)

    result = expenses_module.get_expenses(account_name=account.name, db=db_session)

    assert Decimal(result.total) == Decimal("350")
    assert len(result.items) == 2
    assert result.items[0].account_id == account.id


def test_get_expenses_missing_account_returns_404(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        expenses_module.get_expenses(account_name="unknown", db=db_session)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Account not found"


def test_create_expense_persists_transaction(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    user, account, category = _create_user_with_relations(db_session)

    def fake_decode(token, secret, algorithms, options):
        assert token == "valid-token"
        return {"type": "access", "sub": user.email}

    monkeypatch.setattr(expenses_module.jwt, "decode", fake_decode)
    request = _build_request("valid-token")

    body = ExpenseCreate(
        category_name=category.name,
        amount=Decimal("120"),
        date=date.today(),
        description="Dinner",
    )

    response = expenses_module.create_expense(body=body, request=request, db=db_session)

    assert response == {"Create expense": "OK"}

    transactions = db_session.query(Transaction).all()
    assert len(transactions) == 1
    assert transactions[0].description == "Dinner"
    assert transactions[0].amount == 120


def test_create_expense_without_token_returns_401(db_session: Session):
    user, account, category = _create_user_with_relations(db_session)
    body = ExpenseCreate(
        category_name=category.name,
        amount=Decimal("50"),
        date=date.today(),
        description="Fuel",
    )
    request = _build_request(None)

    with pytest.raises(HTTPException) as exc:
        expenses_module.create_expense(body=body, request=request, db=db_session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "No access token found in cookie"
    assert db_session.query(Transaction).count() == 0


def test_get_expense_by_id_returns_single_transaction(db_session: Session):
    user, account, category = _create_user_with_relations(db_session)
    transaction = _create_transaction(db_session, user, account, category, amount=75)

    result = expenses_module.get_expense_by_id(id=transaction.id, db=db_session)

    assert result.id == transaction.id
    assert result.amount == 75


def test_delete_expense_removes_record(db_session: Session):
    user, account, category = _create_user_with_relations(db_session)
    transaction = _create_transaction(db_session, user, account, category, amount=40)

    response = expenses_module.delete_expenses(id=transaction.id, db=db_session)

    assert response == {f"Delete expense for {transaction.id}": "OK"}
    assert db_session.query(Transaction).count() == 0

