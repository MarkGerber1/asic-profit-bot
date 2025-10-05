"""
База данных алгоритмов майнинга с характеристиками
"""

from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class AlgorithmType(Enum):
    POW = "Proof-of-Work"
    POS = "Proof-of-Stake"
    OTHER = "Other"


@dataclass
class MiningAlgorithm:
    """Алгоритм майнинга с характеристиками"""
    name: str
    type: AlgorithmType
    description: str
    difficulty_adjustment: str  # Как часто корректируется сложность
    block_time: int  # Время блока в секундах
    block_reward: float  # Награда за блок (в основной валюте)
    coin_symbol: str
    coin_name: str
    network_hashrate_th: float  # TH/s
    current_price_usd: float
    current_price_rub: float
    profitability_multiplier: float  # Множитель прибыльности (относительно BTC)
    nicehash_unit: str  # Единица измерения на NiceHash
    emcd_supported: bool
    popular_miners: List[str]  # Популярные модели ASIC для этого алгоритма


# База данных алгоритмов
MINING_ALGORITHMS = {
    "SHA-256": MiningAlgorithm(
        name="SHA-256",
        type=AlgorithmType.POW,
        description="Алгоритм Bitcoin и большинства SHA-256 монет",
        difficulty_adjustment="Каждые 2016 блоков (~2 недели)",
        block_time=600,
        block_reward=6.25,
        coin_symbol="BTC",
        coin_name="Bitcoin",
        network_hashrate_th=670000000,  # ~670 EH/s
        current_price_usd=95000,
        current_price_rub=8500000,
        profitability_multiplier=1.0,
        nicehash_unit="TH",
        emcd_supported=True,
        popular_miners=["Antminer S21", "Antminer S19", "Whatsminer M50"]
    ),

    "Scrypt": MiningAlgorithm(
        name="Scrypt",
        type=AlgorithmType.POW,
        description="Алгоритм Litecoin и других Scrypt монет",
        difficulty_adjustment="Каждые 2016 блоков",
        block_time=150,
        block_reward=12.5,
        coin_symbol="LTC",
        coin_name="Litecoin",
        network_hashrate_th=300000,  # 300 TH/s
        current_price_usd=75,
        current_price_rub=6750,
        profitability_multiplier=0.15,
        nicehash_unit="MH",
        emcd_supported=True,
        popular_miners=["Antminer L7", "Antminer L9"]
    ),

    "KHeavyHash": MiningAlgorithm(
        name="KHeavyHash",
        type=AlgorithmType.POW,
        description="Алгоритм Kaspa - высокопроизводительный PoW",
        difficulty_adjustment="DAG-based",
        block_time=1,
        block_reward=100,
        coin_symbol="KAS",
        coin_name="Kaspa",
        network_hashrate_th=1200000,  # 1.2 PH/s
        current_price_usd=0.15,
        current_price_rub=13.5,
        profitability_multiplier=0.25,
        nicehash_unit="GH",
        emcd_supported=True,
        popular_miners=["IceRiver KS5L", "IceRiver KS3M"]
    ),

    "Blake3": MiningAlgorithm(
        name="Blake3",
        type=AlgorithmType.POW,
        description="Быстрый хеш-алгоритм для Alephium и других проектов",
        difficulty_adjustment="Каждые 1024 блока",
        block_time=64,
        block_reward=20.0,
        coin_symbol="ALPH",
        coin_name="Alephium",
        network_hashrate_th=80000,  # 80 TH/s
        current_price_usd=1.8,
        current_price_rub=162,
        profitability_multiplier=0.18,
        nicehash_unit="GH",
        emcd_supported=True,
        popular_miners=["IceRiver KD8", "IceRiver KD5"]
    ),

    "Ethash": MiningAlgorithm(
        name="Ethash",
        type=AlgorithmType.POW,
        description="Алгоритм Ethereum и Ethereum Classic",
        difficulty_adjustment="Каждые 13 секунд",
        block_time=13,
        block_reward=2.0,
        coin_symbol="ETH",
        coin_name="Ethereum",
        network_hashrate_th=1000000,  # 1 PH/s
        current_price_usd=3200,
        current_price_rub=288000,
        profitability_multiplier=0.35,
        nicehash_unit="MH",
        emcd_supported=True,
        popular_miners=["Antminer E9", "RX 580 GPU"]
    ),

    "X11": MiningAlgorithm(
        name="X11",
        type=AlgorithmType.POW,
        description="11-раундовый алгоритм для Dash и других монет",
        difficulty_adjustment="DGW",
        block_time=150,
        block_reward=1.0,
        coin_symbol="DASH",
        coin_name="Dash",
        network_hashrate_th=15000,  # 15 TH/s
        current_price_usd=28,
        current_price_rub=2520,
        profitability_multiplier=0.08,
        nicehash_unit="MH",
        emcd_supported=False,
        popular_miners=["Antminer X7", "GPU miners"]
    ),

    "Kaspa": MiningAlgorithm(
        name="Kaspa",
        type=AlgorithmType.POW,
        description="Алгоритм Kaspa (KHeavyHash)",
        difficulty_adjustment="GHOSTDAG",
        block_time=1,
        block_reward=100,
        coin_symbol="KAS",
        coin_name="Kaspa",
        network_hashrate_th=1200000,  # 1.2 PH/s
        current_price_usd=0.15,
        current_price_rub=13.5,
        profitability_multiplier=0.25,
        nicehash_unit="GH",
        emcd_supported=True,
        popular_miners=["Antminer K7", "IceRiver KS5L"]
    ),

    "Handshake": MiningAlgorithm(
        name="Handshake",
        type=AlgorithmType.POW,
        description="Алгоритм Handshake для управления доменами",
        difficulty_adjustment="LWMA",
        block_time=600,
        block_reward=2000,
        coin_symbol="HNS",
        coin_name="Handshake",
        network_hashrate_th=500,  # 500 TH/s
        current_price_usd=0.02,
        current_price_rub=1.8,
        profitability_multiplier=0.02,
        nicehash_unit="TH",
        emcd_supported=False,
        popular_miners=["Antminer HS5"]
    ),

    "Eaglesong": MiningAlgorithm(
        name="Eaglesong",
        type=AlgorithmType.POW,
        description="Алгоритм Nervos Network (CKB)",
        difficulty_adjustment="Eaglesong",
        block_time=11,
        block_reward=400,
        coin_symbol="CKB",
        coin_name="Nervos",
        network_hashrate_th=300000,  # 300 TH/s
        current_price_usd=0.008,
        current_price_rub=0.72,
        profitability_multiplier=0.03,
        nicehash_unit="TH",
        emcd_supported=False,
        popular_miners=["Antminer K7"]
    ),

    "Autolykos": MiningAlgorithm(
        name="Autolykos",
        type=AlgorithmType.POW,
        description="Алгоритм Ergo - memory-hard PoW",
        difficulty_adjustment="Autolykos",
        block_time=120,
        block_reward=67.5,
        coin_symbol="ERG",
        coin_name="Ergo",
        network_hashrate_th=20000,  # 20 TH/s
        current_price_usd=1.2,
        current_price_rub=108,
        profitability_multiplier=0.05,
        nicehash_unit="MH",
        emcd_supported=False,
        popular_miners=["GPU miners"]
    ),

    "RandomX": MiningAlgorithm(
        name="RandomX",
        type=AlgorithmType.POW,
        description="Memory-hard алгоритм Monero",
        difficulty_adjustment="LWMA",
        block_time=120,
        block_reward=0.6,
        coin_symbol="XMR",
        coin_name="Monero",
        network_hashrate_th=15000,  # 15 GH/s
        current_price_usd=155,
        current_price_rub=13950,
        profitability_multiplier=0.12,
        nicehash_unit="KH",
        emcd_supported=False,
        popular_miners=["CPU miners"]
    ),

    "Tensority": MiningAlgorithm(
        name="Tensority",
        type=AlgorithmType.POW,
        description="Алгоритм Bytom для tensor операций",
        difficulty_adjustment="Tensority",
        block_time=150,
        block_reward=12.5,
        coin_symbol="BTM",
        coin_name="Bytom",
        network_hashrate_th=2000,  # 2 TH/s
        current_price_usd=0.05,
        current_price_rub=4.5,
        profitability_multiplier=0.01,
        nicehash_unit="KH",
        emcd_supported=False,
        popular_miners=["GPU miners"]
    )
}


