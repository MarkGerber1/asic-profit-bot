from datetime import datetime
from typing import List
import httpx
from bs4 import BeautifulSoup
from models import Miner
from config import WHATTOMINE_URL, DEFAULT_KWH
import re

def fetch_wtm() -> List[Miner]:
    print(">>> Fetching from WhatToMine...")
    resp = httpx.get(WHATTOMINE_URL, timeout=30)
    resp.raise_for_status()
    print(f">>> Response status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, "lxml")
    tables = soup.find_all("table")
    if not tables:
        print(">>> No tables found")
        return []
        
    table = tables[0]  # Берем первую таблицу
    rows = table.select("tbody tr")
    print(f">>> Found {len(rows)} tbody rows")
    
    miners: List[Miner] = []
    for tr in rows:
        cells = tr.find_all("td")
        if len(cells) < 7:
            continue
            
        try:
            # [0]: 'Bitmain Antminer S23 Hyd 3UJan 2026' -> разделяем на vendor + model
            name_raw = cells[0].text.strip()
            # Убираем дату из конца (обычно это год в конце)
            name_clean = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}$', '', name_raw).strip()
            
            parts = name_clean.split(' ', 1)
            vendor = parts[0] if parts else "Unknown"
            model = parts[1] if len(parts) > 1 else name_clean
            
            # [1]: '1.16 Ph/s @ 11020WSHA-256' -> hashrate, power, algo
            hashrate_power_algo = cells[1].text.strip()
            if '@' not in hashrate_power_algo:
                continue
                
            hashrate_part, power_algo_part = hashrate_power_algo.split('@', 1)
            hashrate = hashrate_part.strip()
            
            # Извлекаем power (ищем число + W)
            power_match = re.search(r'(\d+)W', power_algo_part)
            if not power_match:
                continue
            power = int(power_match.group(1))
            
            # Извлекаем алгоритм (все что после числа+W)
            algo_match = re.search(r'\d+W([A-Za-z0-9-]+)', power_algo_part)
            algorithm = algo_match.group(1) if algo_match else "Unknown"
            
            # [3]: '$69.33' -> profit
            profit_str = cells[3].text.strip().replace("$", "").replace(",", "")
            daily_usd = float(profit_str)

            miners.append(
                Miner(
                    model=model,
                    vendor=vendor,
                    hashrate=hashrate,
                    power=power,
                    daily_usd=daily_usd,
                    payback_days=9999,  # WhatToMine не предоставляет payback
                    algorithm=algorithm,
                    cooling="Air",  # По умолчанию
                    scraped_at=datetime.utcnow(),
                )
            )

        except (IndexError, ValueError, AttributeError) as e:
            print(f">>> Error parsing WTM row: {e}")
            continue
    
    print(f">>> Parsed {len(miners)} miners from WhatToMine")
    return miners
