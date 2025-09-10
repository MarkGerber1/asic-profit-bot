import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN
from ranking import init_db, get_top, refresh_miners, get_miner_by_model
from user_db import init_user_db, get_user_settings, update_user_tariff, update_user_currency, add_favorite_miner, remove_favorite_miner, get_user_favorites
from currency import format_currency
from scheduler import start_scheduler
from messages import build_ranking_message, build_deep_dive, build_compare_message, build_help_message, build_market_message, build_settings_message

logging.basicConfig(level=logging.INFO)

# States для FSM
class UserStates(StatesGroup):
    waiting_for_tariff = State()
    waiting_for_compare_model1 = State()
    waiting_for_compare_model2 = State()

# Инициализация бота
default_props = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(BOT_TOKEN, default=default_props)
dp = Dispatcher()

# ГЛАВНОЕ МЕНЮ - ПОСТОЯННЫЕ КНОПКИ ВНИЗУ ЭКРАНА
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

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Стартовое сообщение с главным меню"""
    await message.answer(
        "🚀 <b>Добро пожаловать в ASIC Profit Bot!</b>\n\n"
        "💎 Я помогу вам найти самые прибыльные ASIC майнеры с учетом "
        "вашего индивидуального тарифа на электричество.\n\n"
        "🎯 <b>Что я умею:</b>\n"
        "• 🏆 Показывать реальную прибыльность майнеров\n"
        "• 💱 Конвертировать цены в рубли и другие валюты\n"
        "• ⚙️ Учитывать ваши локальные условия\n"
        "• 📊 Предоставлять подробную аналитику\n"
        "• ⭐ Сохранять избранные модели\n\n"
        "🔥 <b>Выберите действие из меню ниже!</b>",
        reply_markup=MAIN_MENU
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Справка со списком команд"""
    help_text = build_help_message()
    await message.answer(help_text, reply_markup=MAIN_MENU)

# --- Обработчики кнопок главного меню ---

@dp.message(F.text == "🪙 ТОП-майнеры")
async def menu_top_miners(message: Message):
    """Обработчик кнопки ТОП-майнеры"""
    print(f"✅ ХЕНДЛЕР: Обрабатывается кнопка 'ТОП-майнеры' от пользователя {message.from_user.id}")
    try:
        user_settings = await get_user_settings(message.from_user.id)
        tariff = user_settings['electricity_tariff']
        currency = user_settings['currency']
        
        miners = await get_top(10, tariff, currency)
        if not miners:
            await message.answer(
                "❌ <b>Данные временно недоступны</b>\n\n"
                "⏳ Попробуйте через минуту — возможно идёт обновление базы данных.\n\n"
                "🔄 <i>Данные обновляются каждые 12 часов</i>",
                reply_markup=MAIN_MENU
            )
            return
        
        # Используем функцию форматирования из messages.py
        response_text = build_ranking_message(miners, tariff, currency)
        await message.answer(response_text, reply_markup=MAIN_MENU)
        
    except Exception as e:
        print(f"Error in menu_top_miners: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка при загрузке данных</b>\n\n"
            "🔧 Попробуйте позже или обратитесь к администратору.\n\n"
            "💡 Возможные причины:\n"
            "• Обновление базы данных\n"
            "• Временные проблемы с источниками данных\n"
            "• Техническое обслуживание",
            reply_markup=MAIN_MENU
        )

@dp.message(F.text == "📈 Аналитика")  
async def menu_analytics(message: Message):
    """Обработчик кнопки Аналитика"""
    print(f"✅ ХЕНДЛЕР: Обрабатывается кнопка 'Аналитика' от пользователя {message.from_user.id}")
    try:
        user_settings = await get_user_settings(message.from_user.id)
        miners = await get_top(100, user_settings['electricity_tariff'], user_settings['currency'])
        
        if not miners:
            await message.answer(
                "❌ <b>Данные для аналитики недоступны</b>\n\n"
                "⏳ Попробуйте через минуту",
                reply_markup=MAIN_MENU
            )
            return
        
        # Используем функцию из messages.py для аналитики
        analytics_text = build_market_message(miners, user_settings['currency'])
        await message.answer(analytics_text, reply_markup=MAIN_MENU)
        
    except Exception as e:
        print(f"Error in menu_analytics: {e}")
        await message.answer(
            "📊 <b>АНАЛИТИКА РЫНКА ASIC</b>\n\n"
            "❌ Данные временно недоступны\n"
            "🔄 Попробуйте позже",
            reply_markup=MAIN_MENU
        )

