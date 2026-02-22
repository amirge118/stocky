
from app.core.database import get_db

# Re-export common dependencies
__all__ = ["get_db_session"]

get_db_session = get_db
