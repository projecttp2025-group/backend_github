import logging

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger("app.categories")


@router.get("/categories")
def get_statistic():
    logger.debug("Categories endpoint activated")
    return {"Categories": "OK"}
