import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from groq import Groq

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# ---- НАСТРОЙКИ И ТОКЕНЫ ----
API_TOKEN = '8950772471:AAEBaTKh_wUU9V_tw7_HT2lZbckbvzbL7Lo'
GROQ_API_KEY = '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'
ADMIN_ID = 6499973284
GITHUB_URL = 'https://github.com/akhbel125-dev/my-first-tg-bot'

# Прямая ссылка на фото для блока "Обо мне" (можешь заменить на свою, если нужно)
ABOUT_PHOTO_URL = 'https://raw.githubusercontent.com/akhbel125-dev/my-first-tg-bot/main/about.jpg'

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()
ai_client = Groq(api_key=GROQ_API_KEY)

# ---- ГЛАВНОЕ МЕНЮ ----
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Обо мне"), KeyboardButton(text="Прайс")]
    ],
    resize_keyboard=True
)

# Хэндлер на команду /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "Добро пожаловать. Бот успешно запущен и готов к работе. Используйте меню ниже для навигации или отправьте текстовый запрос для ИИ.",
            reply_markup=main_keyboard
        )
    else:
        await message.answer("Доступ ограничен.")

# Хэндлер для кнопки "Обо мне" (с отправкой фото и текстом)
@dp.message(lambda message: message.text == "Обо мне")
async def about_me(message: Message):
    if message.from_user.id != ADMIN_ID: 
        return
    
    caption_text = (
        "Пользователь: akhbel125-dev\n"
        "Специализация: Разработка Telegram-ботов, автоматизация процессов на Python.\n\n"
        f"Исходный код данного проекта доступен в репозитории GitHub:\n{GITHUB_URL}"
    )
    
    try:
        # Отправляем фото с описанием
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=ABOUT_PHOTO_URL,
            caption=caption_text
        )
    except Exception:
        # Если фото не найдено по ссылке, отправляем просто текст, чтобы бот не падал
        await message.answer(caption_text)

# Хэндлер для кнопки "Прайс"
@dp.message(lambda message: message.text == "Прайс")
async def price_list(message: Message):
    if message.from_user.id != ADMIN_ID: 
        return
        
    await message.answer(
        "Разработка Telegram-ботов под ключ:\n\n"
        "• Простой бот-визитка — от 500 ₽\n"
        "• Бот с интеграцией ИИ (Groq/Llama) — от 1500 ₽\n"
        "• Сложные системы (FSM, базы данных) — договорная."
    )

# Хэндлер для текстовых запросов к ИИ
@dp.message()
async def handle_message(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        completion = ai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )
        response_text = completion.choices[0].message.content
        await message.answer(response_text)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка при обращении к Groq AI:\n`{e}`")

async def main():
    print("=== БОТ УСПЕШНО ЗАПУЩЕН! ===")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
