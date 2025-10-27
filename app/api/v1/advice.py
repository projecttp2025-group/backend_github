import logging

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger("app.advice")


@router.get("/advice")
def get_timeserie():
    logger.debug("Advice endpoint activated")
    return {"Advice": "OK"}
