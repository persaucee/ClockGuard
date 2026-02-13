import os

from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")



# Async DB Setup (sets up connection pooling and async session management)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ASYNC_DB_URL = f"postgresql+psycopg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async_engine = create_async_engine(
    ASYNC_DB_URL,
    pool_size=8,
    max_overflow=5,
    pool_pre_ping=False,
    pool_recycle=300,
    echo=False,
    connect_args={
        "prepare_threshold": None
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine)
Base = declarative_base()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)