"""
База данных ASIC майнеров с актуальными ценами (2024-2025)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class EquipmentCategory(Enum):
    TOP = "🏆 ТОП"
    MID = "⭐ СРЕДНИЕ"
    BUDGET = "💰 БЮДЖЕТНЫЕ"


@dataclass
class ASICMiner:
    """ASIC майнер с характеристиками и ценами"""
    model: str
    vendor: str
    algorithm: str
    hashrate_value: float
    hashrate_unit: str  # TH/s, GH/s, MH/s
    power_w: int
    efficiency: float  # W/TH для SHA-256, или соответствующие единицы
    price_used_rub: int
    price_new_rub: int
    price_used_usd: int
    price_new_usd: int
    category: EquipmentCategory
    release_year: int
    notes: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.vendor} {self.model}"

    @property
    def hashrate_display(self) -> str:
        return f"{self.hashrate_value} {self.hashrate_unit}"

    def get_price_rub(self, is_used: bool = True) -> int:
        return self.price_used_rub if is_used else self.price_new_rub

    def get_price_usd(self, is_used: bool = True) -> int:
        return self.price_used_usd if is_used else self.price_new_usd


# База данных ASIC майнеров
ASIC_MINERS = [
    # ТОП ФЛАГМАНЫ
    ASICMiner(
        model="S21 XP Hyd", vendor="Bitmain Antminer",
        algorithm="SHA-256", hashrate_value=473, hashrate_unit="TH/s",
        power_w=5676, efficiency=12.0,
        price_used_rub=650000, price_new_rub=1100000,
        price_used_usd=8500, price_new_usd=14000,
        category=EquipmentCategory.TOP, release_year=2024
    ),
    ASICMiner(
        model="S23 Hyd 3U", vendor="Bitmain Antminer",
        algorithm="SHA-256", hashrate_value=615, hashrate_unit="TH/s",
        power_w=11020, efficiency=17.9,
        price_used_rub=950000, price_new_rub=1450000,
        price_used_usd=12000, price_new_usd=18500,
        category=EquipmentCategory.TOP, release_year=2024
    ),
    ASICMiner(
        model="L9", vendor="Bitmain Antminer",
        algorithm="Scrypt", hashrate_value=16, hashrate_unit="GH/s",
        power_w=3360, efficiency=210.0,
        price_used_rub=700000, price_new_rub=1050000,
        price_used_usd=9000, price_new_usd=13500,
        category=EquipmentCategory.TOP, release_year=2024
    ),
    ASICMiner(
        model="KS5L", vendor="IceRiver",
        algorithm="KHeavyHash", hashrate_value=15, hashrate_unit="TH/s",
        power_w=3400, efficiency=226.7,
        price_used_rub=1400000, price_new_rub=2200000,
        price_used_usd=18000, price_new_usd=28000,
        category=EquipmentCategory.TOP, release_year=2024
    ),
    ASICMiner(
        model="KD8", vendor="IceRiver",
        algorithm="Blake3", hashrate_value=320, hashrate_unit="GH/s",
        power_w=3600, efficiency=11.25,
        price_used_rub=850000, price_new_rub=1300000,
        price_used_usd=11000, price_new_usd=16500,
        category=EquipmentCategory.TOP, release_year=2024
    ),

    # СРЕДНИЕ (ОПТИМАЛЬНЫЕ)
    ASICMiner(
        model="S21", vendor="Bitmain Antminer",
        algorithm="SHA-256", hashrate_value=200, hashrate_unit="TH/s",
        power_w=3500, efficiency=17.5,
        price_used_rub=350000, price_new_rub=560000,
        price_used_usd=4500, price_new_usd=7200,
        category=EquipmentCategory.MID, release_year=2023
    ),
    ASICMiner(
        model="M50S", vendor="MicroBT Whatsminer",
        algorithm="SHA-256", hashrate_value=126, hashrate_unit="TH/s",
        power_w=3306, efficiency=26.24,
        price_used_rub=220000, price_new_rub=350000,
        price_used_usd=2800, price_new_usd=4500,
        category=EquipmentCategory.MID, release_year=2023
    ),
    ASICMiner(
        model="L7", vendor="Bitmain Antminer",
        algorithm="Scrypt", hashrate_value=9.5, hashrate_unit="GH/s",
        power_w=3425, efficiency=360.5,
        price_used_rub=430000, price_new_rub=625000,
        price_used_usd=5500, price_new_usd=8000,
        category=EquipmentCategory.MID, release_year=2023
    ),
    ASICMiner(
        model="KS3M", vendor="IceRiver",
        algorithm="KHeavyHash", hashrate_value=6, hashrate_unit="TH/s",
        power_w=3400, efficiency=566.7,
        price_used_rub=320000, price_new_rub=480000,
        price_used_usd=4100, price_new_usd=6150,
        category=EquipmentCategory.MID, release_year=2023
    ),
    ASICMiner(
        model="KD5", vendor="IceRiver",
        algorithm="Blake3", hashrate_value=205, hashrate_unit="GH/s",
        power_w=3000, efficiency=14.6,
        price_used_rub=400000, price_new_rub=600000,
        price_used_usd=5100, price_new_usd=7650,
        category=EquipmentCategory.MID, release_year=2023
    ),

    # БЮДЖЕТНЫЕ (НАЧАЛЬНЫЙ УРОВЕНЬ)
    ASICMiner(
        model="S19", vendor="Bitmain Antminer",
        algorithm="SHA-256", hashrate_value=95, hashrate_unit="TH/s",
        power_w=3250, efficiency=34.2,
        price_used_rub=95000, price_new_rub=155000,
        price_used_usd=1200, price_new_usd=2000,
        category=EquipmentCategory.BUDGET, release_year=2022
    ),
    ASICMiner(
        model="M30S+", vendor="MicroBT Whatsminer",
        algorithm="SHA-256", hashrate_value=100, hashrate_unit="TH/s",
        power_w=3400, efficiency=34.0,
        price_used_rub=120000, price_new_rub=195000,
        price_used_usd=1500, price_new_usd=2500,
        category=EquipmentCategory.BUDGET, release_year=2022
    ),
    ASICMiner(
        model="KA3", vendor="IceRiver",
        algorithm="KHeavyHash", hashrate_value=166, hashrate_unit="GH/s",
        power_w=400, efficiency=2.41,
        price_used_rub=85000, price_new_rub=140000,
        price_used_usd=1100, price_new_usd=1800,
        category=EquipmentCategory.BUDGET, release_year=2022
    ),
    ASICMiner(
        model="KD2", vendor="IceRiver",
        algorithm="Blake3", hashrate_value=6, hashrate_unit="GH/s",
        power_w=400, efficiency=66.7,
        price_used_rub=75000, price_new_rub=125000,
        price_used_usd=950, price_new_usd=1600,
        category=EquipmentCategory.BUDGET, release_year=2022
    ),
    ASICMiner(
        model="E9", vendor="Bitmain Antminer",
        algorithm="Ethash", hashrate_value=3, hashrate_unit="GH/s",
        power_w=2556, efficiency=852.0,
        price_used_rub=100000, price_new_rub=165000,
        price_used_usd=1300, price_new_usd=2100,
        category=EquipmentCategory.BUDGET, release_year=2022
    ),

    # ДОПОЛНИТЕЛЬНЫЕ АЛГОРИТМЫ
    ASICMiner(
        model="K7", vendor="Bitmain Antminer",
        algorithm="Kaspa", hashrate_value=336, hashrate_unit="GH/s",
        power_w=3154, efficiency=9.4,
        price_used_rub=380000, price_new_rub=580000,
        price_used_usd=4850, price_new_usd=7400,
        category=EquipmentCategory.MID, release_year=2023
    ),
    ASICMiner(
        model="X7", vendor="Bitmain Antminer",
        algorithm="X11", hashrate_value=262, hashrate_unit="GH/s",
        power_w=1486, efficiency=5.67,
        price_used_rub=300000, price_new_rub=460000,
        price_used_usd=3850, price_new_usd=5900,
        category=EquipmentCategory.MID, release_year=2023
    ),
    ASICMiner(
        model="HS5", vendor="Bitmain Antminer",
        algorithm="Handshake", hashrate_value=2.7, hashrate_unit="TH/s",
        power_w=2650, efficiency=981.5,
        price_used_rub=250000, price_new_rub=380000,
        price_used_usd=3200, price_new_usd=4850,
        category=EquipmentCategory.MID, release_year=2023
    ),
]


def get_miners_by_category(category: EquipmentCategory) -> List[ASICMiner]:
    """Получить майнеры по категории"""
    return [miner for miner in ASIC_MINERS if miner.category == category]


def get_all_categories() -> List[EquipmentCategory]:
    """Получить все категории"""
    return list(EquipmentCategory)


def search_miners(query: str) -> List[ASICMiner]:
    """Поиск майнеров по названию или алгоритму"""
    query_lower = query.lower()
    return [
        miner for miner in ASIC_MINERS
        if query_lower in miner.full_name.lower() or
           query_lower in miner.algorithm.lower() or
           query_lower in miner.vendor.lower()
    ]


def get_miner_by_model(model: str) -> Optional[ASICMiner]:
    """Найти майнер по точному названию модели"""
    for miner in ASIC_MINERS:
        if miner.model.lower() == model.lower():
            return miner
    return None


def get_algorithms() -> List[str]:
    """Получить список уникальных алгоритмов"""
    return list(set(miner.algorithm for miner in ASIC_MINERS))


def get_miners_by_algorithm(algorithm: str) -> List[ASICMiner]:
    """Получить майнеры по алгоритму"""
    return [miner for miner in ASIC_MINERS if miner.algorithm.lower() == algorithm.lower()]


# Статистика для отображения
def get_category_stats() -> Dict[str, int]:
    """Статистика майнеров по категориям"""
    stats = {}
    for category in EquipmentCategory:
        stats[category.value] = len(get_miners_by_category(category))
    return stats


def get_price_ranges() -> Dict[str, Dict[str, int]]:
    """Диапазоны цен по категориям"""
    ranges = {}
    for category in EquipmentCategory:
        miners = get_miners_by_category(category)
        if miners:
            used_prices = [m.price_used_usd for m in miners]
            new_prices = [m.price_new_usd for m in miners]
            ranges[category.value] = {
                "used_min": min(used_prices),
                "used_max": max(used_prices),
                "new_min": min(new_prices),
                "new_max": max(new_prices)
            }
    return ranges
