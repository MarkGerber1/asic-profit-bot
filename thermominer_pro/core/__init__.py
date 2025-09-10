
"""
Physics-based calculation engines for ThermoMiner Pro.

Modules:
- hydro_core: Hydronic loop sizing, heat exchanger/radiator sizing, hydraulics, pump selection
- airflow_core: Room airflow sizing, duct network resistance, fan selection
- finance_core: CAPEX/OPEX/TCO/ROI scenario analysis
- risk_engine: Consolidated risk assessment across modules
"""

from . import hydro_core, airflow_core, finance_core, risk_engine

__all__ = [
    "hydro_core",
    "airflow_core",
    "finance_core",
    "risk_engine",
]



