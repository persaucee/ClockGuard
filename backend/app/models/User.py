import uuid

from app.database import Base
from sqlalchemy import TIMESTAMP, Column, String, func, Float
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID


class Admin(Base):
    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(60), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    hourly_rate = Column(Float, nullable=True)
    email = Column(String(255), nullable=True)
    embedding = Column(Vector(512))
    created_at = Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)