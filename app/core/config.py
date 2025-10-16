from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env"
    )

    app_env : str
    app_port : str

    db_host : str
    db_user : str
    db_password : str
    db_name : str 
    db_port : str 

    jwt_secret: str = "dev_change_me"
    jwt_alg: str = "HS256"
    access_token_expire_min: int = 30
    refresh_token_expire_days: int = 14

    smtp_login : str
    smtp_password : str

settings = Settings()
