from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routes import users, analyze, generate
import asyncio
import threading
import os

def run_bot():
    import asyncio
    from bot import start_bot
    asyncio.run(start_bot())

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✅ База даних підключена і таблиці створені")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    yield

app = FastAPI(title="RedFlag AI Backend", version="0.1.0", lifespan=lifespan)

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
