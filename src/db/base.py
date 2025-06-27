from __future__ import annotations

from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """
    Base class for SQLAlchemy models with automatic table name generation.

    Attributes:
        id: Primary key of the model
        __name__: Name of the class (used for table name generation)
    """
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.

        Returns:
            str: Lowercase class name as table name
        """
        return cls.__name__.lower()
