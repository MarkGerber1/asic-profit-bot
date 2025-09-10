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
from ranking import init_db, get_top, refresh_miners
from user_db import init_user_db, get_user_settings, update_user_currency
from currency import format_currency
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

# States для FSM
class UserStates(StatesGroup):
    waiting_for_tariff = State()

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
    help_text = """
📜 <b>СПИСОК ВСЕХ КОМАНД</b>

/start — 🏁 Запуск бота и главное меню
/top — 🪙 ТОП самых прибыльных майнеров
/profit — 💸 Профит в рублях (по курсу ЦБ РФ)
/analytics — 📈 Аналитика рынка ASIC
/settings — ⚙️ Настройки тарифа и валюты
/guide — 🛠️ Гайд по установке майнеров
/about — ℹ️ О боте и разработчике
/partner — 🤝 Партнёрская программа
/faq — ❓ Часто задаваемые вопросы
/help — 📖 Справка по командам

🎯 <b>Быстрые команды:</b>
/favorites — ⭐ Ваши избранные майнеры
/mytariff — 💡 Ваши текущие настройки

💡 <b>Используйте меню внизу экрана для быстрой навигации!</b>
    """
    
    await message.answer(help_text, reply_markup=MAIN_MENU)

# --- Обработчики кнопок главного меню ---

@dp.message(F.text == "🪙 ТОП-майнеры")
async def menu_top_miners(message: Message):
    """Обработчик кнопки ТОП-майнеры"""
    try:
        user_settings = await get_user_settings(message.from_user.id)
        tariff = user_settings['electricity_tariff']
        currency = user_settings['currency']
        
        miners = await get_top(10, tariff, currency)
        if not miners:
            await message.answer(
                "❌ <b>Данные временно недоступны</b>\n\n"
                "⏳ Попробуйте через минуту — возможно идёт обновление базы данных.",
                reply_markup=MAIN_MENU
            )
            return
        
        # Простое форматирование без сложной логики
        lines = [
            "🏆 <b>ТОП ПРИБЫЛЬНЫХ МАЙНЕРОВ</b>",
            f"💱 Валюта: <b>{currency}</b> | ⚡ Тариф: <b>${tariff:.3f}/кВт⋅ч</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        for idx, m in enumerate(miners[:10], 1):
            # Простая проверка прибыльности
            try:
                profit = getattr(m, 'real_profit', m.daily_usd)
                profit_icon = "🟢" if profit > 0 else "🔴"
                daily_str = format_currency(m.daily_usd, currency)
                profit_str = format_currency(profit, currency) if hasattr(m, 'real_profit') else daily_str
            except:
                profit_icon = "⭐"
                daily_str = f"${m.daily_usd:.2f}"
                profit_str = daily_str
            
            rank_icon = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}️⃣"
            
            lines.append(
                f"{rank_icon} <b>{m.vendor} {m.model}</b>\n"
                f"   {profit_icon} Прибыль: <b>{profit_str}</b>/день\n"
                f"   💰 Доход: {daily_str} | ⚡ {m.power}Вт\n"
                f"   🔧 {m.hashrate} • 🧮 {m.algorithm}\n"
            )
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 <i>Данные с whattomine.com</i>",
            f"🔄 <i>Обновление каждые 12 часов</i>"
        ])
        
        await message.answer("\n".join(lines), reply_markup=MAIN_MENU)
        
    except Exception as e:
        print(f"Error in menu_top_miners: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка при загрузке данных</b>\n\n"
            "🔧 Попробуйте позже или обратитесь к администратору.",
            reply_markup=MAIN_MENU
        )

