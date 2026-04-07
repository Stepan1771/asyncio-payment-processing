from sqlalchemy import (
    JSON,
    String,
    Boolean,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .base import Base
from .mixins import (
    IdMixin,
    UidMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
)


class Outbox(Base, IdMixin, UidMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "outbox_events"

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