@dp.message(F.text == "💸 Профит в рублях")
async def menu_profit_rub(message: Message):
    """Обработчик кнопки Профит в рублях"""
    print(f"✅ ХЕНДЛЕР: Обрабатывается кнопка 'Профит в рублях' от пользователя {message.from_user.id}")
    try:
        # Принудительно устанавливаем рубли
        user_id = message.from_user.id
        await update_user_currency(user_id, 'RUB')
        
        user_settings = await get_user_settings(user_id)
        tariff = user_settings['electricity_tariff']
        
        miners = await get_top(10, tariff, 'RUB')
        if not miners:
            await message.answer(
                "❌ <b>Данные временно недоступны</b>\n\n"
                "⏳ Попробуйте через минуту — возможно идёт обновление базы данных.",
                reply_markup=MAIN_MENU
            )
            return
        
        # Форматируем в рублях
        response_text = build_ranking_message(miners, tariff, 'RUB')
        # Добавляем заголовок специально для рублей
        rub_text = f"🇷🇺 <b>ПРОФИТ В РУБЛЯХ</b>\n\n{response_text}"
        
        await message.answer(rub_text, reply_markup=MAIN_MENU)
        
    except Exception as e:
        print(f"Error in menu_profit_rub: {e}")
        await message.answer(
            "🇷🇺 <b>ПРОФИТ В РУБЛЯХ</b>\n\n"
            "❌ Данные временно недоступны\n"
            "🔄 Попробуйте позже",
            reply_markup=MAIN_MENU
        )

@dp.message(F.text == "⚙️ Настройки")
async def menu_settings(message: Message):
    """Обработчик кнопки Настройки"""
    try:
        user_settings = await get_user_settings(message.from_user.id)
        settings_text = build_settings_message(user_settings)
        
        # Добавляем inline кнопки для настроек
        settings_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡ Изменить тариф", callback_data="change_tariff"),
                InlineKeyboardButton(text="💱 Сменить валюту", callback_data="change_currency")
            ],
            [
                InlineKeyboardButton(text="❤️ Избранное", callback_data="show_favorites"),
                InlineKeyboardButton(text="🗑️ Очистить избранное", callback_data="clear_favorites")
            ]
        ])
        
        await message.answer(settings_text, reply_markup=settings_kb)
        
    except Exception as e:
        print(f"Error in menu_settings: {e}")
        await message.answer(
            "⚙️ <b>НАСТРОЙКИ БОТА</b>\n\n"
            "❌ Ошибка загрузки настроек\n"
            "🔄 Попробуйте позже",
            reply_markup=MAIN_MENU
        )

