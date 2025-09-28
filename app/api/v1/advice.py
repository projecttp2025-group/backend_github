from fastapi import APIRouter

router = APIRouter()


@router.get("/advice")
def get_timeserie():
    return {"Advice" : "OK"}
