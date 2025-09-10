import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN

# Главное меню с эмодзи и 8 кнопками
MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🪙 ТОП-майнеры"),
            KeyboardButton(text="📈 Аналитика"),
            KeyboardButton(text="💸 Профит в рублях")
        ],
        [
            KeyboardButton(text="⚙️ Настройки"),
            KeyboardButton(text="🛠️ Гайд по установке")
        ],
        [
            KeyboardButton(text="ℹ️ О боте"),
            KeyboardButton(text="🤝 Партнёрка"),
            KeyboardButton(text="❓ FAQ")
        ]
    ],
    resize_keyboard=True,
    is_persistent=True,
    one_time_keyboard=False,
    input_field_placeholder="Выберите действие из меню..."
)

default_props = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(BOT_TOKEN, default=default_props)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    print(f"[LOG] /start от пользователя {message.from_user.id}")
    await message.answer(
        "<b>Добро пожаловать! Выберите действие из меню ниже.</b>",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "🪙 ТОП-майнеры")
async def top_miners(message: Message):
    print(f"[LOG] КНОПКА: ТОП-майнеры от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали ТОП-майнеры!", reply_markup=MAIN_MENU)

@dp.message(F.text == "📈 Аналитика")
async def analytics(message: Message):
    print(f"[LOG] КНОПКА: Аналитика от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали Аналитика!", reply_markup=MAIN_MENU)

@dp.message(F.text == "💸 Профит в рублях")
async def profit_rub(message: Message):
    print(f"[LOG] КНОПКА: Профит в рублях от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали Профит в рублях!", reply_markup=MAIN_MENU)

@dp.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    print(f"[LOG] КНОПКА: Настройки от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали Настройки!", reply_markup=MAIN_MENU)

@dp.message(F.text == "🛠️ Гайд по установке")
async def guide(message: Message):
    print(f"[LOG] КНОПКА: Гайд по установке от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали Гайд по установке!", reply_markup=MAIN_MENU)

@dp.message(F.text == "ℹ️ О боте")
async def about(message: Message):
    print(f"[LOG] КНОПКА: О боте от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали О боте!", reply_markup=MAIN_MENU)

@dp.message(F.text == "🤝 Партнёрка")
async def partner(message: Message):
    print(f"[LOG] КНОПКА: Партнёрка от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали Партнёрка!", reply_markup=MAIN_MENU)

@dp.message(F.text == "❓ FAQ")
async def faq(message: Message):
    print(f"[LOG] КНОПКА: FAQ от пользователя {message.from_user.id}")
    await message.answer("Вы выбрали FAQ!", reply_markup=MAIN_MENU)

@dp.message(F.text)
async def debug_handler(message: Message):
    print(f"[LOG] Необработанный текст: {message.text} от пользователя {message.from_user.id}")
    await message.answer("Неизвестная команда. Используйте кнопки меню!", reply_markup=MAIN_MENU)

async def main():
    print("[LOG] Запуск тестового бота с полным меню и эмодзи...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 