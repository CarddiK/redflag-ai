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



        context_text = f"\nДодатковий контекст: {context}" if context else ""



        messages_content.append({

            "type": "text",

            "text": f"""Ти — експерт з аналізу переписок та психології спілкування.

Проаналізуй скріншоти та поверни ТІЛЬКИ JSON.



ПРАВИЛА МОВИ ТА СТИЛЮ:

- Якщо в переписці використовується сленг — використовуй його у відповіді

- Якщо переписка формальна — відповідай формально

- Використовуй емодзі у відповіді ТІЛЬКИ якщо вони є в переписці

- Мова відповіді = мова переписки



Формат відповіді:

{{

  "interest_level": число 0-100,

  "vibe_check": "коротка влучна фраза про загальний вайб діалогу",

  "tone": "одне слово про тон",

  "response_pattern": "як співрозмовник відповідає",

  "red_flags": [

    {{

      "flag": "назва червоного прапорця",

      "psychotype": "психотип або поведінковий паттерн",

      "advice": "конкретна порада як діяти"

    }}

  ],

  "summary": "2-3 речення чесного аналізу",

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

        logger.error(f"Помилка в analyze_screenshots: {e}")

        return {"error": "Не вдалося проаналізувати скріншот. Спробуй пізніше."}





async def generate_response(analysis: dict, mode: str) -> list:

    try:

        mode_prompts = {

            "flirt": "фліртувати — грайливо, з інтригою, використовувати легкий український сленг",

            "put_in_place": "поставити на місце — впевнено, база, без агресії, але жорстко",

            "joke": "пожартувати — смішно, можна використовувати самоіронію",

            "soft_reject": "м'яко відшити — ввічливо, але чітко",

            "support": "підтримати — тепло, бути 'своїм' бро"

        }



        mode_description = mode_prompts.get(mode, "відповісти нейтрально")

        user_style = analysis.get("user_style", {})



        response = await client.chat.completions.create(

            model="gpt-4o",

            messages=[

                {

                    "role": "system",

                    "content": f"""Ти допомагаєш скласти відповідь. Стиль: {mode_description}.

Використовуй стиль користувача: емодзі {user_style.get('emoji_usage')}, довжина {user_style.get('message_length')}.

Якщо контекст український — пиши живою українською мовою зі сленгом.

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

                    "content": f"Аналіз ситуації: {analysis.get('summary', '')}. Напиши варіанти."

                }

            ],

            max_tokens=500,

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

            "friend": "Ти — твій бро, кажеш як є, використовуєш сленг (база, жиза), багато жартуєш.",

            "psychologist": "Ти — емпатичний психолог, говориш обережно, допомагаєш розібратися в собі.",

            "coach": "Ти — коуч. Твій підхід: 'Менше соплів, більше діла'. Даєш чіткі інструкції.",

            "honest": "Ти — максимально прямий. Якщо людина робить фігню — ти так і кажеш. Без цензури (але в межах етики).",

            "stylist": "Ти — стиліст з гострим язиком але добрим серцем. Даєш чіткі поради по стилю та образу."

        }



        system_prompt = mode_system_prompts.get(mode, mode_system_prompts["friend"])

        full_system_prompt = f"{system_prompt} Спілкуйся тією мовою, якою пише користувач. Використовуй сленг, якщо це доречно."



        response = await client.chat.completions.create(

            model="gpt-4o",

            messages=[{"role": "system", "content": full_system_prompt}] + messages,

            max_tokens=500

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

                        "text": f"""Ти — стиліст з гострим язиком але добрим серцем.

Людина зібралась: {destination}

Оціни образ та поверни ТІЛЬКИ JSON:

{{

  "vibe": "одна фраза про загальний вайб образу",

  "score": число 0-100,

  "what_works": ["що реально добре", "що зайшло"],

  "fix_this": ["що змінити", "що не підходить для події"],

  "final_verdict": "2-3 речення фінального вердикту з характером"

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

                    "content": "Ти — експерт з аналізу відносин. Порівнюєш двох людей чесно і з гумором."

                },

                {

                    "role": "user",

                    "content": f"""Порівняй двох людей на основі аналізів переписок та поверни ТІЛЬКИ JSON:



Людина 1 — {crush1.get('name')}:

- Середній рівень інтересу: {crush1.get('avg_interest')}%

- Тони: {crush1.get('tones')}

- Червоні прапорці: {crush1.get('red_flags')}



Людина 2 — {crush2.get('name')}:

- Середній рівень інтересу: {crush2.get('avg_interest')}%

- Тони: {crush2.get('tones')}

- Червоні прапорці: {crush2.get('red_flags')}



{{

  "winner": "ім'я того хто більше підходить",

  "winner_score": число 0-100,

  "loser_score": число 0-100,

  "verdict": "2-3 речення чесного порівняння з характером",

  "crush1_pros": ["плюс1", "плюс2"],

  "crush2_pros": ["плюс1", "плюс2"],

  "final_advice": "фінальна порада що робити далі"

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
