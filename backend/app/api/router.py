from fastapi import APIRouter
from app.api.routes import health, auth, users, jobs
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(jobs.router)
