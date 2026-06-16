import asyncio
import os
import sqlite3  # Подключаем настоящую базу данных
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from groq import Groq

# ---- НАСТРОЙКИ И ТОКЕНЫ ----
API_TOKEN = '8950772471:AAEBaTKh_wUU9V_tw7_HT2lZbckbvzbL7Lo'
GROQ_API_KEY = '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'
ADMIN_ID = 6499973284
GITHUB_URL = 'https://github.com/akhbel125-dev/my-first-tg-bot'
DB_FILE = 'bot_database.db'  # Теперь это файл базы данных SQLite

# Инициализируем бота, диспетчер и ИИ-клиент Groq
bot = Bot(token=API_TOKEN)
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


# ---- СОСТОЯНИЯ (FSM) ДЛЯ ПОШАГОВОГО ОПРОСА КЛИЕНТА ----
class BotStates(StatesGroup):
    waiting_for_business = State()  # Шаг 1: сфера бизнеса
    waiting_for_features = State()  # Шаг 2: функции бота
    waiting_for_budget = State()  # Шаг 3: бюджет и контакты
    waiting_for_broadcast = State()  # Ожидание текста рассылки от админа


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


# ---- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ SQLITE ----

def init_db():
    """Создает таблицу пользователей, если её еще нет в базе данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Создаем таблицу из трех колонок: ID, Юзернейм и Полное имя
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_user(user_id: int, username: str, full_name: str):
    """Сохраняет пользователя в базу данных SQLite (если его там нет, старые не дублируются)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # INSERT OR IGNORE автоматически пропустит запись, если такой user_id уже существует
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
                   (user_id, username, full_name))
    conn.commit()
    conn.close()


def get_users_count() -> int:
    """Возвращает точное количество уникальных пользователей из базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_users_ids():
    """Возвращает чистый список всех ID пользователей для рассылки"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    rows = cursor.fetchall()
    conn.close()
    # Превращаем список кортежей [(123,), (456,)] в обычный список [123, 456]
    return [row[0] for row in rows]


# ---- ОБРАБОТЧИКИ КОМАНД И КНОПОК ----

@dp.message(F.text == "/start")
async def send_welcome(message: Message, state: FSMContext):
    await state.clear()

    # Получаем юзернейм, если он есть, или пишем "нет"
    tg_username = message.from_user.username if message.from_user.username else "нет"

    # Сохраняем пользователя в нашу новую взрослую базу SQLite
    save_user(
        user_id=message.from_user.id,
        username=tg_username,
        full_name=message.from_user.full_name
    )

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


# ---- ПОШАГОВЫЙ КОНСТРУКТОР ЗАКАЗА (КНОПКА ЗАКАЗАТЬ БОТА) ----

@dp.message(F.text == "Заказать бота 💰")
async def order_process_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_business)
    await message.answer(
        "🚀 **Запуск конструктора заказа!**\n\n"
        "Шаг 1 из 3: Для какой сферы бизнеса или для каких целей нужен бот? (Например: магазин одежды, автосервис, турниры по FC Mobile, личный блог):"
    )


@dp.message(BotStates.waiting_for_business)
async def order_process_business(message: Message, state: FSMContext):
    await state.update_data(business=message.text)
    await state.set_state(BotStates.waiting_for_features)
    await message.answer(
        "📊 **Шаг 2 из 3**\n\n"
        "Какие функции должны быть в боте? (Например: рассылка пользователям, прием оплаты, админ-панель, интеграция с нейросетью):"
    )


@dp.message(BotStates.waiting_for_features)
async def order_process_features(message: Message, state: FSMContext):
    await state.update_data(features=message.text)
    await state.set_state(BotStates.waiting_for_budget)
    await message.answer(
        "💰 **Шаг 3 из 3**\n\n"
        "Укажи твой примерный budget (если знаешь) и оставь контакты для связи (твой юзернейм `@username` или телефон):"
    )


@dp.message(BotStates.waiting_for_budget)
async def order_process_finish(message: Message, state: FSMContext):
    user_data = await state.get_data()
    budget_and_contact = message.text
    await state.clear()

    if message.from_user.id != ADMIN_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "скрыт/нет"

        report = (
            f"🚨 **ПОСТУПИЛ НОВЫЙ ЗАКАЗ С ПОЛНЫМ ОПИСАНИЕМ!**\n\n"
            f"👤 **Имя клиента:** {message.from_user.full_name}\n"
            f"🔗 **Юзернейм в ТГ:** {username}\n"
            f"🆔 **ID пользователя:** {message.from_user.id}\n\n"
            f"🏢 **Сфера/Цель проекта:**\n{user_data['business']}\n\n"
            f"⚙️ **Что должен делать бот (Функции):**\n{user_data['features']}\n\n"
            f"💵 **Бюджет и контакты для связи:**\n{budget_and_contact}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=report, parse_mode="Markdown")
        await message.answer(
            "Ваша заявка успешно оформлена и отправлена разработчику! Он свяжется с вами в ближайшее время. 🚀")
    else:
        await message.answer(
            "Хозяин, тест конструктора прошел успешно! Заявку зафиксировал, но самому себе пересылать не буду. 👍")


# ---- СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ (ТОЛЬКО ДЛЯ ТЕБЯ) ----

@dp.message(F.text == "/admin")
async def open_admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Добро пожаловать в секретную панель управления, Хозяин! Выберите действие:",
                             reply_markup=admin_keyboard)
    else:
        pass


@dp.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        await message.answer(
            f"📊 **СТАТИСТИКА БОТА**\n\nВ базе данных SQLite зарегистрировано всего пользователей: **{count}**")


@dp.message(F.text == "📢 Сделать рассылку")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.set_state(BotStates.waiting_for_broadcast)
        await message.answer("Введите текст рассылки. Его получат **все** пользователи бота! Напишите сообщение 👇")


@dp.message(BotStates.waiting_for_broadcast)
async def do_broadcast(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.clear()

        users = get_all_users_ids()
        if not users:
            await message.answer("База данных SQLite пуста!")
            return

        await message.answer(f"Начинаю рассылку для {len(users)} пользователей из базы SQLite... ⏳")

        success_count = 0
        for u_id in users:
            try:
                await bot.send_message(chat_id=int(u_id), text=message.text)
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception:
                continue

        await message.answer(
            f"📢 Рассылка завершена!\nУспешно доставлено сообщений: **{success_count}** из **{len(users)}**.",
            reply_markup=admin_keyboard)


@dp.message(F.text == "🔙 Выйти из админки")
async def close_admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Вы вышли из админ-панели. Возвращаю стандартное меню.", reply_markup=main_keyboard)


# ---- РАБОТА ИСКУССТВЕННОГО ИНТЕЛЛЕКТА (ОБЫЧНЫЕ СООБЩЕНИЯ) ----

@dp.message()
async def ai_chat_handler(message: Message):
    if message.text == "/admin" and message.from_user.id != ADMIN_ID:
        pass

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        chat_completion = ai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
        )

        ai_response = chat_completion.choices[0].message.content
        await message.answer(ai_response)

    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        await message.answer(
            "Извините, у моего процессора закружилась голова. Попробуйте написать еще раз чуть позже! 🧠")


# ---- ЗАПУСК БОТА ----
async def main():
    init_db()  # Обязательно запускаем создание базы данных SQLite перед стартом опроса Телеграм
    print("Бот со встроенным ИИ, SQLite и админкой успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())