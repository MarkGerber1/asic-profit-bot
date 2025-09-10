from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Component:
    name: str
    capex_usd: float
    power_w: float = 0.0
    lifetime_years: Optional[float] = None


@dataclass
class Scenario:
    name: str
    components: List[Component]
    baseline_revenue_usd_per_day: float
    electricity_price_usd_per_kwh: float
    hours_per_day: float = 24.0
    additional_revenue_usd_per_day: float = 0.0  # e.g., hydromodel hashrate gain

    def capex_total(self) -> float:
        return sum(c.capex_usd for c in self.components)

    def opex_electricity_per_day(self) -> float:
        kwh_per_day = sum(c.power_w for c in self.components) * self.hours_per_day / 1000.0
        return kwh_per_day * self.electricity_price_usd_per_kwh

    def opex_total_per_day(self) -> float:
        return self.opex_electricity_per_day()

    def gross_profit_per_day(self) -> float:
        return (self.baseline_revenue_usd_per_day + self.additional_revenue_usd_per_day) - self.opex_total_per_day()

    def payback_days(self) -> Optional[float]:
        daily_profit = self.gross_profit_per_day()
        if daily_profit <= 0:
            return None
        return self.capex_total() / daily_profit


def compare_scenarios(base: Scenario, alt: Scenario) -> dict:
    """Compare alternative vs base, returning delta economics and ROI.

    ROI here is defined as (ΔProfit_per_day) / CAPEX_alt, with payback in days
    computed as CAPEX_alt / ΔProfit_per_day when ΔProfit>0.
    """
    base_profit = base.gross_profit_per_day()
    alt_profit = alt.gross_profit_per_day()
    delta_profit = alt_profit - base_profit
    capex = alt.capex_total()
    roi = None if capex <= 0 else (delta_profit * 365.0) / capex
    payback_days = None if (delta_profit <= 0 or capex <= 0) else capex / delta_profit
    return {
        "base_profit_per_day": base_profit,
        "alt_profit_per_day": alt_profit,
        "delta_profit_per_day": delta_profit,
        "alt_capex": capex,
        "alt_roi_per_year": roi,
        "alt_payback_days": payback_days,
    }







