import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://placeholder.com")

@dp.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    referral_code = args[1] if len(args) > 1 else None

    user = message.from_user

    # Формуємо URL з реферальним кодом якщо є
    webapp_url = WEBAPP_URL
    if referral_code:
        webapp_url = f"{WEBAPP_URL}?ref={referral_code}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔍 Відкрити RedFlag AI",
                web_app=WebAppInfo(url=webapp_url)
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Запросити друга",
                callback_data="get_referral"
            )
        ]
    ])

    await message.answer(
        f"Привіт, {user.first_name}! 👋\n\n"
        f"Я RedFlag AI — твій особистий радник у спілкуванні та стосунках.\n\n"
        f"Що вмію:\n"
        f"🔍 Аналізую переписки\n"
        f"✍️ Генерую відповіді у твоєму стилі\n"
        f"👗 Оцінюю образи\n"
        f"💬 Спілкуюся як друг, психолог або коуч\n\n"
        f"Натисни кнопку щоб почати 👇",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "get_referral")
async def get_referral(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)

    import hashlib
    referral_code = hashlib.md5(user_id.encode()).hexdigest()[:8].upper()
    referral_link = f"https://t.me/ai_redflag_bot?start={referral_code}"

    await callback.message.answer(
        f"🔗 Твоє реферальне посилання:\n\n"
        f"`{referral_link}`\n\n"
        f"Запроси 2 друзів — отримай +3 безкоштовних аналізи! 🎁\n\n"
        f"Просто скинь це посилання другу 👆",
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    logger.info("🤖 Бот запущено")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
