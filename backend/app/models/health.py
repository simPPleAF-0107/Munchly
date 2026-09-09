import uuid
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import MedicalCondition

class UserHealthCondition(UUIDMixin, Base):
    __tablename__ = "user_health_conditions"
    __table_args__ = (
        UniqueConstraint("user_id", "condition", name="uq_user_health_condition"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    condition: Mapped[MedicalCondition]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="health_conditions")
