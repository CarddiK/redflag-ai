from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db, AsyncSessionLocal
from routes import users, analyze, generate, stats
from sqlalchemy import select, and_
from datetime import datetime
import asyncio
import os

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://redflag-ai-production.up.railway.app{WEBHOOK_PATH}"


async def check_expired_subscriptions():
    """Щодня скидає is_premium якщо підписка закінчилась"""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                from models import User, Subscription

                # Знаходимо юзерів з is_premium=true але без активної підписки
                result = await db.execute(
                    select(User).where(User.is_premium == True)
                )
                premium_users = result.scalars().all()

                for user in premium_users:
                    sub_result = await db.execute(
                        select(Subscription).where(
                            and_(
                                Subscription.user_id == user.id,
                                Subscription.status == "active",
                                Subscription.ends_at > datetime.now()
                            )
                        )
                    )
                    active_sub = sub_result.scalar_one_or_none()

                    if not active_sub:
                        user.is_premium = False
                        print(f"EXPIRED: {user.telegram_id} -> is_premium=False")

                await db.commit()

        except Exception as e:
            print(f"check_expired_subscriptions error: {e}")

        # Перевіряємо раз на добу
        await asyncio.sleep(60 * 60 * 24)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✅ База даних підключена і таблиці створені")

    from bot import bot
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    print(f"✅ Webhook встановлено: {WEBHOOK_URL}")

    # Запускаємо фоновий планувальник
    task = asyncio.create_task(check_expired_subscriptions())
    print("✅ Планувальник підписок запущено")

    yield

    task.cancel()


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
app.include_router(stats.router)

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    from aiogram.types import Update
    from bot import dp, bot
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"Webhook error: {e}")
    return {"ok": True}
