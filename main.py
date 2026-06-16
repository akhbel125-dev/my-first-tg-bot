import asyncio
import os
import logging
from aiogram.filters import CommandStart
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from groq import Groq

# Включаем логирование, чтобы Render мгновенно выводил информацию
logging.basicConfig(level=logging.INFO)

# ---- НАСТРОЙКИ И ТОКЕНЫ ----
# Твой самый новый рабочий токен
API_TOKEN = '8950772471:AAEBaTKh_wUU9V_tw7_HT2lZbckbvzbL7Lo'
GROQ_API_KEY = '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'
ADMIN_ID = 6499973284
GITHUB_URL = 'https://github.com/akhbel125-dev/my-first-tg-bot'
DB_FILE = 'users.txt'  # Файл, где будут храниться ID пользователей

# Инициализируем бота с поддержкой Markdown, диспетчер и ИИ-клиент Groq
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()
ai_client = Groq(api_key=GROQ_API_KEY)


# ---- СУПЕР-ИНСТРУКЦИЯ ДЛЯ ИИ (АНОНИМНАЯ) ----
SYSTEM_PROMPT = (
    "Ты — умный и вежливый ИИ-ассистент крутого Python-разработчика, основателя этого проекта. "
    "Твоя цель — общаться с клиентами, отвечать на их вопросы про создание Telegram-ботов, "
    "рассказывать о преимуществах автоматизации бизнеса и мотивировать их сделать заказ. "
    "Ни в коем случае не называй имя разработчика. Если клиент спросит, говори, что он предпочитает оставаться инкогнито "
    "и общается лично только по делу после оформления заявки. "
    "Говори уверенно, профессионально, но дружелюбно. Подчеркивай, что наш разработчик пишет качественный код на aiogram. "
    "Если клиент хочет сделать заказ, напомни ему нажать на кнопку 'Заказать бота 💰'. "
    "Отвечай на языке пользователя (по умолчанию на русском), пиши кратко и по делу."
)


# ---- СОСТОЯНИЯ (FSM) ----
class BotStates(StatesGroup):
    waiting_for_tz = State()        # Ожидание текста заказа от пользователя
    waiting_for_broadcast = State() # Ожидание текста рассылки от админа


# ---- КЛАВИАТУРЫ ----

# Главное меню для обычных пользователей
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Обо мне 🧑‍💻"), KeyboardButton(text="Посмотреть мой GitHub 📂")],
        [KeyboardButton(text="Заказать бота 💰")]
    ],
    resize_keyboard=True
)

# Секретное меню для тебя (Админка)
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📢 Сделать рассылку")],
        [KeyboardButton(text="🔙 Выйти из админки")]
    ],
    resize_keyboard=True
)

github_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Открыть репозиторий 🚀", url=GITHUB_URL)]
    ]
)


# ---- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ (ФАЙЛОМ) ----

def save_user(user_id: int):
    """Добавляет ID пользователя в файл, если его там еще нет"""
    user_id_str = str(user_id)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            f.write(user_id_str + '\n')
        return

    with open(DB_FILE, 'r') as f:
        users = f.read().splitlines()

    if user_id_str not in users:
        with open(DB_FILE, 'a') as f:
            f.write(user_id_str + '\n')

def get_users_count() -> int:
    """Возвращает количество уникальных пользователей"""
    if not os.path.exists(DB_FILE):
        return 0
    with open(DB_FILE, 'r') as f:
        users = f.read().splitlines()
    return len(users)


# ---- ОБРАБОТЧИКИ КОМАНД И КНОПОК ----

@dp.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext):
    await state.clear()
    # Сохраняем пользователя в нашу мини-базу данных
    save_user(message.from_user.id)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я бот-визитка с искусственным интеллектом.\n"
        f"Ты можешь задать мне любой вопрос про разработку ботов прямо в чат, или воспользоваться меню ниже! 👇",
        reply_markup=main_keyboard
    )


@dp.message(F.text == "Обо мне 🧑‍💻")
async def about_me(message: Message):
    photo_path = "my_photo.jpg"
    text_content = (
        "Я начинающий Python-разработчик. Создаю крутых и функциональных Telegram-ботов на библиотеке aiogram. "
        "Готов реализовать проект любой сложности для вашего бизнеса!"
    )
    if os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        await message.answer_photo(photo=photo, caption=text_content)
    else:
        await message.answer(text_content + "\n\n(Файл my_photo.jpg не найден)")


