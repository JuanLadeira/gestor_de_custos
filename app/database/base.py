from datetime import datetime
from typing import Annotated

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Type annotations for common column types
intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[
    datetime, mapped_column(server_default=func.now(), nullable=False)
]
updated_at = Annotated[
    datetime,
    mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False),
]


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    id: Mapped[intpk]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
