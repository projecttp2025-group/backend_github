import logging
from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger("app.analytics")


@router.get("/analytics/timeseries")
def get_timeserie():
    logger.debug("Analytics/timeseries endpoint activated")
    return {"Timeseries" : "OK"}


@router.get("/analytics/by-category")
def get_timeserie_by_category():
    logger.debug("Analytics/by-category endpoint activated")
    return {"By-category" : "OK"}
