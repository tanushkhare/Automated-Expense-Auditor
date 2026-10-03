from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.expenses import router as expenses_router
from backend.app.api.policy_rules import router as policy_rules_router
from backend.app.api.reports import router as reports_router
from backend.app.api.auth import router as auth_router
from backend.app.core.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Automated Expense Auditor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expenses_router, prefix="/api/v1")
app.include_router(policy_rules_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Automated Expense Auditor API"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
