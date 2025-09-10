"""
💱 API для получения курсов валют от ЦБ РФ
✅ Реальные данные от Центрального банка России
✅ Кеширование для оптимизации запросов
✅ Обработка ошибок и fallback значения
"""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Optional
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class CurrencyAPI:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=1)  # Кеш на 1 час
        
    async def get_usd_rub_rate(self) -> float:
        """
        Получает актуальный курс USD/RUB от ЦБ РФ
        Возвращает курс с кешированием
        """
        cache_key = "USD_RUB"
        now = datetime.now()
        
        # Проверяем кеш
        if (cache_key in self.cache and 
            cache_key in self.cache_expiry and 
            now < self.cache_expiry[cache_key]):
            logger.info(f"💾 Используем кешированный курс USD/RUB: {self.cache[cache_key]}")
            return self.cache[cache_key]
        
        try:
            # Получаем данные от ЦБ РФ
            async with httpx.AsyncClient(timeout=10.0) as client:
                # API ЦБ РФ для получения текущих курсов
                url = "https://www.cbr.ru/scripts/XML_daily.asp"
                response = await client.get(url)
                response.raise_for_status()
                
                # Парсим XML ответ
                root = ET.fromstring(response.content)
                
                # Ищем доллар США (код R01235)
                for valute in root.findall('Valute'):
                    char_code = valute.find('CharCode')
                    if char_code is not None and char_code.text == 'USD':
                        value_element = valute.find('Value')
                        if value_element is not None:
                            # Заменяем запятую на точку для корректного парсинга
                            rate_str = value_element.text.replace(',', '.')
                            rate = float(rate_str)
                            
                            # Сохраняем в кеш
                            self.cache[cache_key] = rate
                            self.cache_expiry[cache_key] = now + self.cache_duration
                            
                            logger.info(f"💱 Получен актуальный курс USD/RUB от ЦБ РФ: {rate}")
                            return rate
                
                # Если доллар не найден, используем fallback
                logger.warning("⚠️ Доллар не найден в ответе ЦБ РФ, используем fallback")
                return self._get_fallback_rate()
                
        except Exception as e:
            logger.error(f"❌ Ошибка при получении курса от ЦБ РФ: {e}")
            return self._get_fallback_rate()
    
    def _get_fallback_rate(self) -> float:
        """
        Возвращает резервный курс USD/RUB на случай недоступности API
        """
        fallback_rate = 78.45  # Актуальный курс на момент создания
        logger.info(f"🔄 Используем резервный курс USD/RUB: {fallback_rate}")
        return fallback_rate
    
    async def convert_usd_to_rub(self, usd_amount: float) -> float:
        """
        Конвертирует сумму из USD в RUB
        """
        rate = await self.get_usd_rub_rate()
        rub_amount = usd_amount * rate
        return round(rub_amount, 2)
    
    async def format_currency_rub(self, usd_amount: float) -> str:
        """
        Форматирует сумму в USD и RUB для отображения
        """
        rub_amount = await self.convert_usd_to_rub(usd_amount)
        rate = await self.get_usd_rub_rate()
        
        return f"${usd_amount:.2f} = {rub_amount:,.0f}₽ (курс: {rate:.2f})"

# Глобальный экземпляр для использования в боте
currency_api = CurrencyAPI()

# Тестовая функция
async def test_currency_api():
    """
    Тестирует работу API курсов валют
    """
    print("🧪 Тестирование Currency API...")
    
    # Тест получения курса
    rate = await currency_api.get_usd_rub_rate()
    print(f"📊 Текущий курс USD/RUB: {rate}")
    
    # Тест конвертации
    test_amounts = [1, 10, 100, 1000]
    for amount in test_amounts:
        rub_amount = await currency_api.convert_usd_to_rub(amount)
        formatted = await currency_api.format_currency_rub(amount)
        print(f"💱 {formatted}")
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    # Запуск тестов
    asyncio.run(test_currency_api()) 