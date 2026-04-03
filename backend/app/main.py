from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.scheduler import start_scheduler, stop_scheduler
from contextlib import asynccontextmanager
from app.websockets import ws_router

from .routes import auth, employees, organization, payroll, attendance
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()

app = FastAPI(root_path="/api", lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(organization.router)
app.include_router(payroll.router)
app.include_router(attendance.router)
app.include_router(ws_router.router)

# Health check endpoint
@app.get("/")
async def root():
    return {"success": True, "data": {"info": "ClockGuard Auth API"}, "message": "Service healthy"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)