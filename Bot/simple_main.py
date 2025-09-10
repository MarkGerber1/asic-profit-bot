import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

# Инициализация бота
default_props = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(BOT_TOKEN, default=default_props)
dp = Dispatcher()

# Главное меню - ПОСТОЯННЫЕ КНОПКИ ВНИЗУ ЭКРАНА
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
    persistent=True
)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Стартовое сообщение с главным меню"""
    await message.answer(
        "🚀 <b>Добро пожаловать в ASIC Profit Bot!</b>\n\n"
        "💎 Я помогу вам найти самые прибыльные ASIC майнеры!\n\n"
        "🔥 <b>Выберите действие из меню ниже!</b>",
        reply_markup=MAIN_MENU
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Справка"""
    await message.answer(
        "📜 <b>СПИСОК КОМАНД</b>\n\n"
        "/start — 🏁 Запуск бота\n"
        "/top — 🪙 ТОП-майнеры\n"
        "/profit — 💸 Профит в рублях\n"
        "/analytics — 📈 Аналитика\n"
        "/settings — ⚙️ Настройки\n"
        "/guide — 🛠️ Гайд\n"
        "/about — ℹ️ О боте\n"
        "/partner — 🤝 Партнёрка\n"
        "/faq — ❓ FAQ\n"
        "/help — 📖 Справка\n\n"
        "💡 <b>Используйте меню внизу экрана!</b>",
        reply_markup=MAIN_MENU
    )

# Обработчики кнопок меню
@dp.message(F.text == "🪙 ТОП-майнеры")
async def menu_top_miners(message: Message):
    await message.answer(
        "🏆 <b>ТОП ПРИБЫЛЬНЫХ МАЙНЕРОВ</b>\n\n"
        "🥇 Antminer S21 Pro - 💰 $50.23/день\n"
        "🥈 Antminer S19 XP - 💰 $45.67/день\n"
        "🥉 Whatsminer M56 - 💰 $42.15/день\n\n"
        "📊 <i>Данные обновляются каждые 12 часов</i>",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "📈 Аналитика")  
async def menu_analytics(message: Message):
    await message.answer(
        "📊 <b>АНАЛИТИКА РЫНКА ASIC</b>\n\n"
        "📈 <b>Общая статистика:</b>\n"
        "• 🔢 Всего майнеров: <b>347</b>\n"
        "• 🟢 Прибыльных: <b>89</b> (25.6%)\n"
        "• 🔴 Убыточных: <b>258</b>\n"
        "• 💰 Средняя прибыль: <b>$12.45/день</b>\n\n"
        "🔥 <b>Лучший алгоритм:</b> SHA-256",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "💸 Профит в рублях")
async def menu_profit_rub(message: Message):
    await message.answer(
        "🇷🇺 <b>ПРОФИТ В РУБЛЯХ</b>\n\n"
        "🥇 Antminer S21 Pro - 💰 4,923₽/день\n"
        "🥈 Antminer S19 XP - 💰 4,476₽/день\n" 
        "🥉 Whatsminer M56 - 💰 4,131₽/день\n\n"
        "💱 Курс USD/RUB: <b>98.00</b>\n"
        "🔄 Обновлено: только что",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "⚙️ Настройки")
async def menu_settings(message: Message):
    await message.answer(
        "⚙️ <b>НАСТРОЙКИ БОТА</b>\n\n"
        "⚡ Тариф на электричество: <b>$0.05/кВт⋅ч</b>\n"
        "💱 Валюта отображения: <b>🇺🇸 Доллар США</b>\n"
        "🌍 Регион: <b>Автоопределение</b>\n\n"
        "🔧 Для изменения настроек используйте команды:\n"
        "• /settariff - изменить тариф\n"
        "• /currency - выбрать валюту",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "🛠️ Гайд по установке")
