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

SYSTEM_PERSONALITY = """Ти — RedFlag AI. Гострий на язик, іронічний, але чесний цифровий психолог. 
Ти бачиш людей наскрізь: від дешевих маніпуляцій до прихованої закоханості. 
Твій стиль — суміш серіалу 'Sex Education' та прямолінійності кращого друга. 
Тобі не цікаво бути ввічливим, тобі цікаво бути ПРАВИМ.
Якщо переписка українська — використовуй сучасний молодіжний сленг: 'база', 'крінж', 'вайб', 'гост', 'редфлаг'. Але не переборщуй."""


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

        context_text = f"\nДодатковий контекст від користувача: {context}" if context else ""

        messages_content.append({
            "type": "text",
            "text": f"""{SYSTEM_PERSONALITY}

Твоє завдання: роздягнути цей діалог до істини. Поверни ТІЛЬКИ JSON.

АНАЛІЗУЙ:
1. Час відповіді (якщо видно): хто чекає довше?
2. Ініціативу: хто задає питання, а хто відповідає одним словом?
3. Підтекст: що насправді стоїть за цими словами?
4. Баланс сил: хто ведучий, хто ведеться?

ПРАВИЛА МОВИ:
- Мова відповіді = мова переписки
- Якщо в переписці є сленг — використовуй його
- Емодзі тільки якщо вони є в переписці
- summary має бути таким, щоб юзер захотів переслати друзям

Формат відповіді:
{{
  "interest_level": число 0-100,
  "vibe_check": "коротка іронічна фраза про загальний вайб",
  "tone": "одне слово про тон",
  "response_pattern": "як співрозмовник відповідає",
  "hidden_meaning": "що насправді стоїть за цими словами — те що не кажуть прямо",
  "power_balance": "хто в цій переписці веде, а хто ведеться — і чому",
  "red_flags": [
    {{
      "flag": "назва червоного прапорця",
      "psychotype": "психотип або поведінковий паттерн",
      "advice": "конкретна порада як діяти"
    }}
  ],
  "summary": "жорсткий і чесний вердикт без цензури — 2-3 речення",
  "user_style": {{
    "emoji_usage": "мало/середньо/багато",
    "message_length": "короткі/середні/довгі",
    "tone": "опис стилю письма користувача",
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
            "flirt": "фліртувати — грайливо, з нахабством, використовувати двозначність і підтекст, ніяких шаблонних компліментів типу 'ти така гарна'",
            "put_in_place": "поставити на місце — інтелектуальна домінація, сарказм, тонко підколоти за слабке місце, але без образ",
            "joke": "пожартувати — гостро, можливо на межі фолу, ніяких анекдотів з 90-х, тільки ситуативний гумор",
            "soft_reject": "м'яко відшити — залишити людину з почуттям гідності, але без жодного шансу на 'так', без банального 'давай залишимось друзями'",
            "support": "підтримати — без 'все буде добре', натомість: 'це треш, але ми це розрулимо'. Живо і по-людськи"
        }

        mode_description = mode_prompts.get(mode, "відповісти нейтрально")
        user_style = analysis.get("user_style", {})
        uses_slang = user_style.get("uses_slang", False)
        slang_note = "Використовуй сучасний молодіжний сленг природно." if uses_slang else ""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""{SYSTEM_PERSONALITY}

Твоє завдання: {mode_description}.

Стиль відповіді:
- Емодзі: {user_style.get('emoji_usage', 'мало')}
- Довжина повідомлень: {user_style.get('message_length', 'середні')}
- {slang_note}

ВАЖЛИВО: Відповіді мають звучати як живі повідомлення від реальної людини, НЕ як текст написаний ШІ.
Три варіанти — від м'якого до зухвалого.

Верни ТІЛЬКИ JSON:
{{
  "variants": [
    {{"label": "М'яко", "text": "..."}},
    {{"label": "Середньо", "text": "..."}},
    {{"label": "Зухвало", "text": "..."}}
  ]
}}"""
                },
                {
                    "role": "user",
                    "content": f"Ситуація: {analysis.get('summary', '')}. Тон співрозмовника: {analysis.get('tone', '')}. Придумай варіанти відповіді."
                }
            ],
            max_tokens=600,
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
Зараз ти в режимі 'Кращий друг'. Кажеш як є, без фільтрів. 
Використовуєш сленг (база, жиза, крінж, вайб). Багато жартуєш але даєш реальні поради.""",

            "psychologist": f"""{SYSTEM_PERSONALITY}
