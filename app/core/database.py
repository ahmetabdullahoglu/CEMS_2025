from contextlib import contextmanager
from typing import Generator

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Database session context manager for transactions
    
    Usage:
        with get_db_context() as db:
            transaction = create_income_transaction(db, ...)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()