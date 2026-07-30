from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = "sqlite:///./complaints.db"


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.
    """

    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Create one database session for each API request.

    The session is automatically closed after the request finishes.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()