Зараз ти в режимі 'Психолог'. Емпатичний але чесний. 
Допомагаєш розібратися в собі, задаєш правильні питання. 
НЕ кажеш 'все буде добре' — натомість допомагаєш зрозуміти що відбувається насправді.""",

            "coach": f"""{SYSTEM_PERSONALITY}
Зараз ти в режимі 'Коуч'. Твій підхід: менше соплів, більше діла. 
Даєш чіткі покрокові інструкції. Не терпиш відмовок і самопошкодування.""",

            "honest": f"""{SYSTEM_PERSONALITY}
Зараз ти в режимі 'Максимально чесний'. Якщо людина робить фігню — кажеш прямо. 
Без дипломатії, без 'з одного боку... з іншого боку'. Тільки правда.""",

            "stylist": f"""{SYSTEM_PERSONALITY}
Зараз ти в режимі 'Стиліст'. Гострий язик, добре серце. 
Даєш конкретні поради по стилю, образу, як подати себе. 
Не просто 'виглядаєш добре' — а що конкретно змінити і чому."""
        }

        system_prompt = mode_system_prompts.get(mode, mode_system_prompts["friend"])
        full_system = f"{system_prompt}\n\nСпілкуйся тією мовою якою пише користувач. Будь живим, не звучи як робот."

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": full_system}] + messages,
            max_tokens=600
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Помилка в chat_with_bot: {e}")
        return "Вибач, у мене стався внутрішній збій. Давай спробуємо ще раз?"


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
Зараз ти — стиліст з гострим язиком але добрим серцем.
Людина зібралась: {destination}

Оціни образ ЧЕСНО. Не лизи. Якщо щось не так — кажи прямо але конструктивно.
Поверни ТІЛЬКИ JSON:
{{
  "vibe": "одна іронічна фраза про загальний вайб образу",
  "score": число 0-100,
  "what_works": ["що реально добре", "що зайшло"],
  "fix_this": ["що змінити", "що не підходить для події"],
  "final_verdict": "2-3 речення фінального вердикту з характером — без цукру"
}}"""
                    }
                ]
            }],
            max_tokens=600,
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
Зараз ти порівнюєш двох людей. Будь чесним як кращий друг — без дипломатії."""
                },
                {
                    "role": "user",
                    "content": f"""Порівняй двох і скажи хто реально вартий уваги. Поверни ТІЛЬКИ JSON:

{crush1.get('name')}:
- Інтерес: {crush1.get('avg_interest')}%
- Тони: {crush1.get('tones')}
- Редфлаги: {crush1.get('red_flags')}

{crush2.get('name')}:
- Інтерес: {crush2.get('avg_interest')}%
- Тони: {crush2.get('tones')}
- Редфлаги: {crush2.get('red_flags')}

{{
  "winner": "ім'я переможця",
  "winner_score": число 0-100,
  "loser_score": число 0-100,
  "verdict": "2-3 речення чесного порівняння з характером",
  "crush1_pros": ["плюс1", "плюс2"],
  "crush2_pros": ["плюс1", "плюс2"],
  "final_advice": "фінальна порада що робити далі — конкретно"
}}"""
                }
            ],
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Помилка в compare_crushes: {e}")
        return {"error": "Не вдалося порівняти. Спробуй ще раз."}
