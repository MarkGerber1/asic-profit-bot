import re
from datetime import datetime
from typing import List
import httpx
from bs4 import BeautifulSoup
from models import Miner
from config import ASICMINERVALUE_URL

CLEAN_REGEX = re.compile(r"[^\d.]")

def _text_to_int(txt: str) -> int:
    cleaned = CLEAN_REGEX.sub("", txt)
    if not cleaned:
        return 0
    try:
        # Сначала преобразуем в float, затем в int (для обработки десятичных чисел)
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0

def _parse_hashrate(raw: str) -> str:
    return raw.strip()

def fetch_asicminervalue() -> List[Miner]:
    print(">>> AsicMinerValue: DISABLED (no profit data available)")
    # Сайт изменил структуру и больше не предоставляет данные о прибыли
    # Все поля profit содержат только '.../day' без числовых значений
    return []
