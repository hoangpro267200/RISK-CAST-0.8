from typing import Generator
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """Provide a DB session placeholder."""
    yield None

