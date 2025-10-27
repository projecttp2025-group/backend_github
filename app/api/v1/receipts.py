import logging

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger("app.receipts")


@router.post("/receipts")
def add_receipt():
    logger.debug("Receipts endpoint activated")
    return {"Receipt": "OK"}
