from textwrap import dedent
from models import Miner
from config import DEFAULT_KWH
from currency import format_currency
from typing import List

def build_ranking_message(miners: List[Miner], user_currency: str = 'USD', user_tariff: float = DEFAULT_KWH) -> str:
    """Красивое сообщение с топом майнеров"""
    
    lines = [
        "🏆 <b>ТОП ПРИБЫЛЬНЫХ МАЙНЕРОВ</b>",
        f"💱 Валюта: <b>{user_currency}</b> | ⚡ Тариф: <b>{format_currency(user_tariff, user_currency)}/кВт⋅ч</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for idx, m in enumerate(miners, 1):
        # Определяем иконку прибыльности
        if hasattr(m, 'real_profit') and m.real_profit is not None:
            if m.real_profit > 50:
                profit_icon = "🟢💎"
            elif m.real_profit > 20:
                profit_icon = "🟢"
            elif m.real_profit > 0:
                profit_icon = "🟡"
            else:
                profit_icon = "🔴"
                
            revenue_str = format_currency(m.daily_usd, user_currency)
            profit_str = format_currency(m.real_profit, user_currency)
            electricity_str = format_currency(getattr(m, 'electricity_cost', 0), user_currency)
        else:
            profit_icon = "⭐"
            revenue_str = format_currency(m.daily_usd, user_currency)
            profit_str = "N/A"
            electricity_str = "N/A"
        
        # Иконка для топ-3
        rank_icon = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}️⃣"
        
        lines.append(
            f"{rank_icon} <b>{m.vendor} {m.model}</b>\n"
            f"   {profit_icon} Прибыль: <b>{profit_str}</b>/день\n"
            f"   💰 Доход: {revenue_str} | 🔌 Расход: {electricity_str}\n"
            f"   ⚡ {m.power}Вт • 🔧 {m.hashrate} • 🧮 {m.algorithm}\n"
        )
    
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 <i>Данные с whattomine.com</i>",
        f"🔄 <i>Обновление каждые 12 часов</i>"
    ])
    
    return "\n".join(lines)

def build_deep_dive(m: Miner) -> str:
    """Подробный гайд по майнеру с красивыми иконками"""
    user_currency = getattr(m, 'user_currency', 'USD')
    real_profit = getattr(m, 'real_profit', m.daily_usd)
    electricity_cost = getattr(m, 'electricity_cost', 0)
    
    revenue_str = format_currency(m.daily_usd, user_currency)
    profit_str = format_currency(real_profit, user_currency)
    electricity_str = format_currency(electricity_cost, user_currency)
    
    # Статус прибыльности
    if real_profit > 50:
        status_icon = "🟢💎 ОЧЕНЬ ПРИБЫЛЬНЫЙ"
    elif real_profit > 20:
        status_icon = "🟢 ПРИБЫЛЬНЫЙ"
    elif real_profit > 0:
        status_icon = "🟡 УМЕРЕННО ПРИБЫЛЬНЫЙ"
    else:
        status_icon = "🔴 УБЫТОЧНЫЙ"
    
    # Рентабельность
    if electricity_cost > 0:
        profitability = (real_profit / electricity_cost) * 100
        profitability_str = f"{profitability:+.1f}%"
        profitability_icon = "📈" if profitability > 50 else "📊" if profitability > 0 else "📉"
    else:
        profitability_str = "∞"
        profitability_icon = "🚀"
    
    # Приблизительная окупаемость
    if real_profit > 0:
        avg_price_usd = 4000
        if user_currency == 'RUB':
            avg_price = avg_price_usd * 100
        elif user_currency == 'EUR':
            avg_price = avg_price_usd * 0.85
        else:
            avg_price = avg_price_usd
        
        payback_days = avg_price / real_profit if real_profit > 0 else 9999
        payback_str = f"{payback_days:.0f} дней" if payback_days < 1000 else "∞"
        payback_icon = "⚡" if payback_days < 200 else "🐌" if payback_days < 500 else "❌"
    else:
        payback_str = "Убыточно"
        payback_icon = "❌"
    
    guide = dedent(f"""
        🔧 <b>ПОДРОБНЫЙ АНАЛИЗ: {m.vendor} {m.model}</b>
        
        {status_icon}
        
        💰 <b>ЭКОНОМИКА МАЙНИНГА</b>
        • 💵 Доход: <b>{revenue_str}</b>/день
        • ⚡ Электричество: <b>{electricity_str}</b>/день  
        • 💎 <b>Чистая прибыль: {profit_str}/день</b>
        • {profitability_icon} Рентабельность: <b>{profitability_str}</b>
        • {payback_icon} Окупаемость: <b>~{payback_str}</b>
        
        🔌 <b>ЭЛЕКТРИЧЕСТВО И ПИТАНИЕ</b>
        • ⚡ Потребление: <b>{m.power} Вт</b>
        • 🔧 При 220В: <b>{m.power/220:.1f} А</b>
        • 🛡️ Рекомендуемый автомат: <b>{max(16, round(m.power/220*1.25/5)*5)} А</b>
        • 🔌 Сечение кабеля: <b>2.5-4 мм²</b>
        
        🌪️ <b>ОХЛАЖДЕНИЕ</b>
        • 🧊 Тип: <b>{m.cooling}</b>
        • 💨 Воздушный поток: <b>~{m.power//3} м³/ч</b>  
        • 🌡️ Температура: <b>≤30°C на входе</b>
        • 💧 Влажность: <b>≤65% RH</b>
        • 🧹 Чистка фильтров: <b>каждые 2 недели</b>
        
        🏠 <b>РАЗМЕЩЕНИЕ</b>
        • 🔇 Отдельное помещение (шум ~75 дБ)
        • 🌪️ Приточно-вытяжная вентиляция
        • 🚨 Дымовой извещатель обязателен
        • ⚡ Заземление и УЗО
        
        ⚙️ <b>НАСТРОЙКА</b>
        1. 🌐 Подключение к сети, поиск IP
        2. 💻 Веб-интерфейс: обычно root/admin
        3. ⛏️ Настройка пула майнинга
        4. 🔄 Обновление прошивки
        5. 📊 Мониторинг температуры
        
        📊 <b>ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ</b>
        • 🚀 Хешрейт: <b>{m.hashrate}</b>
        • 🧮 Алгоритм: <b>{m.algorithm}</b>
        • ⚡ Энергоэффективность: <b>~{m.power/100:.1f} Вт/Th</b>
        
        📚 <b>ПОЛЕЗНЫЕ ССЫЛКИ</b>
        • 📖 Инструкция: Google "{m.vendor} {m.model} manual"
        • 🔧 Альтернативные прошивки: HiveOS, Braiins OS
        • 🧮 Калькуляторы: WhatToMine, NiceHash
        • 🛒 Магазины: AliExpress, Amazon
        """).strip()
    
    return guide

