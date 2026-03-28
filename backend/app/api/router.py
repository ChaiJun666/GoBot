from fastapi import APIRouter

from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.health import router as health_router
from app.api.routes.linkedin import router as linkedin_router
from app.api.routes.llm import router as llm_router
from app.api.routes.mail import router as mail_router
from app.api.routes.scrape_jobs import router as scrape_jobs_router
from app.api.routes.sites import router as sites_router

api_router = APIRouter()
api_router.include_router(campaigns_router)
api_router.include_router(health_router)
api_router.include_router(linkedin_router)
api_router.include_router(llm_router)
api_router.include_router(mail_router)
api_router.include_router(scrape_jobs_router)
api_router.include_router(sites_router)
