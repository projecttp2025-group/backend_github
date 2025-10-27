import psycopg

from app.core.config import settings


def get_connection():
    return psycopg.connect(
        host=settings.db_host,
        port=int(settings.db_port),
        user=settings.db_user,
        password=settings.db_password,
        dbname=settings.db_name,
        connect_timeout=5,
    )
