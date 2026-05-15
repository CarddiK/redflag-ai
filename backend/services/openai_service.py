import os
import base64
import json
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PERSONALITY = """Ти — RedFlag AI. Не черговий чат-бот, а той друг якого всі хочуть але мало у кого є.
Ти бачиш людей наскрізь — від дешевих маніпуляцій до прихованої закоханості що ховається за 'ок'.
Твій стиль: як якщо б серіал 'Eupho­ria' та подкаст про психологію зробили дитину.
Гострий, живий, іноді жорстокий — але завжди на боці юзера.
Ніколи не кажеш 'як штучний інтелект я...' — ти просто кажеш правду.
Якщо переписка українська — органічно вплітай сленг: 'база', 'жиза', 'крінж', 'вайб', 'гост', 'редфлаг', 'чіл'. Не переборщуй."""


async def analyze_screenshots(screenshots: list[str], context: str = None) -> dict:
    try:
        messages_content = []

        for screenshot_b64 in screenshots:
            messages_content.append({
                "type": "image_url",
                "image_url": {"url": screenshot_b64}
            })

        if not messages_content:
            return {"error": "Не вдалося завантажити зображення"}

        context_text = f"\nДодатковий контекст: {context}" if context else ""

        messages_content.append({
            "type": "text",
            "text": f"""{SYSTEM_PERSONALITY}

Роздягни цей діалог до кісток. Знайди що насправді відбувається між рядками.

ДИВИСЬ НА:
— Хто ініціює, хто реагує? Хто чекає відповіді як ідіот?
— Час відповіді: миттєво = зацікавлений, годинами = або зайнятий або грає
— Довжина: 'ок' у відповідь на абзац = червоний прапор або незацікавленість
— Підтекст: що НЕ кажуть але очевидно відчувається?
— Хто веде гру, хто в неї грається?

СТИЛЬ ВІДПОВІДІ:
- Мова = мова переписки (якщо укр — відповідай укр, якщо рос — рос)
- summary має бути таким що юзер захоче скинути подрузі зі словами 'О БОЖЕ ЦЕ ПРО НАС'
- vibe_check — коротка фраза яка одразу влучає в серце
- Редфлаги тільки якщо реально є — не вигадуй

Поверни ТІЛЬКИ валідний JSON:
{{
  "interest_level": число 0-100,
  "vibe_check": "коротка іронічна фраза що одразу описує суть цього діалогу",
  "tone": "одне слово",
  "response_pattern": "як ця людина відповідає — патерн поведінки",
  "hidden_meaning": "що насправді стоїть за словами — підтекст якого юзер може не помічати",
  "power_balance": "хто тут альфа а хто бігає за увагою — і чому це саме так",
  "red_flags": [
    {{
      "flag": "назва паттерну",
      "psychotype": "що це означає психологічно",
      "advice": "що конкретно робити з цим прямо зараз"
    }}
  ],
  "summary": "вердикт без анестезії — 2-3 речення правди якої юзер можливо боявся почути",
  "user_style": {{
    "emoji_usage": "мало/середньо/багато",
    "message_length": "короткі/середні/довгі",
    "tone": "як юзер пише — стиль, характер",
    "uses_slang": true
  }}
}}{context_text}"""
        })

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": messages_content}],
            max_tokens=1200,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Помилка в analyze_screenshots: {e}")
        return {"error": "Не вдалося проаналізувати скріншот. Спробуй пізніше."}


async def generate_response(analysis: dict, mode: str) -> list:
    try:
        mode_prompts = {
            "flirt": """флiртувати — але не як школяр що вперше побачив дівчину. 
Грайливо, з підтекстом, трохи нахабно. Змусь людину перечитати повідомлення двічі.
Ніяких 'ти така гарна' — це нудно і передбачувано.""",

            "put_in_place": """поставити на місце — холодно, розумно, без крику.
Одне влучне речення що збиває з ніг краще ніж скандал.
Сарказм дозволений, образи — ні. Залиш їх думати що не так.""",

            "joke": """пожартувати — гостро, ситуативно, можливо трохи на межі.
Ніяких заїжджених мемів і анекдотів. Тільки те що народилось з цієї конкретної ситуації.
Якщо смішно — відправляй. Якщо не смішно — це не жарт.""",

            "soft_reject": """м'яко відмовити — щоб людина зрозуміла 'ні' але не відчула себе дном.
Без 'давай залишимось друзями' і без брехні. 
Гідно, чесно, з повагою — але двері закриті назавжди.""",

            "support": """підтримати — але не з ватою в роті.
Без 'все буде добре' і порожніх слів. 
'Це справді хуйня, і твої почуття норм' — ось з чого починаємо.
Потім конкретно: що робити далі."""
        }

        mode_description = mode_prompts.get(mode, "відповісти нейтрально")
        user_style = analysis.get("user_style", {})
        uses_slang = user_style.get("uses_slang", False)
        slang_note = "Юзер використовує сленг — вплітай органічно." if uses_slang else "Без сленгу — нейтральна жива мова."

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""{SYSTEM_PERSONALITY}

ЗАВДАННЯ: {mode_description}

СТИЛЬ:
- Емодзі: {user_style.get('emoji_usage', 'мало')}
- Довжина: {user_style.get('message_length', 'середні')}
- {slang_note}
- Звучить як ЛЮДИНА, не як GPT написав о третій ночі

Три варіанти — від стриманого до зухвалого. Кожен має бути робочим і відправним.

