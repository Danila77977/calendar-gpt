import os
import json
import openai
from calendar_bot import get_free_slots, create_event

# Установите свой OpenAI API ключ
openai.api_key = os.getenv('OPENAI_API_KEY')  # или укажите строкой здесь

# Описание функций для GPT Function Calling
FUNCTIONS = [
    {
        "name": "get_free_slots",
        "description": "Получить список свободных слотов на указанную дату",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Дата в формате YYYY-MM-DD"}
            },
            "required": ["date"]
        }
    },
    {
        "name": "create_event",
        "description": "Запланировать встречу в календаре",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": "Начало встречи в ISO формате, например: 2025-08-01T14:00:00+03:00"},
                "end":   {"type": "string", "description": "Окончание встречи в ISO формате, например: 2025-08-01T14:30:00+03:00"},
                "email": {"type": "string", "description": "Email участника встречи"}
            },
            "required": ["start", "end", "email"]
        }
    }
]

# История сообщений с моделью
messages = [
    {"role": "system", "content": "Вы — ассистент, который автоматически планирует встречи для клиента."}
]

def run_agent(user_request: str) -> str:
    """Отправить запрос агенту и получить ответ"""
    # Добавляем запрос пользователя
    messages.append({"role": "user", "content": user_request})

    # Первый вызов: позволяем модели выбрать функцию автоматически
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=FUNCTIONS,
        function_call="auto"
    )
    message = response.choices[0].message

    # Если модель решила вызвать функцию — выполняем её
    if message.get("function_call"):
        fn_name = message["function_call"]["name"]
        args = json.loads(message["function_call"]["arguments"])
        if fn_name == "get_free_slots":
            result = get_free_slots(args["date"])
        else:
            result = create_event(args["start"], args["end"], args["email"])

        # Добавляем в историю вызов и результат функции
        messages.append(message)
        messages.append({"role": "function", "name": fn_name, "content": json.dumps(result)})

        # Второй запрос: модель формирует итоговый ответ
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return second_response.choices[0].message["content"]

    # Если без вызова функции — возвращаем ответ
    return message["content"]

# ========== Примеры использования закомментированы ==========
# if __name__ == "__main__":
#     print(run_agent("Покажи свободные слоты на 2025-08-02"))
#     print(run_agent(
#         "Забронируй встречу 2025-08-02T14:00:00+03:00 до 2025-08-02T14:30:00+03:00 с otdelsmayonezom@gmail.com"
#     ))
