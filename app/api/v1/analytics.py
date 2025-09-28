from fastapi import APIRouter

router = APIRouter()


@router.get("/analytics/timeseries")
def get_timeserie():
    return {"Timeseries" : "OK"}


@router.get("/analytics/by-category")
def get_timeserie_by_category():
    return {"By-category" : "OK"}
