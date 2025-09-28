from fastapi import APIRouter

router = APIRouter()

@router.post("/receipts")
def add_receipt():
    return {"Receipt" : "OK"}