@dp.message(F.text == "🛠️ Гайд по установке")
async def menu_guide(message: Message):
    """Обработчик кнопки Гайд по установке"""
    guide_text = """
🛠️ <b>ПОЛНЫЙ ГАЙД ПО УСТАНОВКЕ ASIC-МАЙНЕРА</b>

🎯 <b>ШАГ 1: ВЫБОР МАЙНЕРА</b>
• 💡 Используйте кнопку 🪙 ТОП-майнеры для выбора прибыльной модели
• 📊 Учитывайте ваш tарифу на электричество
• 🌡️ Проверьте требования к охлаждению
• 💰 Рассчитайте период окупаемости

🏠 <b>ШАГ 2: ПОДГОТОВКА ПОМЕЩЕНИЯ</b>
• 🌪️ Приточно-вытяжная вентиляция (обязательно!)
• 🌡️ Температура воздуха не выше 30°C
• 💧 Влажность не более 65%
• 🔇 Отдельное помещение (шум 70-80 дБ)
• 🚨 Пожарная сигнализация

⚡ <b>ШАГ 3: ЭЛЕКТРИКА</b>
• 🔌 Отдельная линия с автоматом
• 🛡️ УЗО (устройство защитного отключения)
• 🌍 Заземление обязательно
• 📏 Кабель сечением 2.5-4 мм²
• 📊 Расчет: мощность майнера + 25% запас

🌐 <b>ШАГ 4: СЕТЬ И НАСТРОЙКА</b>
• 🔗 Ethernet подключение (WiFi не рекомендуется)
• 🔍 Поиск IP-адреса майнера
• 💻 Вход через веб-интерфейс
• ⛏️ Настройка пула майнинга
• 🔐 Смена паролей по умолчанию

🔧 <b>ШАГ 5: ОБСЛУЖИВАНИЕ</b>
• 🧹 Чистка каждые 2-4 недели
• 🌡️ Мониторинг температуры
• 📊 Контроль хешрейта
• 🔄 Обновление прошивки
• 📝 Ведение журнала работы

⚠️ <b>ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ:</b>
• 🚫 Не размещайте в жилых помещениях
• 💨 Обеспечьте достаточную вентиляцию  
• ⚡ Не перегружайте электросеть
• 🧯 Держите огнетушитель поблизости
• 📞 Уведомите страховую компанию

💡 <b>ПОЛЕЗНЫЕ ССЫЛКИ:</b>
• Калькуляторы: WhatToMine, NiceHash
• Пулы: Antpool, F2Pool, Poolin
• Прошивки: Braiins OS+, HiveOS
• Мониторинг: minerstat, awesome-miner

❓ Есть вопросы? Используейте ❓ FAQ в меню!
    """
    
    await message.answer(guide_text, reply_markup=MAIN_MENU)

@dp.message(F.text == "ℹ️ О боте")
async def menu_about(message: Message):
    """Обработчик кнопки О боте"""
    about_text = """
ℹ️ <b>О ПРОЕКТЕ ASIC PROFIT BOT</b>

🎯 <b>МИССИЯ</b>
Помочь майнерам принимать обоsnованные решения при выборе ASIC-оборудования с учетом реальных условий эксплуатации.

🔧 <b>ЧТО ДЕЛАЕТ БОТ:</b>
• 📊 Собирает данные с ведущих сайтов (WhatToMine, AsicMinerValue)
• 💰 Рассчитывает реальную прибыльность с учетом ваших тарифов
• 💱 Конвертирует цены в рубли по актуальному курсу
• 📈 Предоставляет аналитику рынка
• 🛠️ Дает практические советы по установке

⚡ <b>ОСОБЕННОСТИ:</b>
• 🎯 Персонализированные расчеты
• 🔄 Обновление данных каждые 12 часов  
• 🇷🇺 Полная русская локализация
• 📱 Удобный интерфейс с красивыми иконками
• ⭐ Система избранных майнеров

👨‍💻 <b>РАЗРАБОТЧИК:</b>
Бот создан энтузиастом криптовалютного майнинга для помощи сообществу. 

📧 <b>КОНТАКТЫ:</b>
• Телеграм: @your_username
• Email: support@asicprofitbot.com
• GitHub: github.com/your-repo

💝 <b>ПОДДЕРЖАТЬ ПРОЕКТ:</b>
• BTC: bc1qxxxxxxxxxxxxxxxxxxx
• ETH: 0xxxxxxxxxxxxxxxxxxxx
• Поделиться ботом с друзьями

🎉 <b>БЛАГОДАРНОСТИ:</b>
Спасибо всем, кто тестирует бота и присылает обратную связь!

📅 Версия: 2.0
🗓️ Последнее обновление: декабрь 2024
    """
    
    await message.answer(about_text, reply_markup=MAIN_MENU)

