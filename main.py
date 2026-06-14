import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import FSInputFile


TOKEN = "8950772471:AAEd6iaWv-qs1s0tWBiywobpihOduHiqiQU"

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()

    builder.add(types.KeyboardButton(text="Узнать прайс 💰"))
    builder.add(types.KeyboardButton(text="Обо мне 👨‍💻"))
    builder.add(types.KeyboardButton(text="Связаться 🤝"))

    builder.adjust(2)

    await message.answer(
        f"Привет, {message.from_user.first_name}! Я твой личный бот-визитка. Выбери пункт меню:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@dp.message()
async def echo_message(message: types.Message):
    user_text = message.text

    if user_text == "Узнать прайс 💰":
        await message.answer("Разработка простого бота: от 3000 руб.\nПарсер данных: от 2000 руб. 💸")

    elif user_text == "Обо мне 👨‍💻":
        inline_builder = InlineKeyboardBuilder()
        inline_builder.add(types.InlineKeyboardButton(
            text="Посмотреть мой GitHub 📂",
            url="https://github.com"
        ))

        photo = FSInputFile("my_photo.jpg")

        await message.answer_photo(
            photo=photo,
            caption="Я начинающий Python-разработчик.\n\nСдал ОГЭ по информатике на максимум, сейчас создаю автоматизацию и Telegram-ботов! 🚀",
            reply_markup=inline_builder.as_markup()
        )

    elif user_text == "Связаться 🤝":
        await message.answer("По всем вопросам пишите автору проекта: @akhbel_125")

    elif user_text.lower() == "привет":
        await message.answer("И тебе привет! Рад тебя слышать! 👋")

    elif user_text.lower() == "как дела":
        await message.answer("Отлично! Кручу код на Python в режиме 24/7. А у тебя?")

    else:
        await message.answer(f"Ты написал: {user_text}")


async def main():
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())