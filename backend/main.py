from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import engine, Base
from routes import users, analyze, generate
import os

load_dotenv()

app = FastAPI(title="RedFlag AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(analyze.router)
app.include_router(generate.router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База даних підключена і таблиці створені")

@app.get("/")
async def root():
    return {"status": "ok", "message": "RedFlag AI Backend is running"}