@dp.message(F.text == "📈 Аналитика")
async def menu_analytics(message: Message):
    """Обработчик кнопки Аналитика"""
    try:
        user_settings = await get_user_settings(message.from_user.id)
        miners = await get_top(100, user_settings['electricity_tariff'], user_settings['currency'])
        
        if not miners:
            await message.answer(
                "❌ <b>Данные для аналитики недоступны</b>",
                reply_markup=MAIN_MENU
            )
            return
        
        # Простая аналитика
        total_count = len(miners)
        profitable_count = sum(1 for m in miners if getattr(m, 'real_profit', 0) > 0)
        avg_profit = sum(getattr(m, 'real_profit', 0) for m in miners) / total_count if total_count > 0 else 0
        
        # Топ алгоритмы
        algorithms = {}
        for m in miners:
            algo = m.algorithm
            if algo not in algorithms:
                algorithms[algo] = 0
            algorithms[algo] += 1
        
        top_algo = max(algorithms.items(), key=lambda x: x[1]) if algorithms else ("Unknown", 0)
        
        analytics_text = f"""
📊 <b>АНАЛИТИКА РЫНКА ASIC</b>

📈 <b>ОБЩАЯ СТАТИСТИКА:</b>
• 🔢 Всего майнеров: <b>{total_count}</b>
• 🟢 Прибыльных: <b>{profitable_count}</b> ({profitable_count/total_count*100:.1f}%)
• 🔴 Убыточных: <b>{total_count-profitable_count}</b>
• 💰 Средняя прибыль: <b>{format_currency(avg_profit, user_settings['currency'])}/день</b>

🏆 <b>ЛИДИРУЮЩИЙ АЛГОРИТМ:</b>
🥇 <b>{top_algo[0]}</b>: {top_algo[1]} моделей

📊 <b>РЫНОЧНЫЕ ТРЕНДЫ:</b>
• 🔥 SHA-256 остаётся доминирующим
• ⚡ Энергоэффективность растёт
• 💎 Новые модели показывают лучшие результаты
• 🌍 Тарифы на электричество критически важны

🔄 <i>Данные обновляются каждые 12 часов</i>
        """.strip()
        
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
        
        lines = [
            "🇷🇺 <b>ПРОФИТ В РУБЛЯХ</b>",
            f"⚡ Тариф: <b>${tariff:.3f}/кВт⋅ч</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        for idx, m in enumerate(miners[:10], 1):
            try:
                profit = getattr(m, 'real_profit', 0)
                profit_icon = "🟢" if profit > 0 else "🔴"
                daily_str = format_currency(m.daily_usd, 'RUB')
                profit_str = format_currency(profit, 'RUB')
            except:
                profit_icon = "⭐"
                daily_str = f"{m.daily_usd * 98:.0f}₽"  # примерный курс
                profit_str = daily_str
            
            rank_icon = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}️⃣"
            
            lines.append(
                f"{rank_icon} <b>{m.vendor} {m.model}</b>\n"
                f"   {profit_icon} Прибыль: <b>{profit_str}</b>/день\n"
                f"   💰 Доход: {daily_str} | ⚡ {m.power}Вт\n"
            )
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"💱 <i>Курс обновляется автоматически</i>",
            f"📊 <i>Учтен ваш тариф на электричество</i>"
        ])
        
        await message.answer("\n".join(lines), reply_markup=MAIN_MENU)
        
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
        tariff = user_settings['electricity_tariff']
        currency = user_settings['currency']
        
        currency_names = {
            'USD': '🇺🇸 Доллар США',
            'RUB': '🇷🇺 Российский рубль',
            'EUR': '🇪🇺 Евро',
            'CNY': '🇨🇳 Китайский юань'
        }
        
        currency_name = currency_names.get(currency, currency)
        
        settings_text = f"""
⚙️ <b>НАСТРОЙКИ БОТА</b>

💡 <b>ТЕКУЩИЕ ПАРАМЕТРЫ:</b>
• ⚡ Тариф на электричество: <b>${tariff:.3f}/кВт⋅ч</b>
• 💱 Валюта отображения: <b>{currency_name}</b>
• 🌍 Регион: <b>Автоопределение</b>

🎯 <b>ЧТО МОЖНО НАСТРОИТЬ:</b>
• Изменить тариф на электричество
• Выбрать валюту для отображения цен
• Настроить региональные параметры

💡 <b>ПОЧЕМУ ЭТО ВАЖНО:</b>
• 🎯 Точные расчёты прибыльности
• 💰 Учёт ваших локальных условий
• 🚀 Персонализированные рекомендации

🔧 <b>Для изменения используйте команды:</b>
• /settariff - изменить тариф
• /currency - выбрать валюту

📊 <i>Все расчёты будут пересчитаны автоматически</i>
        """.strip()
        
        await message.answer(settings_text, reply_markup=MAIN_MENU)
        
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
• 📊 Учитывайте ваш тариф на электричество
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

❓ Есть вопросы? Используйте ❓ FAQ в меню!
    """
    
    await message.answer(guide_text, reply_markup=MAIN_MENU)

@dp.message(F.text == "ℹ️ О боте")
async def menu_about(message: Message):
    """Обработчик кнопки О боте"""
    about_text = """
ℹ️ <b>О ПРОЕКТЕ ASIC PROFIT BOT</b>

🎯 <b>МИССИЯ</b>
Помочь майнерам принимать обоснованные решения при выборе ASIC-оборудования с учетом реальных условий эксплуатации.

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
🏊 Крупные: Antpool, F2Pool, Poolin. Для начинающих лучше крупные пулы со стабильными выплатами.

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

# Главная функция
async def main():
    print("🚀 Запуск ASIC Profit Bot с данными майнеров...")
    try:
        await init_db()
        await init_user_db()
        start_scheduler()
        await refresh_miners()
        print("✅ Все системы инициализированы!")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 