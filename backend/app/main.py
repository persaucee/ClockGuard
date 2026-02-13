from fastapi import FastAPI

from .routes import auth

app = FastAPI(root_path="/api")
app.include_router(auth.router)

# Health check endpoint
@app.get("/")
async def root():
    return {"success": True, "data": {"info": "ClockGuard Auth API"}, "message": "Service healthy"}