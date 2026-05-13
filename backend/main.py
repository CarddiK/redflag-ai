from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db, AsyncSessionLocal
from routes import users, analyze, generate, stats
from sqlalchemy import select, and_
from datetime import datetime, timedelta
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
                result = await db.execute(select(User).where(User.is_premium == True))
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

        await asyncio.sleep(60 * 60 * 24)


async def notify_analyses_reset():
    """Щопонеділка повідомляє юзерів що аналізи поновились"""
    while True:
        try:
            now = datetime.now()
            # Чекаємо до понеділка 10:00
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= 10:
                days_until_monday = 7
            next_monday = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
            wait_seconds = (next_monday - now).total_seconds()
            await asyncio.sleep(wait_seconds)

            from bot import bot
            async with AsyncSessionLocal() as db:
                from models import User
                # Тільки фрі юзери які робили аналізи
                result = await db.execute(
                    select(User).where(
                        and_(
                            User.is_premium == False,
                            User.free_analyses_used > 0
                        )
                    )
                )
                users = result.scalars().all()

                for user in users:
                    try:
                        await bot.send_message(
                            chat_id=int(user.telegram_id),
                            text=(
                                "🔄 Твої безкоштовні аналізи поновились!\n\n"
                                "У тебе знову є 5 аналізів на цьому тижні.\n"
                                "Є кому написав — саме час перевірити 👀"
                            )
                        )
                        await asyncio.sleep(0.05)  # щоб не спамити Telegram API
                    except Exception as e:
                        print(f"notify_reset error for {user.telegram_id}: {e}")

        except Exception as e:
            print(f"notify_analyses_reset error: {e}")
            await asyncio.sleep(60 * 60)


async def notify_inactive_users():
    """Щодня перевіряє юзерів які не заходили 3 дні"""
    while True:
        try:
            await asyncio.sleep(60 * 60 * 24)  # раз на добу

            from bot import bot
            async with AsyncSessionLocal() as db:
                from models import User, Analysis
                three_days_ago = datetime.now() - timedelta(days=3)
                seven_days_ago = datetime.now() - timedelta(days=7)

                # Юзери у яких останній аналіз був 3 дні тому
                result = await db.execute(select(User))
                all_users = result.scalars().all()

                for user in all_users:
                    try:
                        # Знаходимо останній аналіз
                        last_analysis = await db.execute(
                            select(Analysis)
                            .where(Analysis.user_id == user.id)
                            .order_by(Analysis.created_at.desc())
                            .limit(1)
                        )
                        last = last_analysis.scalars().first()

                        if not last:
                            continue

                        last_date = last.created_at
                        if not last_date:
                            continue

                        # Якщо останній аналіз був рівно 3 дні тому (±12 годин)
                        diff = datetime.now() - last_date
                        if timedelta(days=2, hours=12) <= diff <= timedelta(days=3, hours=12):
                            await bot.send_message(
                                chat_id=int(user.telegram_id),
                                text=(
                                    "👀 Давно не бачились!\n\n"
                                    "Поки тебе не було — може хтось написав?\n"
                                    "Кинь скріншот і подивимось що до чого 🔍"
                                )
                            )
                            await asyncio.sleep(0.05)

                    except Exception as e:
                        print(f"notify_inactive error for {user.telegram_id}: {e}")

        except Exception as e:
            print(f"notify_inactive_users error: {e}")
            await asyncio.sleep(60 * 60)


async def notify_subscription_expiring():
    """Щодня перевіряє підписки які закінчуються через 3 дні"""
    while True:
        try:
            await asyncio.sleep(60 * 60 * 24)  # раз на добу

            from bot import bot
            async with AsyncSessionLocal() as db:
                from models import User, Subscription

                in_three_days = datetime.now() + timedelta(days=3)
                in_four_days = datetime.now() + timedelta(days=4)

                result = await db.execute(
                    select(Subscription).where(
                        and_(
                            Subscription.status == "active",
                            Subscription.ends_at >= in_three_days,
                            Subscription.ends_at < in_four_days
                        )
                    )
                )
                expiring_subs = result.scalars().all()

                for sub in expiring_subs:
                    try:
                        user_result = await db.execute(
                            select(User).where(User.id == sub.user_id)
                        )
                        user = user_result.scalar_one_or_none()
                        if not user:
                            continue

                        plan_name = "VIP 👑" if "vip" in (sub.payment_type or "") else "Love Pro 💜"

                        await bot.send_message(
                            chat_id=int(user.telegram_id),
                            text=(
                                f"⏰ Твоя підписка {plan_name} закінчується через 3 дні!\n\n"
                                f"Щоб не втратити доступ до всіх функцій — продовж підписку.\n\n"
                                f"Відкрий додаток і переходь в розділ Premium 💎"
                            )
                        )
                        await asyncio.sleep(0.05)

                    except Exception as e:
                        print(f"notify_expiring error for sub {sub.id}: {e}")

        except Exception as e:
            print(f"notify_subscription_expiring error: {e}")
            await asyncio.sleep(60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✅ База даних підключена і таблиці створені")

    from bot import bot
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    print(f"✅ Webhook встановлено: {WEBHOOK_URL}")

    task1 = asyncio.create_task(check_expired_subscriptions())
    task2 = asyncio.create_task(notify_analyses_reset())
    task3 = asyncio.create_task(notify_inactive_users())
    task4 = asyncio.create_task(notify_subscription_expiring())
    print("✅ Всі планувальники запущено")

    yield

    task1.cancel()
    task2.cancel()
    task3.cancel()
    task4.cancel()


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
