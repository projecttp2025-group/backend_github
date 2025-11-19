from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


url = settings.database_url
database_engine = create_engine(url)

def get_db():
    db = Session(bind=database_engine)
    try:
        yield db
    finally:
        db.close()