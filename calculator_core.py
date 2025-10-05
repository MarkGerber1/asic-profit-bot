"""
Ядро калькулятора ASIC майнинга - расчеты прибыли и окупаемости
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import math

from equipment_db import ASICMiner, get_miner_by_model
from algorithms_db import MiningAlgorithm, get_algorithm
from emcd_integration import get_emcd_data, EMCDMinerData
from currency_api import get_usd_rub_rate, get_crypto_prices


class CalculationPeriod(Enum):
    HOUR = "1h"
    DAY = "24h"
    WEEK = "168h"
    MONTH = "720h"  # 30 дней
    THREE_MONTHS = "2160h"  # 90 дней
    SIX_MONTHS = "4320h"  # 180 дней
    YEAR = "8760h"  # 365 дней


@dataclass
class CalculationParams:
    """Параметры расчета"""
    electricity_price_rub: float  # ₽/кВт⋅ч
    electricity_price_usd: float  # $/кВт⋅ч
    pool_fee_percent: float = 1.0  # Комиссия пула (%)
    marketplace_fee_percent: float = 1.0  # Комиссия маркетплейса (%)
    uptime_percent: float = 100.0  # Время работы (%)
    difficulty_increase_percent: float = 5.0  # Рост сложности в месяц (%)
    power_efficiency_loss: float = 2.0  # Потери эффективности в год (%)


@dataclass
class ProfitabilityResult:
    """Результат расчета прибыльности"""
    period: CalculationPeriod
    hours: int

    # Доходы
    revenue_rub: float
    revenue_usd: float

    # Расходы
    electricity_cost_rub: float
    electricity_cost_usd: float
    total_fees_rub: float
    total_fees_usd: float

    # Прибыль
    gross_profit_rub: float
    gross_profit_usd: float
    net_profit_rub: float
    net_profit_usd: float

    # Эффективность
    profit_per_kwh_rub: float
    profit_per_kwh_usd: float
    roi_days: Optional[int] = None
    payback_months: Optional[float] = None


@dataclass
class CalculatorResult:
    """Полный результат расчета"""
    miner: ASICMiner
    algorithm: Optional[MiningAlgorithm]
    params: CalculationParams

    # Текущая прибыльность
    current_profit_rub_day: float
    current_profit_usd_day: float

    # Расчеты по периодам
    results: List[ProfitabilityResult]

    # ROI и окупаемость
    roi_days_used: Optional[int]
    roi_days_new: Optional[int]
    payback_months_used: Optional[float]
    payback_months_new: Optional[float]

    # Дополнительная информация
    electricity_cost_rub_day: float
    electricity_cost_usd_day: float
    hashrate_display: str
    power_display: str
    efficiency_display: str

    calculated_at: datetime
    data_source: str


class MiningCalculator:
    """Калькулятор майнинга"""

    def __init__(self):
        self.usd_rub_rate = 85.0  # Базовый курс, будет обновляться

    async def update_rates(self):
        """Обновить курсы валют"""
        try:
            self.usd_rub_rate = await get_usd_rub_rate() or 85.0
        except Exception as e:
            print(f"Ошибка обновления курса USD/RUB: {e}")

    def calculate_by_equipment(
        self,
        miner: ASICMiner,
        electricity_price_rub: float,
        is_used: bool = True,
        custom_params: Optional[CalculationParams] = None
    ) -> CalculatorResult:
        """
        Расчет по оборудованию (используя данные из базы)
        """
        params = custom_params or CalculationParams(
            electricity_price_rub=electricity_price_rub,
            electricity_price_usd=electricity_price_rub / self.usd_rub_rate
        )

        # Получаем алгоритм майнера
        algorithm = get_algorithm(miner.algorithm)

        # Расчет текущей прибыли (упрощенная модель на основе данных базы)
        # В реальности здесь должна быть интеграция с NiceHash/EMCD
        base_profit_usd_day = miner.income_usd_day if hasattr(miner, 'income_usd_day') else 50.0

        # Корректируем на фактические параметры
        electricity_cost_usd_day = (miner.power_w / 1000) * 24 * params.electricity_price_usd
        current_profit_usd_day = base_profit_usd_day - electricity_cost_usd_day
        current_profit_rub_day = current_profit_usd_day * self.usd_rub_rate

        # Расчеты по периодам
        results = []
        for period in CalculationPeriod:
            hours = self._period_to_hours(period)

            # Учитываем рост сложности и деградацию
            difficulty_multiplier = self._calculate_difficulty_multiplier(hours, params.difficulty_increase_percent)
            efficiency_multiplier = self._calculate_efficiency_multiplier(hours, params.power_efficiency_loss)

            # Расчет доходов и расходов
            revenue_usd = self._calculate_revenue(current_profit_usd_day, hours, difficulty_multiplier)
            electricity_cost_usd = electricity_cost_usd_day * hours / 24 * efficiency_multiplier
            fees_usd = revenue_usd * (params.pool_fee_percent + params.marketplace_fee_percent) / 100
            uptime_multiplier = params.uptime_percent / 100

            gross_profit_usd = revenue_usd - electricity_cost_usd - fees_usd
            net_profit_usd = gross_profit_usd * uptime_multiplier

            # Конвертация в рубли
            revenue_rub = revenue_usd * self.usd_rub_rate
            electricity_cost_rub = electricity_cost_usd * self.usd_rub_rate
            fees_rub = fees_usd * self.usd_rub_rate
            gross_profit_rub = gross_profit_usd * self.usd_rub_rate
            net_profit_rub = net_profit_usd * self.usd_rub_rate

            result = ProfitabilityResult(
                period=period,
                hours=hours,
                revenue_rub=revenue_rub,
                revenue_usd=revenue_usd,
                electricity_cost_rub=electricity_cost_rub,
                electricity_cost_usd=electricity_cost_usd,
                total_fees_rub=fees_rub,
                total_fees_usd=fees_usd,
                gross_profit_rub=gross_profit_rub,
                gross_profit_usd=gross_profit_usd,
                net_profit_rub=net_profit_rub,
                net_profit_usd=net_profit_usd,
                profit_per_kwh_rub=net_profit_rub / (miner.power_w * hours / 1000) if miner.power_w > 0 else 0,
                profit_per_kwh_usd=net_profit_usd / (miner.power_w * hours / 1000) if miner.power_w > 0 else 0
            )
            results.append(result)

        # Расчет ROI
        price_used = miner.get_price_usd(is_used=True)
        price_new = miner.get_price_usd(is_used=False)

        roi_days_used = self._calculate_roi_days(price_used, current_profit_usd_day) if price_used > 0 else None
        roi_days_new = self._calculate_roi_days(price_new, current_profit_usd_day) if price_new > 0 else None

        payback_months_used = (roi_days_used / 30) if roi_days_used else None
        payback_months_new = (roi_days_new / 30) if roi_days_new else None

        return CalculatorResult(
            miner=miner,
            algorithm=algorithm,
            params=params,
            current_profit_rub_day=current_profit_rub_day,
            current_profit_usd_day=current_profit_usd_day,
            results=results,
            roi_days_used=roi_days_used,
            roi_days_new=roi_days_new,
            payback_months_used=payback_months_used,
            payback_months_new=payback_months_new,
            electricity_cost_rub_day=electricity_cost_usd_day * self.usd_rub_rate,
            electricity_cost_usd_day=electricity_cost_usd_day,
            hashrate_display=miner.hashrate_display,
            power_display=f"{miner.power_w} W",
            efficiency_display=f"{miner.efficiency:.1f} W/TH" if hasattr(miner, 'efficiency') and miner.efficiency > 0 else "N/A",
            calculated_at=datetime.now(),
            data_source="Internal Database"
        )

    async def calculate_by_algorithm(
        self,
        algorithm_name: str,
        hashrate_value: float,
        hashrate_unit: str,
        power_w: int,
        electricity_price_rub: float,
        custom_params: Optional[CalculationParams] = None
    ) -> CalculatorResult:
        """
        Расчет по алгоритму (используя NiceHash/EMCD API)
        """
        algorithm = get_algorithm(algorithm_name)
        if not algorithm:
            raise ValueError(f"Алгоритм {algorithm_name} не найден")

        params = custom_params or CalculationParams(
            electricity_price_rub=electricity_price_rub,
            electricity_price_usd=electricity_price_rub / self.usd_rub_rate
        )

        # Получаем актуальную прибыльность из EMCD или NiceHash
        current_profit_usd_day = await self._get_realtime_profitability(
            algorithm_name, hashrate_value, hashrate_unit, power_w, params
        )

        # Создаем виртуальный майнер для совместимости
        virtual_miner = ASICMiner(
            model=f"Custom {algorithm_name}",
            vendor="Virtual",
            algorithm=algorithm_name,
            hashrate_value=hashrate_value,
            hashrate_unit=hashrate_unit,
            power_w=power_w,
            efficiency=power_w / hashrate_value if hashrate_value > 0 else 0,
            price_used_rub=0,  # Не применимо для виртуального майнера
            price_new_rub=0,
            price_used_usd=0,
            price_new_usd=0,
            category=None,  # type: ignore
            release_year=datetime.now().year
        )

        electricity_cost_usd_day = (power_w / 1000) * 24 * params.electricity_price_usd
        current_profit_rub_day = current_profit_usd_day * self.usd_rub_rate

        # Расчеты по периодам (аналогично calculate_by_equipment)
        results = []
        for period in CalculationPeriod:
            hours = self._period_to_hours(period)

            difficulty_multiplier = self._calculate_difficulty_multiplier(hours, params.difficulty_increase_percent)
            efficiency_multiplier = self._calculate_efficiency_multiplier(hours, params.power_efficiency_loss)

            revenue_usd = self._calculate_revenue(current_profit_usd_day, hours, difficulty_multiplier)
            electricity_cost_usd = electricity_cost_usd_day * hours / 24 * efficiency_multiplier
            fees_usd = revenue_usd * (params.pool_fee_percent + params.marketplace_fee_percent) / 100
            uptime_multiplier = params.uptime_percent / 100

            gross_profit_usd = revenue_usd - electricity_cost_usd - fees_usd
            net_profit_usd = gross_profit_usd * uptime_multiplier

            revenue_rub = revenue_usd * self.usd_rub_rate
            electricity_cost_rub = electricity_cost_usd * self.usd_rub_rate
            fees_rub = fees_usd * self.usd_rub_rate
            gross_profit_rub = gross_profit_usd * self.usd_rub_rate
            net_profit_rub = net_profit_usd * self.usd_rub_rate

            result = ProfitabilityResult(
                period=period,
                hours=hours,
                revenue_rub=revenue_rub,
                revenue_usd=revenue_usd,
                electricity_cost_rub=electricity_cost_rub,
                electricity_cost_usd=electricity_cost_usd,
                total_fees_rub=fees_rub,
                total_fees_usd=fees_usd,
                gross_profit_rub=gross_profit_rub,
                gross_profit_usd=gross_profit_usd,
                net_profit_rub=net_profit_rub,
                net_profit_usd=net_profit_usd,
                profit_per_kwh_rub=net_profit_rub / (power_w * hours / 1000) if power_w > 0 else 0,
                profit_per_kwh_usd=net_profit_usd / (power_w * hours / 1000) if power_w > 0 else 0
            )
            results.append(result)

        return CalculatorResult(
            miner=virtual_miner,
            algorithm=algorithm,
            params=params,
            current_profit_rub_day=current_profit_rub_day,
            current_profit_usd_day=current_profit_usd_day,
            results=results,
            roi_days_used=None,  # Не применимо для алгоритма
            roi_days_new=None,
            payback_months_used=None,
            payback_months_new=None,
            electricity_cost_rub_day=electricity_cost_usd_day * self.usd_rub_rate,
            electricity_cost_usd_day=electricity_cost_usd_day,
            hashrate_display=f"{hashrate_value} {hashrate_unit}",
            power_display=f"{power_w} W",
            efficiency_display=f"{power_w/hashrate_value:.2f} W/{hashrate_unit.split('/')[0]}" if hashrate_value > 0 else "N/A",
            calculated_at=datetime.now(),
            data_source="EMCD.io / NiceHash"
        )

    async def _get_realtime_profitability(
        self,
        algorithm: str,
        hashrate: float,
        hashrate_unit: str,
        power_w: int,
        params: CalculationParams
    ) -> float:
        """
        Получить актуальную прибыльность из внешних источников
        """
        try:
            # Сначала пробуем EMCD
            emcd_data = await get_emcd_data(f"{algorithm}_{hashrate}", params.electricity_price_rub)
            if emcd_data:
                return emcd_data.net_profit_usd_day

            # Если EMCD недоступен, используем NiceHash API через service
            # Для упрощения используем базовую оценку
            base_profitability = self._estimate_profitability(algorithm, hashrate, hashrate_unit)
            electricity_cost = (power_w / 1000) * 24 * params.electricity_price_usd

            return max(0, base_profitability - electricity_cost)

        except Exception as e:
            print(f"Ошибка получения данных о прибыльности: {e}")
            # Возвращаем базовую оценку
            return self._estimate_profitability(algorithm, hashrate, hashrate_unit)

    def _estimate_profitability(self, algorithm: str, hashrate: float, hashrate_unit: str) -> float:
        """Базовая оценка прибыльности (fallback)"""
        algo_data = get_algorithm(algorithm)
        if not algo_data:
            return 10.0  # Базовая прибыль

        # Конвертируем хешрейт в TH/s для расчетов
        hash_th = self._convert_to_th(hashrate, hashrate_unit)

        # Базовая формула: цена монеты * награда * хешрейт / сеть * множитель прибыльности
        base_profit = (algo_data.current_price_usd * algo_data.block_reward *
                      hash_th / (algo_data.network_hashrate_th / 1000000) *
                      algo_data.profitability_multiplier)

        return max(0, base_profit)

    def _convert_to_th(self, value: float, unit: str) -> float:
        """Конвертировать хешрейт в TH/s"""
        unit_multipliers = {
            'H/s': 1e-12,
            'KH/s': 1e-9,
            'MH/s': 1e-6,
            'GH/s': 1e-3,
            'TH/s': 1,
            'PH/s': 1e3,
            'EH/s': 1e6
        }
        return value * unit_multipliers.get(unit, 1)

    def _period_to_hours(self, period: CalculationPeriod) -> int:
        """Конвертировать период в часы"""
        period_hours = {
            CalculationPeriod.HOUR: 1,
            CalculationPeriod.DAY: 24,
            CalculationPeriod.WEEK: 168,
            CalculationPeriod.MONTH: 720,  # 30 дней
            CalculationPeriod.THREE_MONTHS: 2160,  # 90 дней
            CalculationPeriod.SIX_MONTHS: 4320,  # 180 дней
            CalculationPeriod.YEAR: 8760  # 365 дней
        }
        return period_hours[period]

    def _calculate_difficulty_multiplier(self, hours: int, increase_percent: float) -> float:
        """Рассчитать множитель роста сложности"""
        months = hours / (24 * 30)
        return (1 - increase_percent / 100) ** months

    def _calculate_efficiency_multiplier(self, hours: int, loss_percent: float) -> float:
        """Рассчитать множитель потери эффективности"""
        years = hours / (24 * 365)
        return (1 + loss_percent / 100) ** years

    def _calculate_revenue(self, daily_profit: float, hours: int, difficulty_multiplier: float) -> float:
        """Рассчитать доход с учетом сложности"""
        days = hours / 24
        return daily_profit * days * difficulty_multiplier

    def _calculate_roi_days(self, equipment_price: float, daily_profit: float) -> Optional[int]:
        """Рассчитать ROI в днях"""
        if daily_profit <= 0:
            return None
        return math.ceil(equipment_price / daily_profit)

    async def compare_miners(self, miner_models: List[str], electricity_price_rub: float) -> List[CalculatorResult]:
        """Сравнить несколько майнеров"""
        results = []
        for model in miner_models:
            miner = get_miner_by_model(model)
            if miner:
                result = self.calculate_by_equipment(miner, electricity_price_rub)
                results.append(result)
        return results


# Глобальный экземпляр калькулятора
calculator = MiningCalculator()


async def calculate_equipment_profitability(
    model: str,
    electricity_price_rub: float,
    is_used: bool = True
) -> Optional[CalculatorResult]:
    """Быстрый расчет для оборудования"""
    await calculator.update_rates()
    miner = get_miner_by_model(model)
    if miner:
        return calculator.calculate_by_equipment(miner, electricity_price_rub, is_used)
    return None


async def calculate_algorithm_profitability(
    algorithm: str,
    hashrate: float,
    hashrate_unit: str,
    power_w: int,
    electricity_price_rub: float
) -> CalculatorResult:
    """Быстрый расчет для алгоритма"""
    await calculator.update_rates()
    return await calculator.calculate_by_algorithm(
        algorithm, hashrate, hashrate_unit, power_w, electricity_price_rub
    )
