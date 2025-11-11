from app.core.config import settings
from sqlalchemy import create_engine


url = settings.database_url
database_engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else None)
