from datetime import datetime, timedelta
from models import User, Subscription
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_


# Всі досягнення
ACHIEVEMENTS = {
    # Аналізи
    "first_analysis": {
        "title": "Перший аналіз 🔍",
        "desc": "Зробив перший аналіз переписки",
        "bonus": {"analyses": 1}
    },
    "analyses_5": {
        "title": "5 аналізів 📊",
        "desc": "Зробив 5 аналізів переписки",
        "bonus": {"analyses": 2}
    },
    "analyses_10": {
        "title": "Детектив 🕵️",
        "desc": "Зробив 10 аналізів переписки",
        "bonus": {"analyses": 3}
    },
    "analyses_25": {
        "title": "Профі 💼",
        "desc": "Зробив 25 аналізів переписки",
        "bonus": {"analyses": 5}
    },
    "analyses_50": {
        "title": "Легенда 👑",
        "desc": "Зробив 50 аналізів переписки",
        "bonus": {"premium_days": 3}
    },

    # Streak
    "streak_3": {
        "title": "3 дні поспіль 🔥",
        "desc": "Заходив 3 дні поспіль",
        "bonus": {"analyses": 2}
    },
    "streak_7": {
        "title": "Тижневий стрік 🔥🔥",
        "desc": "Заходив 7 днів поспіль",
        "bonus": {"analyses": 5}
    },
    "streak_14": {
        "title": "2 тижні поспіль 💪",
        "desc": "Заходив 14 днів поспіль",
        "bonus": {"premium_days": 7}
    },
    "streak_30": {
        "title": "Місяць поспіль 🏆",
        "desc": "Заходив 30 днів поспіль",
        "bonus": {"vip_days": 7}
    },

    # Редфлаги
    "first_redflag": {
        "title": "Перший редфлаг 🚩",
        "desc": "Знайшов перший редфлаг",
        "bonus": {"analyses": 1}
    },
    "redflags_10": {
        "title": "Детектор брехні 🎯",
        "desc": "Знайшов 10 редфлагів",
        "bonus": {"outfit": 2}
    },
    "redflags_25": {
        "title": "Психолог 🧠",
        "desc": "Знайшов 25 редфлагів",
        "bonus": {"analyses": 5}
    },

    # Чат
    "first_message": {
        "title": "Перша розмова 💬",
        "desc": "Відправив перше повідомлення в чаті",
        "bonus": {"analyses": 1}
    },
    "messages_10": {
        "title": "Балакун 🗣️",
        "desc": "Відправив 10 повідомлень в чаті",
        "bonus": {"outfit": 2}
    },
}


async def give_bonus(user: User, bonus: dict, db: AsyncSession):
    """Видає бонус юзеру"""
    if "analyses" in bonus:
        user.bonus_analyses = (user.bonus_analyses or 0) + bonus["analyses"]

    if "outfit" in bonus:
        user.bonus_outfit_analyses = (user.bonus_outfit_analyses or 0) + bonus["outfit"]

    if "premium_days" in bonus:
        user.is_premium = True
        sub = Subscription(
            user_id=user.id,
            status="active",
            started_at=datetime.now(),
            ends_at=datetime.now() + timedelta(days=bonus["premium_days"]),
            payment_type="achievement_love_pro"
        )
        db.add(sub)

    if "vip_days" in bonus:
        user.is_premium = True
        sub = Subscription(
            user_id=user.id,
            status="active",
            started_at=datetime.now(),
            ends_at=datetime.now() + timedelta(days=bonus["vip_days"]),
            payment_type="achievement_vip"
        )
        db.add(sub)


async def check_and_award(user: User, db: AsyncSession, bot=None) -> list:
    """Перевіряє і видає нові досягнення. Повертає список нових досягнень."""
    current = user.achievements or []
    new_achievements = []

    total = int(user.total_analyses or 0)
    flags = int(user.total_red_flags or 0)
    messages = int(user.total_messages or 0)
    streak = int(user.streak_days or 0)

    # Перевіряємо кожне досягнення
    to_check = {
        "first_analysis": total >= 1,
        "analyses_5": total >= 5,
        "analyses_10": total >= 10,
        "analyses_25": total >= 25,
        "analyses_50": total >= 50,
        "streak_3": streak >= 3,
        "streak_7": streak >= 7,
        "streak_14": streak >= 14,
        "streak_30": streak >= 30,
        "first_redflag": flags >= 1,
        "redflags_10": flags >= 10,
        "redflags_25": flags >= 25,
        "first_message": messages >= 1,
        "messages_10": messages >= 10,
    }

    for key, condition in to_check.items():
        if condition and key not in current:
            achievement = ACHIEVEMENTS[key]
            current.append(key)
            new_achievements.append(achievement)
            await give_bonus(user, achievement["bonus"], db)
            print(f"ACHIEVEMENT: {user.telegram_id} -> {key}")

            # Повідомляємо юзера в Telegram
            if bot:
                try:
                    bonus_text = _format_bonus(achievement["bonus"])
                    await bot.send_message(
                        chat_id=int(user.telegram_id),
                        text=(
                            f"🏆 Нове досягнення!\n\n"
                            f"{achievement['title']}\n"
                            f"{achievement['desc']}\n\n"
                            f"🎁 Нагорода: {bonus_text}"
                        )
                    )
                except Exception as e:
                    print(f"achievement notify error: {e}")

    user.achievements = current
    return new_achievements


def _format_bonus(bonus: dict) -> str:
    parts = []
    if "analyses" in bonus:
        parts.append(f"+{bonus['analyses']} аналізів")
    if "outfit" in bonus:
        parts.append(f"+{bonus['outfit']} спроби стиліста")
    if "premium_days" in bonus:
        parts.append(f"Love Pro на {bonus['premium_days']} днів 💜")
    if "vip_days" in bonus:
        parts.append(f"VIP на {bonus['vip_days']} днів 👑")
    return ", ".join(parts)


async def update_streak(user: User, db: AsyncSession):
    """Оновлює streak юзера"""
    now = datetime.now().date()
    last = user.streak_last_date

    # Обробляємо випадок коли в базі рядок 'NULL' замість None
    if last and str(last).upper() == 'NULL':
        last = None

    if last:
        try:
            last_date = last.date() if hasattr(last, 'date') else datetime.fromisoformat(str(last)).date()
            diff = (now - last_date).days

            if diff == 0:
                return
            elif diff == 1:
                user.streak_days = int(user.streak_days or 0) + 1
            else:
                user.streak_days = 1
        except Exception as e:
            print(f"streak parse error: {e}")
            user.streak_days = 1
    else:
        user.streak_days = 1

    user.streak_last_date = datetime.now()