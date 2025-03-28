from fastapi import FastAPI
from backend.database import engine, Base
from backend.handlers import git_summary_handler


import asyncio

app = FastAPI()

# DB Initialization on startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def read_root():
    return {"message": "FastAPI Backend is running!"}

app.include_router(git_summary_handler.router, prefix="/api")

@app.get("/analyze")
async def analyze_code():
    return {"status": "Analysis Started"}

# Run with: uvicorn main:app --reload
