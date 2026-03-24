import uuid

from app.database import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Float, ForeignKey, String, func, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Admin(Base):
    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(60), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship(
        "Organization",
        back_populates="admins"
    )

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    hourly_rate = Column(Float, nullable=True)
    email = Column(String(255), nullable=True)
    embedding = Column(Vector(512), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    attendance_logs = relationship(
        "AttendanceLog",
        back_populates="employee",
        cascade="all, delete-orphan"
    )
    organization = relationship(
        "Organization",
        back_populates="employees"
    )

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    default_open_time = Column(Time, nullable=True)
    default_close_time = Column(Time, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    employees = relationship(
        "Employee",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    admins = relationship(
        "Admin",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(
        Enum(
            "IN",
            "OUT",
            name="action_type",
            schema="public",
            create_type=False,
        ),
        nullable=False,
    )
    timestamp = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    employee = relationship("Employee", back_populates="attendance_logs")

class PayrollSession(Base):
    __tablename__ = "payroll_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shift_date = Column(Date, nullable=False)
    clock_in_time = Column(TIMESTAMP(timezone=True), nullable=False)
    clock_out_time = Column(TIMESTAMP(timezone=True), nullable=False)
    total_hours = Column(Float, nullable=False)
    total_pay = Column(Float, nullable=False)
    requires_admin_review = Column(Boolean, nullable=False, server_default="false")

    employee = relationship("Employee", back_populates="payroll_sessions")
