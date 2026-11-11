from typing import Generator, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from wapang.database.settings import DB_SETTINGS


class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(
            DB_SETTINGS.url,
            pool_recycle=28000,
            pool_size=10,
            pool_pre_ping=True,
        )
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

database_manager = DatabaseManager()

def get_db_session() -> Generator[Session, Any, None]:
    session = database_manager.session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()