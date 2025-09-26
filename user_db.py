import aiosqlite
from datetime import datetime
from typing import Optional

USER_DB_FILE = "users.db"

async def init_user_db():
    """Инициализация базы данных пользователей"""
    db = await aiosqlite.connect(USER_DB_FILE)
    try:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                electricity_tariff REAL DEFAULT 0.10,
                currency TEXT DEFAULT 'USD',
                timezone TEXT DEFAULT 'UTC',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vendor TEXT,
                model TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, vendor, model)
            )
            """
        )
        
        await db.commit()
        print(">>> User database initialized successfully")
    except Exception as e:
        print(f">>> User database error: {e}")
        raise
    finally:
        await db.close()

async def get_user_settings(user_id: int) -> dict:
    """Получить настройки пользователя"""
    db = await aiosqlite.connect(USER_DB_FILE)
    try:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            
        if row:
            return dict(row)
        else:
            # Создаём пользователя с настройками по умолчанию
            await db.execute(
                """
                INSERT OR IGNORE INTO users (user_id, electricity_tariff, currency)
                VALUES (?, 0.10, 'USD')
                """,
                (user_id,)
            )
            await db.commit()
            return {
                'user_id': user_id,
                'electricity_tariff': 0.10,
                'currency': 'USD',
                'timezone': 'UTC'
            }
    finally:
        await db.close()

async def update_user_tariff(user_id: int, tariff: float):
    """Обновить тариф пользователя"""
    db = await aiosqlite.connect(USER_DB_FILE)
    try:
        await db.execute(
            """
            INSERT OR REPLACE INTO users (user_id, electricity_tariff, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, tariff)
        )
        await db.commit()
    finally:
        await db.close()

async def update_user_currency(user_id: int, currency: str):
    """Обновить валюту пользователя"""
    db = await aiosqlite.connect(USER_DB_FILE)
    try:
        await db.execute(
            """
            INSERT OR REPLACE INTO users (user_id, currency, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, currency)
        )
        await db.commit()
    finally:
        await db.close()

async def add_favorite_miner(user_id: int, vendor: str, model: str):
    """Добавить майнер в избранное"""
    db = await aiosqlite.connect(USER_DB_FILE)
    try:
        await db.execute(
            """
            INSERT OR IGNORE INTO user_favorites (user_id, vendor, model)
            VALUES (?, ?, ?)
            """,
            (user_id, vendor, model)
        )
        await db.commit()
        return True
    except Exception:
        return False
    finally:
        await db.close()

async def remove_favorite_miner(user_id: int, vendor: str, model: str):
    """Удалить майнер из избранного"""
    db = await aiosqlite.connect(USER_DB_FILE)
    try:
        await db.execute(
            """
            DELETE FROM user_favorites 
            WHERE user_id = ? AND vendor = ? AND model = ?
            """,
            (user_id, vendor, model)
        )
        await db.commit()
        return True
    except Exception:
        return False
    finally:
        await db.close()

async def get_user_favorites(user_id: int) -> list:
    """Получить избранные майнеры пользователя"""
    db = await aiosqlite.connect(USER_DB_FILE)
    try:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT vendor, model FROM user_favorites 
            WHERE user_id = ? ORDER BY added_at DESC
            """,
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close() 