import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties
from groq import Groq

# ---- НАСТРОЙКИ И ТОКЕНЫ ----
API_TOKEN = '8950772471:AAEBaTKh_wUU9V_tw7_HT2lZbckbvzbL7Lo'
GROQ_API_KEY = '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'
ADMIN_ID = 6499973284
GITHUB_URL = 'https://github.com/akhbel125-dev/my-first-tg-bot'


bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()
ai_client = Groq(api_key=GROQ_API_KEY)

# ПУТЬ К ПАПКЕ ПРОЕКТА (для фото)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ИСПРАВЛЕНИЕ ДЛЯ AMVERA: Сохраняем базу данных в постоянное хранилище /data
if os.path.exists('/data'):
    DB_FILE = '/data/users.txt'
else:
    # Если запускаем на компе, файл создастся как обычно рядом с кодом
    DB_FILE = os.path.join(BASE_DIR, 'users.txt')


# ---- СУПЕР-ИНСТРУКЦИЯ ДЛЯ ИИ ----
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
    waiting_for_tz = State()
    waiting_for_broadcast = State()


# ---- КЛАВИАТУРЫ ----
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Обо мне 🧑‍💻"), KeyboardButton(text="Посмотреть мой GitHub 📂")],
        [KeyboardButton(text="Заказать бота 💰")]
    ],
    resize_keyboard=True
)

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


# ---- ФУНКЦИИ БАЗЫ ДАННЫХ ----
def save_user(user_id: int):
    user_id_str = str(user_id)
    try:
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w') as f:
                f.write(user_id_str + '\n')
            return

        with open(DB_FILE, 'r') as f:
            users = f.read().splitlines()

        if user_id_str not in users:
            with open(DB_FILE, 'a') as f:
                f.write(user_id_str + '\n')
    except Exception as e:
        print(f"Ошибка записи БД: {e}")

def get_users_count() -> int:
    if not os.path.exists(DB_FILE):
        return 0
    try:
        with open(DB_FILE, 'r') as f:
            users = f.read().splitlines()
        return len(users)
    except Exception:
        return 0


# ---- ОБРАБОТЧИКИ ----

@dp.message(F.text == "/start")
async def send_welcome(message: Message, state: FSMContext):
    await state.clear()
    save_user(message.from_user.id)
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я бот-визитка с искусственным интеллектом.\n"
        f"Ты можешь задать мне любой вопрос про разработку ботов прямо в чат, или воспользоваться меню ниже! 👇",
        reply_markup=main_keyboard
    )


@dp.message(F.text == "Обо мне 🧑‍💻")
async def about_me(message: Message):
    photo_path = os.path.join(BASE_DIR, "my_photo.jpg")
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


@dp.message(F.text == "Заказать бота 💰")
async def order_process(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_tz)
    await message.answer(
        "Прекрасно! Напиши прямо сейчас одним сообщением:\n\n"
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


@dp.message(F.text == "/admin")
async def open_admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Добро пожаловать в секретную панель управления, Хозяин! Выберите действие:", reply_markup=admin_keyboard)


@dp.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        await message.answer(f"📊 **СТАТИСТИКА БОТА**\n\nВ базе данных зарегистрировано всего пользователей: **{count}**")


@dp.message(F.text == "📢 Сделать рассылку")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.set_state(BotStates.waiting_for_broadcast)
        await message.answer("Введите текст рассылки. Его получат все пользователи бота! Напишите сообщение 👇")


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
                await asyncio.sleep(0.05)
            except Exception:
                continue
        await message.answer(f"📢 Рассылка завершена!\nУспешно доставлено сообщений: **{success_count}** из **{len(users)}**.", reply_markup=admin_keyboard)


@dp.message(F.text == "🔙 Выйти из админки")
async def close_admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Вы вышли из админ-панели. Возвращаю стандартное меню.", reply_markup=main_keyboard)


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
        await message.answer("Извините, у моего процессора закружилась голова. Попробуйте написать еще раз чуть позже! 🧠")


async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())