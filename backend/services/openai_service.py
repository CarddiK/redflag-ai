import os
import base64
import httpx
import json
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

        context_text = f"\nКонтекст від юзера: {context}" if context else ""

        # ЗОЛОТИЙ ПРОМПТ АНАЛІЗУ
        messages_content.append({
            "type": "text",
                "text": f"""Ти — RedFlag AI, топовий цифровий психолог і експерт з маніпуляцій. 
Твоє завдання: роздягнути цей діалог до істини. Ти не "асистент", ти — той самий прямолінійний бро, який каже правду в очі.

ПРАВИЛА АНАЛІЗУ:
1. Читай між рядків. Хто домінує? Хто "в ігнорі"? Хто виправдовується?
2. Звертай увагу на час відповідей та ініціативу.
3. Якщо бачиш маніпуляції (газлайтинг, гостінг, лав-бомбінг) — називай їх прямо.

ПРАВИЛА СТИЛЮ:
- Мова: жива українська з використанням актуального сленгу (база, крінж, вайб, жиза, гост, шип).
- Тон: іронічний, гострий, впевнений. Ніякої "води".
- Формат: ТІЛЬКИ JSON.

Формат відповіді:
{{
  "interest_level": число 0-100,
  "vibe_check": "коротка іронічна фраза про вайб",
  "power_balance": "хто веде в діалозі, а хто наздоганяє",
  "hidden_meaning": "що насправді стоїть за цими словами (підтекст)",
  "red_flags": [
    {{
      "flag": "назва прапорця",
      "psychotype": "опис паттерну",
      "advice": "зухвала порада що робити"
    }}
  ],
  "summary": "3-4 речення жорсткого та чесного вердикту",
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
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"По error в analyze_screenshots: {e}")
        return {"error": "Бот перегрівся від цього крінжу. Спробуй пізніше."}


async def generate_response(analysis: dict, mode: str) -> list:
    try:
        # ОНОВЛЕНІ РЕЖИМИ ВІДПОВІДЕЙ
        mode_prompts = {
            "flirt": "фліртувати — нахабно, грайливо, з підтекстом, ніяких кліше, тільки вогонь",
            "put_in_place": "поставити на місце — інтелектуальне приниження, сарказм, жорстка база",
            "joke": "пожартувати — гостро, іронічно, можна на межі фолу",
            "soft_reject": "м'яко відшити — елегантно закрити двері, не лишаючи надії",
            "support": "підтримати — як справжній бро, без соплів, але по факту"
        }

        mode_description = mode_prompts.get(mode, "відповісти нейтрально")
        user_style = analysis.get("user_style", {})

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""Ти — голос користувача. Ти допомагаєш йому написати відповідь, яка розірве діалог.
Стиль: {mode_description}.
Використовуй стиль юзера (емодзі: {user_style.get('emoji_usage')}), але зроби відповідь в 10 разів цікавішою. 
Уникай стилю "ШІ-помічника". Пиши як жива людина.

Верни ТІЛЬКИ JSON:
{{
  "variants": [
    {{"label": "Safe", "text": "обережний варіант"}},
    {{"label": "Style", "text": "стильний варіант"}},
    {{"label": "Toxic/Bold", "text": "зухвалий/нахабний варіант"}}
  ]
}}"""
                },
                {
                    "role": "user",
                    "content": f"Вердикт ситуації: {analysis.get('summary', '')}. Підтекст: {analysis.get('hidden_meaning', '')}. Напиши варіанти."
                }
            ],
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("variants", [])

    except Exception as e:
        logger.error(f"Помилка в generate_response: {e}")
        return [{"label": "Помилка", "text": "Навіть я не знаю, що тут відповісти..."}]


async def chat_with_bot(messages: list, mode: str) -> str:
    try:
        mode_system_prompts = {
            "friend": "Ти — твій бро. Кажеш правду, матюкаєшся (в міру), кидаєш бази, не любиш ниття.",
            "psychologist": "Ти — професор психології, який втомився від людської тупості, але реально допомагає.",
            "coach": "Ти — жорсткий коуч. Твій підхід: 'Встала і пішла'. Тільки конкретні дії.",
            "honest": "Ти — дзеркало. Максимально жорстка правда. Якщо юзер — 'запасний варіант', ти так і кажеш.",
            "stylist": "Ти — фешн-ікона. Твій язик гостріший за підбори. Оцінюй лук без жалю."
        }

        system_prompt = mode_system_prompts.get(mode, mode_system_prompts["friend"])
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system", 
                "content": f"{system_prompt} Пиши живою мовою, використовуй сленг. Не будь роботом."
            }] + messages,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Помилка в chat_with_bot: {e}")
        return "Мозок кипить. Давай ще раз?"
