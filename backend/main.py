from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routes import users, analyze, generate
import os

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://redflag-ai-production.up.railway.app{WEBHOOK_PATH}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✅ База даних підключена і таблиці створені")
    
    # Встановлюємо webhook
    from bot import bot, dp
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook встановлено: {WEBHOOK_URL}")
    yield
    
    # Видаляємо webhook при зупинці
    await bot.delete_webhook()

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

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    from aiogram.types import Update
    from bot import dp, bot
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
