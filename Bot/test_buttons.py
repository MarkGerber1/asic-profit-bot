import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ТЕСТОВОЕ МЕНЮ
TEST_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Тест 1"), KeyboardButton(text="Тест 2")],
        [KeyboardButton(text="🪙 ТОП-майнеры"), KeyboardButton(text="📈 Аналитика")]
    ],
    resize_keyboard=True,
    is_persistent=True,
    one_time_keyboard=False
)

@dp.message(CommandStart())
async def start_handler(message: Message):
    print(f"🟢 /start от пользователя {message.from_user.id}")
    await message.answer(
        "🔧 <b>ТЕСТ КНОПОК</b>\n\nНажмите любую кнопку для теста:",
        reply_markup=TEST_MENU
    )

# Простые текстовые кнопки
@dp.message(F.text == "Тест 1")
async def test1_handler(message: Message):
    print(f"✅ РАБОТАЕТ: Тест 1 от пользователя {message.from_user.id}")
    await message.answer("✅ <b>Кнопка 'Тест 1' РАБОТАЕТ!</b>", reply_markup=TEST_MENU)

@dp.message(F.text == "Тест 2")
async def test2_handler(message: Message):
    print(f"✅ РАБОТАЕТ: Тест 2 от пользователя {message.from_user.id}")
    await message.answer("✅ <b>Кнопка 'Тест 2' РАБОТАЕТ!</b>", reply_markup=TEST_MENU)

# Кнопки с эмодзи
@dp.message(F.text == "🪙 ТОП-майнеры")
async def emoji1_handler(message: Message):
    print(f"✅ ЭМОДЗИ РАБОТАЕТ: ТОП-майнеры от пользователя {message.from_user.id}")
    await message.answer("✅ <b>Кнопка с эмодзи '🪙 ТОП-майнеры' РАБОТАЕТ!</b>", reply_markup=TEST_MENU)

@dp.message(F.text == "📈 Аналитика")
async def emoji2_handler(message: Message):
    print(f"✅ ЭМОДЗИ РАБОТАЕТ: Аналитика от пользователя {message.from_user.id}")
    await message.answer("✅ <b>Кнопка с эмодзи '📈 Аналитика' РАБОТАЕТ!</b>", reply_markup=TEST_MENU)

# Ловим ВСЕ текстовые сообщения
@dp.message(F.text)
async def catch_all_handler(message: Message):
    print(f"🔍 ПОЛУЧЕН ТЕКСТ: '{message.text}' от пользователя {message.from_user.id}")
    print(f"🔍 ДЛИНА: {len(message.text)} символов")
    print(f"🔍 БАЙТЫ: {message.text.encode('utf-8')}")
    print(f"🔍 REPR: {repr(message.text)}")
    
    await message.answer(
        f"🔍 <b>ДИАГНОСТИКА:</b>\n\n"
        f"📝 Получен текст: <code>{message.text}</code>\n"
        f"📏 Длина: {len(message.text)} символов\n"
        f"🔢 Первые 3 символа: {repr(message.text[:3])}\n\n"
        f"💡 Попробуйте кнопки выше!",
        reply_markup=TEST_MENU
    )

async def main():
    print("🔧 ЗАПУСК ДИАГНОСТИЧЕСКОГО БОТА ДЛЯ ТЕСТИРОВАНИЯ КНОПОК")
    print("🔧 Все нажатия будут логироваться в консоль")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 