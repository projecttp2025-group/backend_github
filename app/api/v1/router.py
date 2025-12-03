from fastapi import APIRouter

from . import advice, analytics, auth, categories, expenses, health, receipts, chat

api_router = APIRouter()


api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(expenses.router, tags=["expenses"])
api_router.include_router(receipts.router, tags=["receipts"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(categories.router, tags=["categories"])
api_router.include_router(advice.router, tags=["advice"])
api_router.include_router(chat.router, tags=["chat"])
