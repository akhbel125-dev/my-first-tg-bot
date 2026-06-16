import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram.filters import CommandStart
from groq import Groq

# Включаем логирование, чтобы Render показывал всё до единой строчки
logging.basicConfig(level=logging.INFO)

# ---- НАСТРОЙКИ И ТОКЕНЫ ----
# Твой самый новый токен, который ты скинул
API_TOKEN = '8950772471:AAEBaTKh_wUU9V_tw7_HT2lZbckbvzbL7Lo'
# Ключ Groq (если он выдаст ошибку лимитов, бот сам напишет об этом в чат)
GROQ_API_KEY = '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'
ADMIN_ID = 6499973284
GITHUB_URL = 'https://github.com/akhbel125-dev/my-first-tg-bot'

# Инициализируем бота и диспетчер без лишних костылей с таймаутами
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()
ai_client = Groq(api_key=GROQ_API_KEY)


# Хэндлер на команду /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Салам! Бот успешно запущен на сервере Render и готов к работе. Пиши любой вопрос!")
    else:
        await message.answer("Доступ ограничен.")


# Хэндлер на любые текстовые сообщения от тебя
@dp.message()
async def handle_message(message: Message):
    # Бот реагирует только на твои сообщения
    if message.from_user.id != ADMIN_ID:
        return

    # Отправляем анимацию «печатает...», чтобы ты видел, что бот думает
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Строгий и безопасный формат запроса к Llama 3 через Groq
        completion = ai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )

        # Забираем ответ нейросети
        response_text = completion.choices[0].message.content
        await message.answer(response_text)

    except Exception as e:
        # Если Groq споткнётся, ты сразу увидишь причину прямо в Телеграме
        await message.answer(f"⚠️ Ошибка при обращении к Groq AI:\n`{e}`")


# Главная функция запуска
async def main():
    print("=== БОТ УСПЕШНО ЗАПУЩЕН! ===")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
