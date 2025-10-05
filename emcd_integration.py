"""
Интеграция с EMCD.io для получения данных о прибыльности ASIC майнеров
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import re
from datetime import datetime, timedelta


@dataclass
class EMCDMinerData:
    """Данные майнера из EMCD.io"""
    model: str
    algorithm: str
    hashrate: float
    hashrate_unit: str
    power_w: int
    profitability_usd_day: float
    profitability_rub_day: float
    electricity_cost_usd_day: float
    electricity_cost_rub_day: float
    net_profit_usd_day: float
    net_profit_rub_day: float
    electricity_price_usd: float
    electricity_price_rub: float
    last_updated: datetime


class EMCDClient:
    """Клиент для работы с EMCD.io"""

    BASE_URL = "https://emcd.io"
    TIMEOUT = 30

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=self.TIMEOUT,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_miners_data(self, electricity_price_rub: float = 5.0) -> List[EMCDMinerData]:
        """
        Получить данные о майнерах с EMCD.io
        electricity_price_rub: цена электричества в руб/кВт⋅ч
        """
        try:
            # EMCD использует динамическую загрузку данных через JavaScript
            # Попробуем получить данные напрямую или через альтернативные методы

            # Для начала попробуем основной endpoint
            url = f"{self.BASE_URL}/"
            response = await self.client.get(url)

            if response.status_code != 200:
                print(f"EMCD.io недоступен: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Ищем данные в HTML или JSON
            miners_data = []

            # Ищем скрипты с данными
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'miners' in script.string.lower():
                    # Пытаемся извлечь данные из JavaScript
                    data = self._extract_data_from_script(script.string)
                    if data:
                        miners_data.extend(data)
                        break

            # Если не нашли в скриптах, пробуем альтернативные методы
            if not miners_data:
                miners_data = await self._scrape_miners_table(soup, electricity_price_rub)

            return miners_data

        except Exception as e:
            print(f"Ошибка при получении данных EMCD.io: {e}")
            return []

    def _extract_data_from_script(self, script_content: str) -> List[EMCDMinerData]:
        """Извлечь данные из JavaScript кода"""
        miners_data = []

        try:
            # Ищем JSON данные в скрипте
            json_match = re.search(r'var\s+miners\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
            if json_match:
                miners_json = json_match.group(1)
                miners_list = json.loads(miners_json)

                for miner in miners_list:
                    try:
                        miner_data = EMCDMinerData(
                            model=miner.get('model', ''),
                            algorithm=miner.get('algorithm', ''),
                            hashrate=miner.get('hashrate', 0),
                            hashrate_unit=miner.get('hashrate_unit', 'H/s'),
                            power_w=miner.get('power', 0),
                            profitability_usd_day=miner.get('profit_usd', 0),
                            profitability_rub_day=miner.get('profit_rub', 0),
                            electricity_cost_usd_day=miner.get('electricity_usd', 0),
                            electricity_cost_rub_day=miner.get('electricity_rub', 0),
                            net_profit_usd_day=miner.get('net_profit_usd', 0),
                            net_profit_rub_day=miner.get('net_profit_rub', 0),
                            electricity_price_usd=miner.get('electricity_price_usd', 0),
                            electricity_price_rub=miner.get('electricity_price_rub', 5.0),
                            last_updated=datetime.now()
                        )
                        miners_data.append(miner_data)
                    except Exception as e:
                        print(f"Ошибка обработки майнера: {e}")
                        continue

        except Exception as e:
            print(f"Ошибка парсинга JSON: {e}")

        return miners_data

    async def _scrape_miners_table(self, soup: BeautifulSoup, electricity_price_rub: float) -> List[EMCDMinerData]:
        """Скрапинг таблицы майнеров"""
        miners_data = []

        try:
            # Ищем таблицу с майнерами
            table = soup.find('table', {'class': re.compile(r'.*miner.*', re.I)})
            if not table:
                # Ищем по другим селекторам
                table = soup.find('table')

            if table:
                rows = table.find_all('tr')[1:]  # Пропускаем заголовок

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:  # Минимум колонок для данных
                        try:
                            # Извлекаем данные из колонок
                            model = cols[0].get_text(strip=True)
                            hashrate_text = cols[1].get_text(strip=True)
                            power_text = cols[2].get_text(strip=True)
                            profit_text = cols[3].get_text(strip=True)

                            # Парсим хешрейт
                            hashrate, hashrate_unit = self._parse_hashrate(hashrate_text)

                            # Парсим мощность
                            power_w = self._parse_power(power_text)

                            # Парсим прибыль
                            profitability_rub_day = self._parse_profit(profit_text)

                            # Рассчитываем остальные значения
                            electricity_cost_rub_day = (power_w / 1000) * 24 * electricity_price_rub
                            electricity_price_usd = electricity_price_rub / 85  # Примерный курс
                            electricity_cost_usd_day = electricity_cost_rub_day / 85
                            net_profit_rub_day = profitability_rub_day - electricity_cost_rub_day
                            net_profit_usd_day = net_profit_rub_day / 85

                            miner_data = EMCDMinerData(
                                model=model,
                                algorithm="SHA-256",  # По умолчанию, можно определить по модели
                                hashrate=hashrate,
                                hashrate_unit=hashrate_unit,
                                power_w=power_w,
                                profitability_usd_day=profitability_rub_day / 85,
                                profitability_rub_day=profitability_rub_day,
                                electricity_cost_usd_day=electricity_cost_usd_day,
                                electricity_cost_rub_day=electricity_cost_rub_day,
                                net_profit_usd_day=net_profit_usd_day,
                                net_profit_rub_day=net_profit_rub_day,
                                electricity_price_usd=electricity_price_usd,
                                electricity_price_rub=electricity_price_rub,
                                last_updated=datetime.now()
                            )
                            miners_data.append(miner_data)

                        except Exception as e:
                            print(f"Ошибка обработки строки таблицы: {e}")
                            continue

        except Exception as e:
            print(f"Ошибка скрапинга таблицы: {e}")

        return miners_data

    def _parse_hashrate(self, text: str) -> Tuple[float, str]:
        """Парсинг хешрейта (например: '100 TH/s' -> (100, 'TH/s'))"""
        match = re.search(r'([\d.]+)\s*(H|KH|MH|GH|TH|PH|EH)/s', text, re.I)
        if match:
            value = float(match.group(1))
            unit = match.group(2).upper() + '/s'
            return value, unit
        return 0, 'H/s'

    def _parse_power(self, text: str) -> int:
        """Парсинг мощности (например: '3000 W' -> 3000)"""
        match = re.search(r'(\d+)\s*W', text, re.I)
        return int(match.group(1)) if match else 0

    def _parse_profit(self, text: str) -> float:
        """Парсинг прибыли (например: '15.5 ₽' -> 15.5)"""
        # Удаляем символы валюты и пробелы
        clean_text = re.sub(r'[₽$€£¥\s]', '', text)
        try:
            return float(clean_text)
        except ValueError:
            return 0.0

    async def get_electricity_price_suggestions(self) -> List[float]:
        """Получить предложения по ценам на электричество"""
        # Стандартные цены для разных регионов России
        return [0, 1, 2, 3, 4, 5, 6, 7, 8, 10]

    async def update_miners_cache(self) -> Dict[str, EMCDMinerData]:
        """Обновить кеш данных майнеров"""
        cache = {}
        electricity_prices = await self.get_electricity_price_suggestions()

        for price in electricity_prices:
            miners = await self.get_miners_data(price)
            for miner in miners:
                key = f"{miner.model}_{price}"
                cache[key] = miner

        return cache


# Глобальный кеш данных EMCD
EMCD_CACHE: Dict[str, EMCDMinerData] = {}
EMCD_CACHE_TIMESTAMP: Optional[datetime] = None
CACHE_TTL_MINUTES = 30


async def get_emcd_data(model: str, electricity_price_rub: float = 5.0) -> Optional[EMCDMinerData]:
    """Получить данные майнера из EMCD с кешированием"""
    global EMCD_CACHE, EMCD_CACHE_TIMESTAMP

    # Проверяем актуальность кеша
    now = datetime.now()
    if EMCD_CACHE_TIMESTAMP and (now - EMCD_CACHE_TIMESTAMP) < timedelta(minutes=CACHE_TTL_MINUTES):
        cache_key = f"{model}_{electricity_price_rub}"
        return EMCD_CACHE.get(cache_key)

    # Обновляем кеш
    async with EMCDClient() as client:
        try:
            miners_data = await client.get_miners_data(electricity_price_rub)
            EMCD_CACHE.clear()

            for miner in miners_data:
                key = f"{miner.model}_{electricity_price_rub}"
                EMCD_CACHE[key] = miner

            EMCD_CACHE_TIMESTAMP = now

            cache_key = f"{model}_{electricity_price_rub}"
            return EMCD_CACHE.get(cache_key)

        except Exception as e:
            print(f"Ошибка получения данных EMCD: {e}")
            return None


async def get_all_emcd_miners(electricity_price_rub: float = 5.0) -> List[EMCDMinerData]:
    """Получить все доступные майнеры из EMCD"""
    async with EMCDClient() as client:
        return await client.get_miners_data(electricity_price_rub)


# Функции для совместимости с существующим кодом
async def get_miner_profitability(model: str, electricity_price_rub: float = 5.0) -> Optional[Dict]:
    """Получить прибыльность майнера (для совместимости)"""
    data = await get_emcd_data(model, electricity_price_rub)
    if data:
        return {
            'profit_rub_day': data.net_profit_rub_day,
            'profit_usd_day': data.net_profit_usd_day,
            'electricity_cost_rub_day': data.electricity_cost_rub_day,
            'electricity_cost_usd_day': data.electricity_cost_usd_day,
            'hashrate': data.hashrate,
            'hashrate_unit': data.hashrate_unit,
            'power_w': data.power_w
        }
    return None
