from fastapi import FastAPI

from .routes import auth, employees

app = FastAPI(root_path="/api")
app.include_router(auth.router)
app.include_router(employees.router)

# Health check endpoint
@app.get("/")
async def root():
    return {"success": True, "data": {"info": "ClockGuard Auth API"}, "message": "Service healthy"}