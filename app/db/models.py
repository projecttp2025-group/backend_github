from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'main'}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    password_hash = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    is_admin = Column(Boolean, default=False)

    accounts = relationship('Account', back_populates='user')
    categories = relationship("Category", back_populates='user')
    receipts = relationship('Receipt', back_populates='user')
    transactions = relationship('Transaction', back_populates='user')
    refresh_tokens = relationship('RefreshToken', back_populates='user')

class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {'schema': 'main'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('main.users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    currency = Column(String, nullable=False, default="BYN")
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    user = relationship('User', back_populates='accounts')
    transactions = relationship('Transaction', back_populates='account')

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {'schema': 'main'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('main.users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    user = relationship('User', back_populates='categories')
    transactions = relationship('Transaction', back_populates='category')

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {'schema': 'main'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('main.users.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('main.accounts.id', ondelete='CASCADE'), nullable=False)
    category_id = Column(Integer, ForeignKey('main.categories.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Integer, nullable=False)
    date = Column(DateTime)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    receipts = relationship('Receipt', back_populates="transaction")
    user = relationship('User', back_populates='transactions')
    account = relationship('Account', back_populates='transactions')
    category = relationship('Category', back_populates='transactions')

class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = {'schema': 'main'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("main.users.id", ondelete='CASCADE'))
    transaction_id = Column(Integer, ForeignKey("main.transactions.id", ondelete='SET NULL'))
    file_path = Column(String, nullable=False, default=None)
    merchant_name = Column(String)
    total_amount = Column(Numeric(15, 2))
    transaction_date = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    user = relationship('User', back_populates='receipts')
    transaction = relationship('Transaction', back_populates='receipts')

class EmailCode(Base):
    __tablename__ = "email_codes"
    __table_args__ = {'schema': 'main'}   

    email = Column(String, primary_key=True, index=True)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts_left = Column(Integer, nullable=False, default=5)
    used = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {'schema': 'main'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('main.users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String, nullable=False)
    jti = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)

    user = relationship('User', back_populates='refresh_tokens')