@dp.message(F.text == "🤝 Партнёрка")
async def menu_partner(message: Message):
    """Обработчик кнопки Партнёрка"""
    user_id = message.from_user.id
    partner_text = f"""
🤝 <b>ПАРТНЁРСКАЯ ПРОГРАММА</b>

💰 <b>ЗАРАБАТЫВАЙТЕ С НАМИ!</b>
Приглашайте друзей и получайте вознаграждение за каждого активного пользователя!

🎯 <b>УСЛОВИЯ ПРОГРАММЫ:</b>
• 💵 5% с покупок по вашим реферальным ссылкам
• 🎁 Бонус 500₽ за каждые 10 рефералов
• 🏆 Дополнительные призы для топ-партнёров
• 📈 Прогрессивная система: чем больше рефералов, тем выше %

🔗 <b>ВАША РЕФЕРАЛЬНАЯ ССЫЛКА:</b>
<code>https://t.me/asic_profit_helper_bot?start=ref_{user_id}</code>

📊 <b>СТАТИСТИКА:</b>
• 👥 Приглашено пользователей: <b>0</b>
• 💰 Заработано: <b>0₽</b>
• 🏆 Ваш уровень: <b>Новичок</b>

🎁 <b>УРОВНИ ПАРТНЁРА:</b>
• 🥉 Новичок (0-9 рефералов): 5%
• 🥈 Эксперт (10-49 рефералов): 7%
• 🥇 Профи (50-99 рефералов): 10%
• 💎 VIP (100+ рефералов): 15%

💳 <b>ВЫПЛАТЫ:</b>
• Минимальная сумма: 1000₽
• Способы: Qiwi, Юmoney, банковская карта
• Периодичность: каждые 15 дней
• Комиссия: 0% (мы берем на себя)

❓ <b>ВОПРОСЫ?</b>
Напишите в поддержку: @partner_support_bot
    """
    
    await message.answer(partner_text, reply_markup=MAIN_MENU)

@dp.message(F.text == "❓ FAQ")
async def menu_faq(message: Message):
    """Обработчик кнопки FAQ"""
    faq_text = """
❓ <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>

🤔 <b>Откуда берутся данные о прибыльности?</b>
📊 Мы собираем данные с ведущих калькуляторов майнинга: WhatToMine и AsicMinerValue. Данные обновляются каждые 12 часов.

💰 <b>Как рассчитывается реальная прибыль?</b>
🧮 Формула: (Доход в день) - (Потребление кВт⋅ч × Ваш тариф × 24 часа)

🔄 <b>Как часто обновляются курсы валют?</b>
💱 Курсы валют обновляются при каждом запросе через API Центрального Банка РФ и других надежных источников.

⚡ <b>Как правильно рассчитать тариф на электричество?</b>
📋 Возьмите квитанцию за свет, разделите сумму к доплате на количество потребленных кВт⋅ч, переведите в доллары по текущему курсу.

🏠 <b>Можно ли майнить дома?</b>
⚠️ ASIC-майнеры очень шумные (70-80 дБ) и выделяют много тепла. Нужно отдельное проветриваемое помещение.

🌡️ <b>Какая температура критична для майнера?</b>
🚨 Критично: выше 85°C. Оптимально: 60-75°C. При 80°C+ майнер начинает троттлинг (снижение производительности).

🔧 <b>Нужна ли особая электропроводка?</b>
⚡ Да! Нужна отдельная линия с автоматом на 25А+, УЗО, заземление. Сечение кабеля минимум 2.5 мм².

💸 <b>Когда майнинг становится убыточным?</b>
📉 Когда стоимость электричества превышает доход от майнинга. Следите за красными индикаторами в боте.

🛒 <b>Где лучше покупать майнеры?</b>
🏪 Официальные дилеры > проверенные продавцы на AliExpress > б/у с гарантией. Остерегайтесь слишком низких цен!

🔄 <b>Как часто нужно обслуживать майнер?</b>
🧹 Чистка от пыли: каждые 2-4 недели. Замена термопасты: раз в год. Профилактика вентиляторов: каждые 3-6 месяцев.

⛏️ <b>Какой пул выбрать для майнинга?</b>
🏊 Крупные: Antpool, F2Pool, Poolin. Для began лучше крупные пулы со стабильными выплатами.

📱 <b>Есть ли мобильное приложение?</b>
📲 Пока только Telegram-бот, но мы работаем над мобильным приложением!

🆘 <b>НЕ НАШЛИ ОТВЕТ?</b>
Задайте вопрос в поддержке: @support_bot
Или в чате сообщества: @asic_chat
    """
    
    await message.answer(faq_text, reply_markup=MAIN_MENU)

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

