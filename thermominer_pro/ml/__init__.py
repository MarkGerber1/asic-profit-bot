"""
Machine Learning module for ThermoMiner Pro
Predictive maintenance and optimization
"""

from .predictive_maintenance import (
    PredictiveMaintenanceModel,
    CoolingOptimizer,
    SensorData,
    FailurePrediction,
    format_prediction_report
)

__all__ = [
    'PredictiveMaintenanceModel',
    'CoolingOptimizer',
    'SensorData',
    'FailurePrediction',
    'format_prediction_report'
]