def build_compare_message(miner1: Miner, miner2: Miner) -> str:
    """Красивое сравнение двух майнеров"""
    user_currency = getattr(miner1, 'user_currency', 'USD')
    
    # Получаем данные для сравнения
    profit1 = getattr(miner1, 'real_profit', miner1.daily_usd)
    profit2 = getattr(miner2, 'real_profit', miner2.daily_usd)
    
    # Определяем победителя
    if profit1 > profit2:
        winner1_profit = "🏆"
        winner2_profit = "🥈"
        winner_text = f"🎯 <b>Рекомендация:</b> {miner1.vendor} {miner1.model}"
    elif profit2 > profit1:
        winner1_profit = "🥈"
        winner2_profit = "🏆"
        winner_text = f"🎯 <b>Рекомендация:</b> {miner2.vendor} {miner2.model}"
    else:
        winner1_profit = "🤝"
        winner2_profit = "🤝"
        winner_text = "🤝 <b>Оба майнера показывают одинаковую прибыльность</b>"
    
    # Сравнение по энергопотреблению
    power_winner1 = "🏆⚡" if miner1.power < miner2.power else "❌"
    power_winner2 = "🏆⚡" if miner2.power < miner1.power else "❌"
    
    return dedent(f"""
        ⚔️ <b>СРАВНЕНИЕ МАЙНЕРОВ</b>
        
        <b>🆚 {miner1.vendor} {miner1.model} VS {miner2.vendor} {miner2.model}</b>
        
        💰 <b>ПРИБЫЛЬНОСТЬ:</b>
        • {miner1.model}: <b>{format_currency(profit1, user_currency)}/день</b> {winner1_profit}
        • {miner2.model}: <b>{format_currency(profit2, user_currency)}/день</b> {winner2_profit}
        
        ⚡ <b>ЭНЕРГОПОТРЕБЛЕНИЕ:</b>
        • {miner1.model}: <b>{miner1.power} Вт</b> {power_winner1}
        • {miner2.model}: <b>{miner2.power} Вт</b> {power_winner2}
        
        🚀 <b>ХЕШРЕЙТ:</b>
        • {miner1.model}: <b>{miner1.hashrate}</b>
        • {miner2.model}: <b>{miner2.hashrate}</b>
        
        🧮 <b>АЛГОРИТМ:</b>
        • {miner1.model}: <b>{miner1.algorithm}</b>
        • {miner2.model}: <b>{miner2.algorithm}</b>
        
        {winner_text}
        
        📊 <i>Расчёт основан на ваших индивидуальных настройках</i>
    """).strip()

