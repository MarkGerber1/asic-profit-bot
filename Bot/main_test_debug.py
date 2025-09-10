import asyncio
import logging

print("🔧 TEST 1: Проверяем основные импорты...")

try:
    from aiogram import Bot, Dispatcher, F
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties
    from aiogram.filters import CommandStart, Command
    from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
    print("✅ Основные aiogram модули импортированы")
except Exception as e:
    print(f"❌ Ошибка импорта aiogram: {e}")
    exit(1)

try:
    from config import BOT_TOKEN
    print("✅ config импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта config: {e}")
    exit(1)

print("🔧 TEST 2: Проверяем дополнительные модули...")

try:
    from ranking import get_top
    print("✅ ranking импортирован")
except Exception as e:
    print(f"⚠️ Ошибка импорта ranking: {e}")

try:
    from currency import convert_currency, get_exchange_rate
    print("✅ currency импортирован")
except Exception as e:
    print(f"⚠️ Ошибка импорта currency: {e}")

try:
    from user_db import get_user_tariff
    print("✅ user_db импортирован")
except Exception as e:
    print(f"⚠️ Ошибка импорта user_db: {e}")

try:
    from messages import build_ranking_message
    print("✅ messages импортирован")
except Exception as e:
    print(f"⚠️ Ошибка импорта messages: {e}")

print("🔧 TEST 3: Создаем простой бот...")

logging.basicConfig(level=logging.INFO)

# Инициализация бота
default_props = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(BOT_TOKEN, default=default_props)
dp = Dispatcher()

# ГЛАВНОЕ МЕНЮ
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
    input_field_placeholder="DEBUG версия..."
)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Стартовое сообщение"""
    print(f"✅ DEBUG /start от пользователя {message.from_user.id}")
    await message.answer(
        "🔧 <b>DEBUG ВЕРСИЯ БОТА</b>\n\n"
        "✅ Все импорты прошли успешно!\n"
        "🧪 Тестируем функциональность...\n\n"
        "Попробуйте кнопки:",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "🪙 ТОП-майнеры")
async def menu_top_miners(message: Message):
    """DEBUG версия ТОП-майнеров"""
    print(f"✅ DEBUG: ТОП-майнеры от пользователя {message.from_user.id}")
    
    try:
        # Пробуем получить данные из БД
        print("🔧 Пытаемся получить данные из БД...")
        
        # Безопасный вызов get_user_tariff
        try:
            user_id = message.from_user.id
            tariff = await get_user_tariff(user_id) 
            print(f"✅ Тариф пользователя: {tariff}")
        except Exception as e:
            print(f"⚠️ Ошибка get_user_tariff: {e}")
            tariff = 0.05  # default
        
        # Безопасный вызов get_top
        try:
            miners = await get_top(5, tariff, 'USD')
            print(f"✅ Получено майнеров: {len(miners) if miners else 0}")
            
            if miners:
                response_text = build_ranking_message(miners, 'USD', tariff)
                await message.answer(response_text, reply_markup=MAIN_MENU)
                return
                
        except Exception as e:
            print(f"⚠️ Ошибка get_top: {e}")
        
        # Fallback
        await message.answer(
            "🔧 <b>DEBUG: ТОП-майнеры</b>\n\n"
            "⚠️ Основная функция недоступна\n"
            "🔄 Используем тестовые данные...\n\n"
            "🥇 <b>Antminer S21 Pro</b>\n"
            "   💰 $50.23/день | ⚡ 3510Вт\n\n"
            "🔧 <i>Режим отладки активен</i>",
            reply_markup=MAIN_MENU
        )
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в menu_top_miners: {e}")
        await message.answer(
            f"❌ <b>ОШИБКА:</b>\n<code>{str(e)}</code>",
            reply_markup=MAIN_MENU
        )

@dp.message(F.text)
async def debug_all_text(message: Message):
    """DEBUG: все текстовые сообщения"""
    print(f"🔧 DEBUG текст: '{message.text}' от {message.from_user.id}")
    await message.answer(
        f"🔧 <b>DEBUG:</b> получен текст\n"
        f"📝 <code>{message.text}</code>\n\n"
        f"💡 Попробуйте кнопки меню!",
        reply_markup=MAIN_MENU
    )

async def main():
    print("🚀 Запуск DEBUG версии бота...")
    print("✅ Все импорты выполнены успешно!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ ФАТАЛЬНАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc() 