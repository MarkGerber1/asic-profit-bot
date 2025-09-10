from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RiskItem:
    code: str
    level: str  # info|warning|critical
    message: str


def assess_hydro(
    t_chip_c: float,
    t_junc_max_c: Optional[float],
    dp_total_pa: float,
    pump_head_capable_pa: float,
    t_inlet_coolant_c: float,
    t_inlet_coolant_max_c: Optional[float],
    ambient_c: float,
    relative_humidity: float,
    coolant_outlet_c: Optional[float] = None,
) -> List[RiskItem]:
    risks: List[RiskItem] = []
    if t_junc_max_c is not None and t_chip_c > t_junc_max_c:
        risks.append(RiskItem("T_CHIP_OVER", "critical", f"Chip temperature {t_chip_c:.1f}°C exceeds max {t_junc_max_c:.1f}°C"))

    if dp_total_pa > pump_head_capable_pa:
        risks.append(RiskItem("PUMP_INSUFFICIENT_HEAD", "critical", "Pump head insufficient: ΔP exceeds pump capability"))

    if t_inlet_coolant_max_c is not None and t_inlet_coolant_c > t_inlet_coolant_max_c:
        risks.append(RiskItem("COOLANT_INLET_TOO_HOT", "warning", f"Coolant inlet {t_inlet_coolant_c:.1f}°C > allowed {t_inlet_coolant_max_c:.1f}°C"))

    # Condensation risk: if any surface < dewpoint; crude check: if coolant_outlet < (ambient - (100 - RH*100)/5)
    # Better: dewpoint approximation (Magnus-Tetens)
    def dew_point_c(T_c: float, RH: float) -> float:
        a, b = 17.62, 243.12
        gamma = (a * T_c / (b + T_c)) + math.log(max(1e-3, RH))
        return (b * gamma) / (a - gamma)

    import math
    RH = max(0.01, min(0.99, relative_humidity))
    Td = dew_point_c(ambient_c, RH)
    if coolant_outlet_c is not None and coolant_outlet_c < Td:
        risks.append(RiskItem("CONDENSATION_RISK", "critical", f"Coolant/loop below dew point {Td:.1f}°C → condensation risk"))

    return risks


def assess_air(
    t_inlet_air_c: float,
    t_inlet_air_max_c: Optional[float],
    openings_area_m2: Optional[float],
    required_openings_area_m2: Optional[float],
    airflow_deficit_cfm: Optional[float],
) -> List[RiskItem]:
    risks: List[RiskItem] = []
    if t_inlet_air_max_c is not None and t_inlet_air_c > t_inlet_air_max_c:
        risks.append(RiskItem("AIR_INLET_OVER", "critical", f"ASIC inlet air {t_inlet_air_c:.1f}°C exceeds allowed {t_inlet_air_max_c:.1f}°C"))
    if openings_area_m2 is not None and required_openings_area_m2 is not None and openings_area_m2 < required_openings_area_m2:
        risks.append(RiskItem("OPENINGS_INSUFFICIENT", "warning", "Ventilation openings area is insufficient"))
    if airflow_deficit_cfm is not None and airflow_deficit_cfm > 0:
        risks.append(RiskItem("AIRFLOW_DEFICIT", "critical", f"Airflow deficit {airflow_deficit_cfm:.0f} CFM vs requirement"))
    return risks