Поверни ТІЛЬКИ JSON:
{{
  "variants": [
    {{"label": "М'яко", "text": "..."}},
    {{"label": "Впевнено", "text": "..."}},
    {{"label": "Зухвало", "text": "..."}}
  ]
}}"""
                },
                {
                    "role": "user",
                    "content": f"Ситуація: {analysis.get('summary', '')}. Підтекст: {analysis.get('hidden_meaning', '')}. Тон: {analysis.get('tone', '')}. Придумай варіанти."
                }
            ],
            max_tokens=700,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("variants", [])

    except Exception as e:
        logger.error(f"Помилка в generate_response: {e}")
        return [{"label": "Помилка", "text": "Не вдалося згенерувати відповідь."}]


async def chat_with_bot(messages: list, mode: str) -> str:
    try:
        mode_system_prompts = {
            "friend": f"""{SYSTEM_PERSONALITY}

Режим: КРАЩИЙ ДРУГ.
Той що скаже правду навіть якщо боляче. Але завжди на твоєму боці.
Говориш як живий — з гумором, сленгом, емоціями. 
Не читаєш лекцій. Просто кажеш що думаєш і що робив би сам.""",

            "psychologist": f"""{SYSTEM_PERSONALITY}

Режим: ПСИХОЛОГ БЕЗ ЦУКРУ.
Емпатичний але не м'якотілий. Задаєш правильні питання.
Допомагаєш людині самій дійти до відповіді — не нав'язуєш її.
НЕ кажеш 'все буде добре' — кажеш 'давай розберемось що насправді відбувається'.""",

            "coach": f"""{SYSTEM_PERSONALITY}

Режим: КОУЧ.
Менше соплів — більше діла. 
Конкретні кроки, конкретні дії, конкретний результат.
Не приймаєш відмовок. Якщо людина саботує себе — кажеш про це прямо.""",

            "honest": f"""{SYSTEM_PERSONALITY}

Режим: МАКСИМАЛЬНА ЧЕСНІСТЬ.
Якщо людина робить фігню — кажеш про це. Без 'але з іншого боку'.
Дипломатія — не твоє. Правда — твоє.
Можна боляче. Не можна жорстоко.""",

            "stylist": f"""{SYSTEM_PERSONALITY}

Режим: СТИЛІСТ.
Гострий язик але добре серце. Любиш людей але ненавидиш погані образи.
Не просто 'виглядаєш норм' — а ЩО конкретно змінити, ЧОМУ це не працює, і ЯК це виправити.
Знаєш тренди але не раб трендів — головне щоб людині йшло."""
        }

        system_prompt = mode_system_prompts.get(mode, mode_system_prompts["friend"])
        full_system = f"{system_prompt}\n\nМова відповіді = мова юзера. Не звучи як робот. Будь живим."

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": full_system}] + messages,
            max_tokens=700
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Помилка в chat_with_bot: {e}")
        return "Вибач, щось пішло не так. Давай ще раз?"


async def analyze_outfit(image_data: str, destination: str) -> dict:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    },
                    {
                        "type": "text",
                        "text": f"""{SYSTEM_PERSONALITY}

Ти — стиліст що бачив все. І зараз бачить цей образ.
Людина збирається: {destination}

Оціни ЧЕСНО. Не лизи. Не знищуй. 
Говори як той друг що знається на стилі і скаже правду перед виходом.

Поверни ТІЛЬКИ JSON:
{{
  "vibe": "одна фраза що одразу передає суть образу — з характером",
  "score": число 0-100,
  "what_works": ["що реально добре і чому", "що вже влучає в ціль"],
  "fix_this": ["що конкретно змінити", "що не підходить для цієї події і чому"],
  "final_verdict": "2-3 речення фінального вердикту — як скаже стиліст перед виходом з дому"
}}"""
                    }
                ]
            }],
            max_tokens=700,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Помилка в analyze_outfit: {e}")
        return {"error": "Не вдалося проаналізувати образ. Спробуй ще раз."}


async def compare_crushes(crush1: dict, crush2: dict) -> dict:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""{SYSTEM_PERSONALITY}

Ти порівнюєш двох людей. Не дипломат — суддя.
Дивишся на цифри, паттерни, редфлаги. І кажеш як є."""
                },
                {
                    "role": "user",
                    "content": f"""Ось дані. Скажи хто реально вартий уваги — і чому.

{crush1.get('name')}:
- Інтерес: {crush1.get('avg_interest')}%  
- Тони спілкування: {', '.join(crush1.get('tones', []))}
- Редфлаги: {', '.join(crush1.get('red_flags', [])) or 'немає'}

{crush2.get('name')}:
- Інтерес: {crush2.get('avg_interest')}%
- Тони спілкування: {', '.join(crush2.get('tones', []))}
- Редфлаги: {', '.join(crush2.get('red_flags', [])) or 'немає'}

Поверни ТІЛЬКИ JSON:
{{
  "winner": "ім'я",
  "winner_score": число 0-100,
  "loser_score": число 0-100,
  "verdict": "2-3 речення чесного порівняння — без м'якого мила",
  "crush1_pros": ["конкретний плюс", "конкретний плюс"],
  "crush2_pros": ["конкретний плюс", "конкретний плюс"],
  "final_advice": "що конкретно робити далі — один чіткий крок"
}}"""
                }
            ],
            max_tokens=700,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Помилка в compare_crushes: {e}")
        return {"error": "Не вдалося порівняти. Спробуй ще раз."}