# Дополнительные команды
@dp.message(Command("mytariff"))
async def cmd_my_tariff(message: Message):
    try:
        user_settings = await get_user_settings(message.from_user.id)
        tariff = user_settings['electricity_tariff']
        currency = user_settings['currency']
        
        await message.answer(
            f"💡 <b>ВАШИ ТЕКУЩИЕ НАСТРОЙКИ</b>\n\n"
            f"⚡ Тариф на электричество: <b>${tariff:.3f}/кВт⋅ч</b>\n"
            f"💱 Валюта отображения: <b>{currency}</b>\n"
            f"🌍 Регион: <b>Автоопределение</b>\n\n"
            f"🔧 Изменить настройки: используйте кнопку ⚙️ Настройки в меню",
            reply_markup=MAIN_MENU
        )
    except Exception as e:
        print(f"Error in cmd_my_tariff: {e}")
        await message.answer("❌ Ошибка загрузки настроек", reply_markup=MAIN_MENU)

@dp.message(Command("favorites"))
async def cmd_favorites(message: Message):
    try:
        user_id = message.from_user.id
        favorites = await get_user_favorites(user_id)
        
        if not favorites:
            await message.answer(
                "⭐ <b>ИЗБРАННЫЕ МАЙНЕРЫ</b>\n\n"
                "📭 У вас пока нет избранных майнеров.\n\n"
                "💡 <i>Добавляйте майнеры в избранное через детальный просмотр в топе</i>",
                reply_markup=MAIN_MENU
            )
        return
        
        text = "⭐ <b>ВАШИ ИЗБРАННЫЕ МАЙНЕРЫ</b>\n\n"
        for fav in favorites[:10]:  # Показываем максимум 10
            text += f"• <b>{fav['vendor']} {fav['model']}</b>\n"
            text += f"  ⭐ <i>Добавлен в избранное</i>\n\n"
        
        text += f"📊 <i>Всего избранных: {len(favorites)}</i>\n\n"
        text += f"💡 <i>Актуальные данные по майнерам смотрите в 🪙 ТОП-майнеры</i>"
        
        await message.answer(text, reply_markup=MAIN_MENU)
        
    except Exception as e:
        print(f"Error in cmd_favorites: {e}")
        await message.answer("❌ Ошибка загрузки избранного", reply_markup=MAIN_MENU)

# Обработчики inline callback'ов
@dp.callback_query(F.data == "change_tariff")
async def change_tariff_callback(callback, state: FSMContext):
    await callback.message.answer(
        "⚡ <b>ИЗМЕНЕНИЕ ТАРИФА НА ЭЛЕКТРИЧЕСТВО</b>\n\n"
        "💡 Введите ваш тариф в долларах за кВт⋅ч.\n\n"
        "📋 <b>Как узнать тариф:</b>\n"
        "1️⃣ Возьмите квитанцию за электричество\n"
        "2️⃣ Разделите сумму на количество кВт⋅ч\n"
        "3️⃣ Переведите в доллары по курсу\n\n"
        "🔢 <b>Пример:</b> 0.05 или 0.12\n\n"
        "❌ Для отмены используйте /cancel",
        reply_markup=MAIN_MENU
    )
    await state.set_state(UserStates.waiting_for_tariff)
    await callback.answer()

