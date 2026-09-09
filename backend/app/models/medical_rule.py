import uuid
from typing import List, Optional
from sqlalchemy import String, Numeric, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import MedicalCondition, RuleOperator, RuleScope

class MedicalRule(UUIDMixin, Base):
    __tablename__ = "medical_rules"

    condition: Mapped[MedicalCondition] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String(100), default="requires_manual_review")
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    constraints: Mapped[List["MedicalRuleConstraint"]] = relationship(back_populates="rule", cascade="all, delete-orphan")

class MedicalRuleConstraint(UUIDMixin, Base):
    __tablename__ = "medical_rule_constraints"

    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medical_rules.id", ondelete="CASCADE"))
    nutrient: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    operator: Mapped[Optional[RuleOperator]] = mapped_column(nullable=True)
    value: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    scope: Mapped[Optional[RuleScope]] = mapped_column(nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    rule: Mapped["MedicalRule"] = relationship(back_populates="constraints")