@dp.message(F.text == "Посмотреть мой GitHub 📂")
async def show_github(message: Message):
    await message.answer(
        "Нажми на кнопку ниже, чтобы перейти в мой публичный репозиторий и оценить код этого бота:",
        reply_markup=github_keyboard
    )


# ---- ЛОГИКА ЗАКАЗА ОТ КЛИЕНТА ----

@dp.message(F.text == "Заказать бота 💰")
async def order_process(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_tz)
    await message.answer(
        "Прекрасно! Напиши прямо сейчас **одним сообщением**:\n\n"
        "1. Какого бота ты хочешь получить (ТЗ/идея).\n"
        "2. Твой бюджет (если знаешь).\n"
        "3. Как с тобой связаться.\n\n"
        "Следующее твое сообщение будет отправлено напрямую разработчику! 👇"
    )


@dp.message(BotStates.waiting_for_tz)
async def forward_tz_to_admin(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "скрыт/нет"
        report = (
            f"🚨 **НОВЫЙ ЗАКАЗ В БОТЕ!**\n\n"
            f"👤 **Имя:** {message.from_user.full_name}\n"
            f"🔗 **Юзернейм:** {username}\n"
            f"🆔 **ID пользователя:** {message.from_user.id}\n\n"
            f"📋 **Текст заявки:**\n{message.text}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=report)
        await message.answer("Ваша заявка успешно отправлена разработчику! Он свяжется с вами в ближайшее время. 🚀")
    else:
        await message.answer("Хозяин, тест прошел успешно! Заявка перехвачена, но самому себе дублировать не буду. 👍")
    
    await state.clear()


# ---- СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ (ТОЛЬКО ДЛЯ ТЕБЯ) ----

@dp.message(F.text == "/admin")
async def open_admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Добро пожаловать в секретную панель управления, Хозяин! Выберите действие:", reply_markup=admin_keyboard)
    else:
        # Для обычных пользователей команда просто проигнорируется здесь и уйдет в ИИ
        pass


@dp.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        await message.answer(f"📊 **СТАТИСТИКА БОТА**\n\nВ базе данных зарегистрировано всего пользователей: **{count}**")


@dp.message(F.text == "📢 Сделать рассылку")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.set_state(BotStates.waiting_for_broadcast)
        await message.answer("Введите текст рассылки. Его получат **все** пользователи бота! Напишите сообщение 👇")


@dp.message(BotStates.waiting_for_broadcast)
async def do_broadcast(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.clear()
        
        if not os.path.exists(DB_FILE):
            await message.answer("База данных пуста!")
            return
            
        with open(DB_FILE, 'r') as f:
            users = f.read().splitlines()
            
        await message.answer(f"Начинаю рассылку для {len(users)} пользователей... ⏳")
        
        success_count = 0
        for u_id in users:
            try:
                await bot.send_message(chat_id=int(u_id), text=message.text)
                success_count += 1
                await asyncio.sleep(0.05) # Задержка против спам-фильтра Telegram
            except Exception:
                continue
                
        await message.answer(f"📢 Рассылка завершена!\nУспешно доставлено сообщений: **{success_count}** из **{len(users)}**.", reply_markup=admin_keyboard)


@dp.message(F.text == "🔙 Выйти из админки")
async def close_admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Вы вышли из админ-панели. Возвращаю стандартное меню.", reply_markup=main_keyboard)


# ---- РАБОТА ИСКУССТВЕННОГО ИНТЕЛЛЕКТА (ОБЫЧНЫЕ СООБЩЕНИЯ) ----

@dp.message()
async def ai_chat_handler(message: Message):
    # Если обычный пользователь пытается ввести /admin, это перехватит ИИ
    if message.text == "/admin" and message.from_user.id != ADMIN_ID:
        pass

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        chat_completion = ai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            model="llama-3.1-8b-instant",  # Новая рабочая модель вместо устаревшей
            temperature=0.7,
        )
        
        ai_response = chat_completion.choices[0].message.content
        await message.answer(ai_response, parse_mode=None)
        
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        await message.answer("Извините, у моего процессора закружилась голова. Попробуйте написать еще раз чуть позже! 🧠")


# ---- ЗАПУСК БОТА ----
async def main():
    print("=== БОТ УСПЕШНО ЗАПУЩЕН! ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
