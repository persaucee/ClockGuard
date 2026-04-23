import os

from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DB_URL = os.getenv("DB_URL")



# Async DB Setup (sets up connection pooling and async session management)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


async_engine = create_async_engine(
    DB_URL,
    pool_size=8,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine)
Base = declarative_base()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)