@dp.callback_query(F.data == "change_currency")
async def change_currency_callback(callback):
    currencies_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 USD", callback_data="currency_USD"),
            InlineKeyboardButton(text="🇷🇺 RUB", callback_data="currency_RUB")
        ],
        [
            InlineKeyboardButton(text="🇪🇺 EUR", callback_data="currency_EUR"),
            InlineKeyboardButton(text="🇨🇳 CNY", callback_data="currency_CNY")
        ]
    ])
    
    await callback.message.answer(
        "💱 <b>ВЫБОР ВАЛЮТЫ</b>\n\n"
        "Выберите валюту для отображения прибыльности:",
        reply_markup=currencies_kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("currency_"))
async def currency_callback(callback):
    currency = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    await update_user_currency(user_id, currency)
    
    currency_names = {
        'USD': '🇺🇸 Доллар США',
        'RUB': '🇷🇺 Российский рубль', 
        'EUR': '🇪🇺 Евро',
        'CNY': '🇨🇳 Китайский юань'
    }
    
    await callback.message.answer(
        f"✅ <b>Валюта изменена!</b>\n\n"
        f"💱 Новая валюта: <b>{currency_names[currency]}</b>\n\n"
        f"🔄 Все расчеты будут пересчитаны автоматически при следующем запросе.",
        reply_markup=MAIN_MENU
    )
    await callback.answer(f"Валюта изменена на {currency}")

# FSM обработчики
@dp.message(UserStates.waiting_for_tariff)
async def process_tariff(message: Message, state: FSMContext):
    try:
        tariff = float(message.text)
        if tariff <= 0 or tariff > 1:
            await message.answer(
                "❌ <b>Некорректный тариф!</b>\n\n"
                "Тариф должен быть положительным числом и не больше $1/кВт⋅ч.\n\n"
                "🔢 Попробуйте еще раз:",
                reply_markup=MAIN_MENU
            )
            return
        
        user_id = message.from_user.id
        await update_user_tariff(user_id, tariff)
        
        await message.answer(
            f"✅ <b>Тариф успешно обновлен!</b>\n\n"
            f"⚡ Новый тариф: <b>${tariff:.3f}/кВт⋅ч</b>\n\n"
            f"🔄 Все расчеты прибыльности будут пересчитаны с учетом нового тарифа.",
            reply_markup=MAIN_MENU
        )
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Введите число в формате: 0.05 или 0.12\n\n"
            "🔢 Попробуйте еще раз:",
            reply_markup=MAIN_MENU
        )

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ <b>Действие отменено</b>\n\n"
        "Возвращаемся к главному меню.",
        reply_markup=MAIN_MENU
    )

# ОТЛАДОЧНЫЙ ХЕНДЛЕР (последний в очереди)
@dp.message(F.text)
async def debug_text_handler(message: Message):
    """Отладочный хендлер - логирует все необработанные текстовые сообщения"""
    print(f"🐛 DEBUG: Необработанный текст: '{message.text}' (len={len(message.text)})")
    print(f"🐛 DEBUG: Repr: {repr(message.text)}")
    print(f"🐛 DEBUG: Bytes: {message.text.encode('utf-8')}")
    await message.answer(
        f"🤔 <b>Не понимаю команду:</b> <code>{message.text}</code>\n\n"
        f"💡 Используйте кнопки меню внизу экрана!",
        reply_markup=MAIN_MENU
    )

# Главная функция
async def main():
    print("🚀 Запуск ASIC Profit Bot с полным функционалом...")
    try:
        print("📊 Инициализация базы данных...")
    await init_db()
        print("👤 Инициализация пользовательской базы...")
        await init_user_db()
        print("⏰ Запуск планировщика...")
    start_scheduler()
        print("🔄 Первичная загрузка данных...")
    await refresh_miners()
        print("✅ Все системы инициализированы! Запуск бота...")
    await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")

if __name__ == "__main__":
    asyncio.run(main())