def get_algorithm(name: str) -> MiningAlgorithm:
    """Получить алгоритм по имени"""
    return MINING_ALGORITHMS.get(name.upper())


def get_all_algorithms() -> List[MiningAlgorithm]:
    """Получить все алгоритмы"""
    return list(MINING_ALGORITHMS.values())


def get_supported_algorithms() -> List[MiningAlgorithm]:
    """Получить алгоритмы, поддерживаемые EMCD"""
    return [algo for algo in MINING_ALGORITHMS.values() if algo.emcd_supported]


def get_algorithms_by_type(algo_type: AlgorithmType) -> List[MiningAlgorithm]:
    """Получить алгоритмы по типу"""
    return [algo for algo in MINING_ALGORITHMS.values() if algo.type == algo_type]


def get_popular_algorithms(limit: int = 8) -> List[MiningAlgorithm]:
    """Получить наиболее популярные алгоритмы"""
    # Сортируем по profitability_multiplier
    return sorted(
        MINING_ALGORITHMS.values(),
        key=lambda x: x.profitability_multiplier,
        reverse=True
    )[:limit]


def search_algorithms(query: str) -> List[MiningAlgorithm]:
    """Поиск алгоритмов по названию или монете"""
    query_lower = query.lower()
    return [
        algo for algo in MINING_ALGORITHMS.values()
        if query_lower in algo.name.lower() or
           query_lower in algo.coin_name.lower() or
           query_lower in algo.coin_symbol.lower()
    ]


def get_algorithm_stats() -> Dict:
    """Статистика по алгоритмам"""
    total = len(MINING_ALGORITHMS)
    supported = len(get_supported_algorithms())
    pow_count = len(get_algorithms_by_type(AlgorithmType.POW))

    return {
        "total_algorithms": total,
        "emcd_supported": supported,
        "pow_algorithms": pow_count,
        "pos_algorithms": len(get_algorithms_by_type(AlgorithmType.POS)),
        "other_algorithms": len(get_algorithms_by_type(AlgorithmType.OTHER))
    }
