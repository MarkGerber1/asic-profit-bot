print("🔧 НАЧИНАЕМ простейший тест...")

import asyncio
print("✅ asyncio импортирован")

from aiogram import Bot, Dispatcher, F
print("✅ aiogram импортирован")

from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
print("✅ Все aiogram модули импортированы")

BOT_TOKEN = "8242982177:AAHGXUrY03XkbwrujbsvxO3DZDzc39S60GE"
print("✅ BOT_TOKEN установлен")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
print("✅ Bot и Dispatcher созданы")

MENU = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Тест")]],
    resize_keyboard=True,
    is_persistent=True
)
print("✅ Меню создано")

@dp.message(CommandStart())
async def start(message: Message):
    print(f"🟢 /start от {message.from_user.id}")
    await message.answer("✅ <b>РАБОТАЕТ!</b>", reply_markup=MENU)

@dp.message(F.text == "Тест")
async def test(message: Message):
    print(f"🟢 Кнопка 'Тест' от {message.from_user.id}")
    await message.answer("🎉 <b>КНОПКА РАБОТАЕТ!</b>", reply_markup=MENU)

async def main():
    print("🚀 Запуск простейшего бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🔥 НАЧИНАЕМ MAIN...")
    asyncio.run(main())
    print("🏁 MAIN ЗАВЕРШЕН") 