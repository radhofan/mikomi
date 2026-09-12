from fastapi import FastAPI

from api.routes.dashboard import router as dashboard_router
from api.routes.dedup import router as dedup_router
from api.routes.leads import router as leads_router
from api.routes.source_extract import router as source_extract_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI-Assisted Mini Lead Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router)
app.include_router(dedup_router)
app.include_router(source_extract_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "lead-management-api"}