def build_help_message() -> str:
    """Красивое сообщение со списком всех команд"""
    return dedent("""
        📜 <b>СПИСОК КОМАНД БОТА</b>
        
        🏆 /top — Топ-10 самых прибыльных майнеров
        💰 /market — Аналитика и тренды рынка ASIC
        ⚙️ /settings — Настройки тарифа, региона и валюты
        🆚 /compare — Сравнить два майнера
        ⭐ /favorites — Ваши избранные майнеры
        💡 /mytariff — Ваши текущие настройки
        🔧 /settariff — Установить тариф на электричество
        💱 /currency — Выбрать валюту отображения
        📜 /help — Справка и список команд
        
        🎯 <b>БЫСТРЫЕ ДЕЙСТВИЯ:</b>
        • Нажимайте на майнеры для подробной информации
        • Используйте кнопки для быстрой навигации
        • Добавляйте интересные модели в избранное
        
        💬 <b>ПОДДЕРЖКА:</b>
        • Бот обновляется каждые 12 часов
        • Данные собираются с надёжных источников
        • Все расчёты учитывают ваш индивидуальный тариф
        
        🚀 <i>Начните с /settings для персонализации результатов!</i>
    """).strip()

def build_market_message(miners: List[Miner], user_currency: str = 'USD') -> str:
    """Аналитика рынка майнеров"""
    if not miners:
        return "❌ Данные временно недоступны"
    
    # Статистика
    profitable_count = sum(1 for m in miners if getattr(m, 'real_profit', 0) > 0)
    total_count = len(miners)
    avg_profit = sum(getattr(m, 'real_profit', 0) for m in miners) / total_count if total_count > 0 else 0
    
    # Топ алгоритмы
    algorithms = {}
    for m in miners:
        algo = m.algorithm
        if algo not in algorithms:
            algorithms[algo] = {'count': 0, 'avg_profit': 0, 'total_profit': 0}
        algorithms[algo]['count'] += 1
        algorithms[algo]['total_profit'] += getattr(m, 'real_profit', 0)
    
    for algo in algorithms:
        algorithms[algo]['avg_profit'] = algorithms[algo]['total_profit'] / algorithms[algo]['count']
    
    # Сортируем по средней прибыльности
    top_algos = sorted(algorithms.items(), key=lambda x: x[1]['avg_profit'], reverse=True)[:5]
    
    algo_lines = []
    for i, (algo, data) in enumerate(top_algos, 1):
        icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        avg_profit_str = format_currency(data['avg_profit'], user_currency)
        algo_lines.append(f"{icon} <b>{algo}</b>: {avg_profit_str}/день ({data['count']} моделей)")
    
    return dedent(f"""
        📊 <b>АНАЛИТИКА РЫНКА ASIC</b>
        
        📈 <b>ОБЩАЯ СТАТИСТИКА:</b>
        • 🔢 Всего майнеров: <b>{total_count}</b>
        • 🟢 Прибыльных: <b>{profitable_count}</b> ({profitable_count/total_count*100:.1f}%)
        • 🔴 Убыточных: <b>{total_count-profitable_count}</b>
        • 💰 Средняя прибыль: <b>{format_currency(avg_profit, user_currency)}/день</b>
        
        🏆 <b>ТОП АЛГОРИТМЫ ПО ПРИБЫЛЬНОСТИ:</b>
        {chr(10).join(algo_lines)}
        
        📊 <b>РЫНОЧНЫЕ ТРЕНДЫ:</b>
        • 🔥 SHA-256 остаётся доминирующим
        • ⚡ Энергоэффективность растёт
        • 💎 Новые модели показывают лучшие результаты
        • 🌍 Тарифы на электричество критически важны
        
        💡 <b>СОВЕТЫ ДЛЯ ИНВЕСТОРОВ:</b>
        • 🎯 Фокус на энергоэффективные модели
        • 📍 Учитывайте местные тарифы на электричество
        • 🔄 Следите за обновлениями прошивки
        • ⚖️ Диверсифицируйте по алгоритмам
        
        🔄 <i>Данные обновляются каждые 12 часов</i>
    """).strip()

def build_settings_message(user_settings: dict) -> str:
    """Красивое меню настроек"""
    tariff = user_settings['electricity_tariff']
    currency = user_settings['currency']
    
    currency_names = {
        'USD': '🇺🇸 Доллар США',
        'RUB': '🇷🇺 Российский рубль',
        'EUR': '🇪🇺 Евро',
        'CNY': '🇨🇳 Китайский юань'
    }
    
    currency_name = currency_names.get(currency, currency)
    
    return dedent(f"""
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
        
        📊 <i>Все расчёты будут пересчитаны автоматически</i>
    """).strip()
