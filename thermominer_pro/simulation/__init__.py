"""
Simulation module for ThermoMiner Pro
Emergency scenario simulation and thermal dynamics
"""

from .emergency_simulator import (
    EmergencySimulator,
    EquipmentState,
    EmergencyScenario,
    format_analysis_report
)

__all__ = [
    'EmergencySimulator',
    'EquipmentState',
    'EmergencyScenario',
    'format_analysis_report'
]

