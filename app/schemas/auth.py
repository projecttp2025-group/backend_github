from pydantic import BaseModel, EmailStr, Field, SecretStr


class EmailIn(BaseModel):
    email: EmailStr


class RequestCodeOut(BaseModel):
    ok: bool = True


class CodeVerifyIn(BaseModel):
    email: EmailStr
    code: str = Field(..., pattern=r"^\d{6}$")


class CodeVerifyOut(BaseModel):
    verified: bool


class SetPasswordIn(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: SecretStr


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str
