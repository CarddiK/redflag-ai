from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import AsyncSessionLocal
from models import User, Subscription
from sqlalchemy import select
from datetime import datetime, timedelta
import hashlib
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()

PLANS = {
    "love_pro": {
        "title": "Love Pro 💜",
        "description": "50 аналізів на місяць, всі режими відповідей, картотека крашів",
        "stars": 100,
        "days": 30,
    },
    "vip": {
        "title": "VIP 👑",
        "description": "Безлімітні аналізи, всі функції, AI-Стиліст",
        "stars": 250,
        "days": 30,
    }
}

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://fluffy-macaron-7115dc.netlify.app")


async def apply_referral_reward(referrer: User, db):
    count = referrer.referral_count or 0
    print(f"REFERRAL REWARD CHECK: count={count} for user {referrer.telegram_id}")

    if count == 2:
        referrer.bonus_analyses = (referrer.bonus_analyses or 0) + 10
        print(f"REFERRAL REWARD: +10 analyses for {referrer.telegram_id}")

    elif count == 5:
        referrer.is_premium = True
        sub = Subscription(
            user_id=referrer.id,
            status="active",
            started_at=datetime.now(),
            ends_at=datetime.now() + timedelta(weeks=1),
            payment_type="referral_love_pro"
        )
        db.add(sub)
        print(f"REFERRAL REWARD: Love Pro 1 week for {referrer.telegram_id}")

    elif count == 10:
        referrer.is_premium = True
        sub = Subscription(
            user_id=referrer.id,
            status="active",
            started_at=datetime.now(),
            ends_at=datetime.now() + timedelta(weeks=2),
            payment_type="referral_vip"
        )
        db.add(sub)
        print(f"REFERRAL REWARD: VIP 2 weeks for {referrer.telegram_id}")


async def process_referral(new_telegram_id: str, ref_code: str, db):
    """Обробка реферального коду — викликається і з бота і з фронтенду"""
    ref_result = await db.execute(select(User).where(User.referral_code == ref_code))
    referrer = ref_result.scalar_one_or_none()

    if not referrer or referrer.telegram_id == new_telegram_id:
        return False

    # Перевіряємо чи цей юзер вже не був зарахований
    new_user_result = await db.execute(select(User).where(User.telegram_id == new_telegram_id))
    new_user = new_user_result.scalar_one_or_none()

    if new_user and new_user.referred_by:
        print(f"REFERRAL SKIP: {new_telegram_id} already has referrer")
        return False

    if new_user:
        new_user.referred_by = referrer.id

    referrer.referral_count = (referrer.referral_count or 0) + 1
    await apply_referral_reward(referrer, db)
    print(f"REFERRAL OK: {new_telegram_id} -> {referrer.telegram_id}, count={referrer.referral_count}")
    return True


@dp.message(CommandStart())
async def start(message: Message):
    args = message.text.split()
    param = args[1] if len(args) > 1 else None
    print(f"START: user={message.from_user.id} param={param}")

    # Якщо це команда купівлі
    if param and param.startswith("buy_"):
        plan_id = param.replace("buy_", "")
        plan = PLANS.get(plan_id)
        if plan:
            await bot.send_invoice(
                chat_id=message.from_user.id,
                title=plan["title"],
                description=plan["description"],
                payload=f"{plan_id}:{message.from_user.id}",
                currency="XTR",
                prices=[LabeledPrice(label=plan["title"], amount=plan["stars"])],
            )
            return

    ref_code = param if param and not param.startswith("buy_") else None

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == str(message.from_user.id)))
        user = result.scalar_one_or_none()

        if not user:
            # Новий юзер — створюємо
            user = User(
                telegram_id=str(message.from_user.id),
                username=message.from_user.username,
                referral_code=hashlib.md5(str(message.from_user.id).encode()).hexdigest()[:8].upper()
            )
            db.add(user)
            await db.flush()

            if ref_code:
                await process_referral(str(message.from_user.id), ref_code, db)

            await db.commit()

        else:
            # Юзер існує — додаємо реферал якщо ще не було
            if ref_code and not user.referred_by:
                await process_referral(str(message.from_user.id), ref_code, db)
                await db.commit()

    # Передаємо реферальний код в URL Mini App щоб фронтенд теж міг зарахувати
    webapp_url = f"{WEBAPP_URL}?ref={ref_code}" if ref_code else WEBAPP_URL

    builder = InlineKeyboardBuilder()
    builder.button(text="🚩 Відкрити RedFlag AI", web_app={"url": webapp_url})
    builder.adjust(1)

    await message.answer(
        "👋 Привіт! Я RedFlag AI — твій особистий радник у стосунках.\n\n"
        "🔍 Аналізую переписки\n"
        "💬 Генерую відповіді\n"
        "💘 Веду картотеку крашів\n\n"
        "Натисни кнопку щоб відкрити додаток 👇",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("buy_"))
async def buy_plan(callback: CallbackQuery):
    plan_id = callback.data.replace("buy_", "")
    plan = PLANS.get(plan_id)
    if not plan:
        return
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=plan["title"],
        description=plan["description"],
        payload=f"{plan_id}:{callback.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"], amount=plan["stars"])],
    )
    await callback.answer()


@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    print(f"PRE CHECKOUT: {pre_checkout_query.id}")
    await pre_checkout_query.answer(ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    print(f"SUCCESSFUL PAYMENT: {message.successful_payment}")
    payload = message.successful_payment.invoice_payload
    plan_id, telegram_id = payload.split(":")

    plan = PLANS.get(plan_id)
    if not plan:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if user:
            user.is_premium = True
            sub = Subscription(
                user_id=user.id,
                status="active",
                started_at=datetime.now(),
                ends_at=datetime.now() + timedelta(days=plan["days"]),
                payment_type=f"stars_{plan_id}"
            )
            db.add(sub)
            await db.commit()

    await message.answer(
        f"🎉 Оплата успішна!\n\n"
        f"✅ {plan['title']} активовано на 30 днів\n\n"
        f"Відкрий додаток і користуйся всіма можливостями! 🚀"
    )


@dp.callback_query(F.data == "get_referral")
async def get_referral(callback: CallbackQuery):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == str(callback.from_user.id)))
        user = result.scalar_one_or_none()
        if user:
            link = f"https://t.me/flagai_bot?start={user.referral_code}"
            await callback.message.answer(f"🔗 Твоє реферальне посилання:\n{link}")
    await callback.answer()


async def start_bot():
    await dp.start_polling(bot)