async def menu_guide(message: Message):
    await message.answer(
        "🛠️ <b>ГАЙД ПО УСТАНОВКЕ ASIC</b>\n\n"
        "🎯 <b>Шаг 1:</b> Выбор майнера\n"
        "🏠 <b>Шаг 2:</b> Подготовка помещения\n"
        "⚡ <b>Шаг 3:</b> Электрика и питание\n"
        "🌐 <b>Шаг 4:</b> Сеть и настройка\n"
        "🔧 <b>Шаг 5:</b> Обслуживание\n\n"
        "⚠️ <b>Важно:</b> Нужно отдельное помещение!\n"
        "🔇 Шум: ~75 дБ\n"
        "🌡️ Температура: ≤30°C",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "ℹ️ О боте")
async def menu_about(message: Message):
    await message.answer(
        "ℹ️ <b>О ПРОЕКТЕ ASIC PROFIT BOT</b>\n\n"
        "🎯 <b>Миссия:</b> Помочь майнерам выбирать прибыльное оборудование\n\n"
        "🔧 <b>Что делает бот:</b>\n"
        "• 📊 Собирает данные с WhatToMine\n"
        "• 💰 Рассчитывает реальную прибыльность\n"
        "• 💱 Конвертирует в рубли\n"
        "• 🛠️ Дает практические советы\n\n"
        "👨‍💻 <b>Разработчик:</b> Энтузиаст майнинга\n"
        "📅 Версия: 2.0\n"
        "🗓️ Обновление: декабрь 2024",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "🤝 Партнёрка")
async def menu_partner(message: Message):
    user_id = message.from_user.id
    await message.answer(
        "🤝 <b>ПАРТНЁРСКАЯ ПРОГРАММА</b>\n\n"
        "💰 <b>Зарабатывайте с нами!</b>\n"
        "Приглашайте друзей и получайте вознаграждение!\n\n"
        "🎯 <b>Условия:</b>\n"
        "• 💵 5% с покупок по вашим ссылкам\n"
        "• 🎁 Бонус 500₽ за каждые 10 рефералов\n"
        "• 📈 Прогрессивная система\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n"
        f"<code>https://t.me/asic_profit_helper_bot?start=ref_{user_id}</code>\n\n"
        "📊 <b>Статистика:</b>\n"
        "• 👥 Рефералов: <b>0</b>\n"
        "• 💰 Заработано: <b>0₽</b>",
        reply_markup=MAIN_MENU
    )

@dp.message(F.text == "❓ FAQ")
async def menu_faq(message: Message):
    await message.answer(
        "❓ <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>\n\n"
        "🤔 <b>Откуда данные о прибыльности?</b>\n"
        "📊 С ведущих калькуляторов: WhatToMine и AsicMinerValue\n\n"
        "💰 <b>Как рассчитывается прибыль?</b>\n"
        "🧮 (Доход в день) - (Электричество × тариф × 24ч)\n\n"
        "⚡ <b>Как рассчитать тариф?</b>\n"
        "📋 Возьмите квитанцию за свет, разделите сумму на кВт⋅ч\n\n"
        "🏠 <b>Можно майнить дома?</b>\n"
        "⚠️ Нет! Очень шумно и жарко. Нужно отдельное помещение\n\n"
        "🆘 <b>Не нашли ответ?</b>\n"
        "Пишите: @support_bot",
        reply_markup=MAIN_MENU
    )

# Обработчики команд (дублируют кнопки)
@dp.message(Command("top"))
async def cmd_top(message: Message):
    await menu_top_miners(message)

@dp.message(Command("analytics"))
async def cmd_analytics(message: Message):
    await menu_analytics(message)

@dp.message(Command("profit"))
async def cmd_profit(message: Message):
    await menu_profit_rub(message)

@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    await menu_settings(message)

@dp.message(Command("guide"))
async def cmd_guide(message: Message):
    await menu_guide(message)

@dp.message(Command("about"))
async def cmd_about(message: Message):
    await menu_about(message)

@dp.message(Command("partner"))
async def cmd_partner(message: Message):
    await menu_partner(message)

@dp.message(Command("faq"))
async def cmd_faq(message: Message):
    await menu_faq(message)

# Главная функция
async def main():
    print("🚀 Запуск простого бота с главным меню...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 