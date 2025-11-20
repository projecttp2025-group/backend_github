from fastapi import HTTPException, status

class NoRequestCodeSend(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=message)


InvalidCredentials = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")

class AccountNotFound(HTTPException):
    def __init__(self, message: str = "Account not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


NoAccessTokenFound = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access token found in cookie")