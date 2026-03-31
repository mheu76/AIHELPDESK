"""
SQLAlchemy base configuration.
Import all models here for Alembic to detect them.
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


# Import all models here for Alembic
# This ensures all models are registered before creating migrations
def import_models():
    """Import all models for Alembic discovery"""
    # Will import models when they are created
    # from app.models import user  # noqa: F401
    # from app.models import chat  # noqa: F401
    # from app.models import ticket  # noqa: F401
    pass
