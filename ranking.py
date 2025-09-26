from datetime import datetime, timedelta
from typing import List
import aiosqlite
from scrapers.asicminervalue import fetch_asicminervalue
from scrapers.whattomine import fetch_wtm
from models import Miner
from config import REFRESH_HOURS, DEFAULT_KWH
from currency import convert_currency, format_currency

DB_FILE = "bot_cache.db"

async def init_db():
    try:
        print(">>> Connecting to database...")
        db = await aiosqlite.connect(DB_FILE)
        print(">>> Creating table...")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS miners (
                vendor TEXT,
                model TEXT,
                hashrate TEXT,
                power INTEGER,
                daily_usd REAL,
                payback_days REAL,
                algorithm TEXT,
                cooling TEXT,
                scraped_at TIMESTAMP,
                UNIQUE(vendor, model)
            )
            """
        )
        await db.commit()
        await db.close()
        print(">>> Database initialized successfully")
    except Exception as e:
        print(f">>> Database error: {e}")
        raise

async def refresh_miners():
    print(">>> Starting refresh_miners")
    miners = fetch_asicminervalue()
    print(f">>> AsicMinerValue returned {len(miners)} miners")
    
    wtm_miners = fetch_wtm()
    print(f">>> WhatToMine returned {len(wtm_miners)} miners")
    
    miners.extend(wtm_miners)
    print(f">>> Total miners before dedup: {len(miners)}")
    
    unique = {(m.vendor, m.model): m for m in miners}
    print(f">>> Unique miners after dedup: {len(unique)}")
    
    # Создаём прямое подключение вместо использования _get_db()
    db = await aiosqlite.connect(DB_FILE)
    try:
        await db.executemany(
            """
            INSERT OR REPLACE INTO miners
            (vendor, model, hashrate, power, daily_usd, payback_days,
             algorithm, cooling, scraped_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            [
                (
                    m.vendor,
                    m.model,
                    m.hashrate,
                    m.power,
                    m.daily_usd,
                    m.payback_days,
                    m.algorithm,
                    m.cooling,
                    m.scraped_at,
                )
                for m in unique.values()
            ],
        )
        await db.commit()
        print(f">>> Successfully saved {len(unique)} miners to database")
    except Exception as e:
        print(f">>> Database error: {e}")
    finally:
        await db.close()

async def get_top(n: int = 15, user_tariff: float = DEFAULT_KWH, user_currency: str = 'USD') -> List[Miner]:
    """Получить топ майнеров с учетом индивидуального тарифа и валюты"""
    db = await aiosqlite.connect(DB_FILE)
    try:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM miners
            WHERE scraped_at > ?
            ORDER BY daily_usd DESC
            LIMIT 100
            """,
            (datetime.utcnow() - timedelta(hours=REFRESH_HOURS + 1),),
        ) as cur:
            rows = await cur.fetchall()
        
        # Создаем майнеров с расчетами
        enhanced_miners = []
        for row in rows:
            # Стоимость электричества в день (USD)
            daily_electricity_cost = user_tariff * row['power'] * 24 / 1000
            # Реальная прибыль
            real_profit_usd = row['daily_usd'] - daily_electricity_cost
            
            # Конвертируем в валюту пользователя если нужно
            if user_currency != 'USD':
                real_profit = await convert_currency(real_profit_usd, 'USD', user_currency)
                daily_revenue = await convert_currency(row['daily_usd'], 'USD', user_currency)
                electricity_cost_converted = await convert_currency(daily_electricity_cost, 'USD', user_currency)
            else:
                real_profit = real_profit_usd
                daily_revenue = row['daily_usd']
                electricity_cost_converted = daily_electricity_cost
            
            # Создаем объект майнера с полными данными
            miner = Miner(
                model=row['model'],
                vendor=row['vendor'],
                hashrate=row['hashrate'],
                power=row['power'],
                daily_usd=daily_revenue,  # В валюте пользователя
                payback_days=row['payback_days'],
                algorithm=row['algorithm'],
                cooling=row['cooling'],
                scraped_at=row['scraped_at'],
                real_profit=real_profit,
                electricity_cost=electricity_cost_converted,
                user_currency=user_currency
            )
            
            enhanced_miners.append(miner)
        
        # Сортируем по реальной прибыли (убывание)
        enhanced_miners.sort(key=lambda x: x.real_profit, reverse=True)
        
        return enhanced_miners[:n]
    finally:
        await db.close()

async def get_miner_by_model(model: str, user_tariff: float = DEFAULT_KWH, user_currency: str = 'USD') -> Miner:
    """Получить конкретный майнер по модели"""
    miners = await get_top(100, user_tariff, user_currency)
    return next((m for m in miners if m.model == model), None)
