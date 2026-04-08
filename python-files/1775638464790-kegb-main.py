from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.database import engine, Base
from routers import auth, ouvrages, evaluations, maintenance, planning, priorisation, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="ICS ADE Pro API",
    description="API de gestion patrimoniale — Algérienne des Eaux",
    version="5.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/api/auth",         tags=["Authentification"])
app.include_router(ouvrages.router,     prefix="/api/ouvrages",     tags=["Ouvrages"])
app.include_router(evaluations.router,  prefix="/api/evaluations",  tags=["Évaluations ICS"])
app.include_router(maintenance.router,  prefix="/api/maintenance",  tags=["Maintenance"])
app.include_router(planning.router,     prefix="/api/planning",     tags=["Planning"])
app.include_router(priorisation.router, prefix="/api/priorisation", tags=["Priorisation"])
app.include_router(dashboard.router,    prefix="/api/dashboard",    tags=["Dashboard"])

@app.get("/")
def root():
    return {"message": "ICS ADE Pro v5.1 — API opérationnelle", "status": "ok"}
