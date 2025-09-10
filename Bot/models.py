from dataclasses import dataclass, field
from datetime import datetime
from config import DEFAULT_KWH
from typing import Optional

@dataclass
class Miner:
    model: str
    vendor: str
    hashrate: str
    power: int
    daily_usd: float
    payback_days: float
    algorithm: str
    cooling: str
    scraped_at: datetime
    
    # Дополнительные поля для персонализации
    real_profit: Optional[float] = field(default=None)
    electricity_cost: Optional[float] = field(default=None)
    user_currency: Optional[str] = field(default='USD')

    @property
    def profit_per_kwh(self) -> float:
        kwh_per_day = self.power * 24 / 1000
        return (self.daily_usd - DEFAULT_KWH * kwh_per_day) / kwh_per_day
