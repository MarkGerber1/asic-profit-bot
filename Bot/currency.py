import httpx
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta

# Курсы валют (кэш)
_currency_cache: Dict[str, float] = {}
_cache_updated: Optional[datetime] = None
CACHE_DURATION = timedelta(hours=1)  # Обновляем курсы каждый час

# Фиксированные курсы на случай проблем с API
FALLBACK_RATES = {
    'RUB': 100.0,  # примерный курс доллара к рублю
    'EUR': 0.85,   # примерный курс евро к доллару
    'CNY': 7.2,    # примерный курс юаня к доллару
}

async def get_exchange_rates() -> Dict[str, float]:
    """Получить актуальные курсы валют"""
    global _currency_cache, _cache_updated
    
    # Проверяем кэш
    if (_cache_updated and 
        datetime.now() - _cache_updated < CACHE_DURATION and 
        _currency_cache):
        return _currency_cache
    
    try:
        # Пробуем получить актуальные курсы с API
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Используем публичный API для курсов валют
            response = await client.get("https://api.exchangerate-api.com/v4/latest/USD")
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # Обновляем кэш
                _currency_cache = {
                    'USD': 1.0,  # базовая валюта
                    'RUB': rates.get('RUB', FALLBACK_RATES['RUB']),
                    'EUR': rates.get('EUR', FALLBACK_RATES['EUR']),
                    'CNY': rates.get('CNY', FALLBACK_RATES['CNY']),
                }
                _cache_updated = datetime.now()
                print(f">>> Currency rates updated: {_currency_cache}")
                return _currency_cache
                
    except Exception as e:
        print(f">>> Failed to fetch currency rates: {e}")
    
    # Если не удалось получить курсы, используем резервные
    if not _currency_cache:
        _currency_cache = {'USD': 1.0, **FALLBACK_RATES}
        _cache_updated = datetime.now()
        print(f">>> Using fallback currency rates: {_currency_cache}")
    
    return _currency_cache

async def convert_currency(amount: float, from_currency: str = 'USD', to_currency: str = 'RUB') -> float:
    """Конвертировать валюту"""
    if from_currency == to_currency:
        return amount
        
    rates = await get_exchange_rates()
    
    # Конвертируем в доллары (базовая валюта)
    if from_currency != 'USD':
        amount = amount / rates.get(from_currency, 1.0)
    
    # Конвертируем в целевую валюту
    if to_currency != 'USD':
        amount = amount * rates.get(to_currency, 1.0)
    
    return amount

def format_currency(amount: float, currency: str) -> str:
    """Форматировать валюту для отображения"""
    currency_symbols = {
        'USD': '$',
        'RUB': '₽',
        'EUR': '€',
        'CNY': '¥'
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    if currency == 'RUB':
        return f"{amount:.0f}{symbol}"  # Рубли без копеек
    else:
        return f"{symbol}{amount:.2f}"

def get_supported_currencies() -> Dict[str, str]:
    """Получить список поддерживаемых валют"""
    return {
        'USD': '🇺🇸 Доллар США',
        'RUB': '🇷🇺 Российский рубль', 
        'EUR': '🇪🇺 Евро',
        'CNY': '🇨🇳 Китайский юань'
    } 