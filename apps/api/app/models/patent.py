from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Patent(Base):
    __tablename__ = "patents"
    __table_args__ = (
        Index("ix_patents_ipc_number", "ipc_number"),
        Index("ix_patents_register_status", "register_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    application_number_normalized: Mapped[str | None] = mapped_column(String(32), index=True)
    register_number: Mapped[str | None] = mapped_column(String(32), index=True)
    publication_number: Mapped[str | None] = mapped_column(String(32), index=True)
    open_number: Mapped[str | None] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    title_eng: Mapped[str | None] = mapped_column(String(500))
    abstract: Mapped[str | None] = mapped_column(Text)
    applicant_name: Mapped[str | None] = mapped_column(String(300), index=True)
    ipc_number: Mapped[str | None] = mapped_column(String(500))
    application_date: Mapped[str | None] = mapped_column(String(32))
    register_status: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="kipris")
    source_url: Mapped[str | None] = mapped_column(Text)
    fetch_status: Mapped[str] = mapped_column(String(50), nullable=False, default="fetched")
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    claims: Mapped[list["Claim"]] = relationship(
        back_populates="patent",
        cascade="all, delete-orphan",
    )


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (
        UniqueConstraint("patent_id", "claim_number", name="uq_claims_patent_claim_number"),
        Index("ix_claims_status", "status"),
        Index("ix_claims_is_independent", "is_independent"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patent_id: Mapped[int] = mapped_column(ForeignKey("patents.id", ondelete="CASCADE"), nullable=False)
    claim_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    is_independent: Mapped[bool | None] = mapped_column(Boolean)
    dependency_claim_numbers: Mapped[str | None] = mapped_column(String(200))
    source_endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    source_document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    parser_confidence: Mapped[float | None] = mapped_column(Float)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    patent: Mapped[Patent] = relationship(back_populates="claims")
    elements: Mapped[list["ClaimElement"]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
    )


class ClaimElement(Base):
    __tablename__ = "claim_elements"
    __table_args__ = (
        UniqueConstraint("claim_id", "element_order", name="uq_claim_elements_claim_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    element_order: Mapped[int] = mapped_column(Integer, nullable=False)
    element_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_span: Mapped[str | None] = mapped_column(Text)
    parser_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    claim: Mapped[Claim] = relationship(back_populates="elements")
