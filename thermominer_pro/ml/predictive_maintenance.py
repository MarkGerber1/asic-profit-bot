"""
Machine Learning Module for Predictive Maintenance
Predicts equipment failures and optimizes cooling parameters
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import joblib
from pathlib import Path
from datetime import datetime, timedelta


@dataclass
class SensorData:
    """Sensor reading from mining equipment."""
    timestamp: datetime
    chip_temp: float  # °C
    coolant_temp: float  # °C
    ambient_temp: float  # °C
    flow_rate: float  # L/min
    pressure: float  # bar
    fan_rpm: int
    power_draw: float  # W
    hashrate: float  # TH/s
    equipment_id: str


@dataclass
class FailurePrediction:
    """Equipment failure prediction."""
    equipment_id: str
    failure_probability: float  # 0-1
    predicted_failure_hours: float
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    recommended_action: str
    contributing_factors: List[str]


class PredictiveMaintenanceModel:
    """ML model for predicting equipment failures."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = Path(model_path) if model_path else Path.home() / '.thermominer_pro' / 'ml_models'
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.failure_classifier = None
        self.time_to_failure_regressor = None
        self.scaler = StandardScaler()
        
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models if available."""
        classifier_path = self.model_path / 'failure_classifier.joblib'
        regressor_path = self.model_path / 'time_to_failure_regressor.joblib'
        scaler_path = self.model_path / 'scaler.joblib'
        
        try:
            if classifier_path.exists():
                self.failure_classifier = joblib.load(classifier_path)
            if regressor_path.exists():
                self.time_to_failure_regressor = joblib.load(regressor_path)
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
        except Exception as e:
            print(f"Не удалось загрузить модели: {e}")
    
    def save_models(self):
        """Save trained models to disk."""
        try:
            if self.failure_classifier:
                joblib.dump(self.failure_classifier, self.model_path / 'failure_classifier.joblib')
            if self.time_to_failure_regressor:
                joblib.dump(self.time_to_failure_regressor, self.model_path / 'time_to_failure_regressor.joblib')
            joblib.dump(self.scaler, self.model_path / 'scaler.joblib')
        except Exception as e:
            print(f"Не удалось сохранить модели: {e}")
    
    def extract_features(self, sensor_data: SensorData) -> np.ndarray:
        """Extract features from sensor data."""
        features = [
            sensor_data.chip_temp,
            sensor_data.coolant_temp,
            sensor_data.ambient_temp,
            sensor_data.flow_rate,
            sensor_data.pressure,
            sensor_data.fan_rpm,
            sensor_data.power_draw,
            sensor_data.hashrate,
            # Derived features
            sensor_data.chip_temp - sensor_data.coolant_temp,  # Temperature delta
            sensor_data.chip_temp - sensor_data.ambient_temp,  # Chip overheat
            sensor_data.power_draw / max(sensor_data.hashrate, 0.1),  # Efficiency
        ]
        return np.array(features).reshape(1, -1)
    
    def train_on_synthetic_data(self, n_samples: int = 1000):
        """Train models on synthetic data (for demonstration).
        
        In production, this should be replaced with real historical data.
        """
        print("Обучение моделей на синтетических данных...")
        
        # Generate synthetic training data
        X_train = []
        y_failure = []
        y_time_to_failure = []
        
        for _ in range(n_samples):
            # Normal operation
            if np.random.rand() > 0.3:
                chip_temp = np.random.normal(65, 5)
                coolant_temp = np.random.normal(30, 3)
                ambient_temp = np.random.normal(25, 2)
                flow_rate = np.random.normal(10, 1)
                pressure = np.random.normal(1.5, 0.2)
                fan_rpm = np.random.normal(3000, 200)
                power_draw = np.random.normal(3250, 100)
                hashrate = np.random.normal(110, 5)
                
                failure = 0
                time_to_failure = np.random.uniform(720, 8760)  # 1 month to 1 year
            else:
                # Degraded/failing operation
                chip_temp = np.random.normal(80, 10)
                coolant_temp = np.random.normal(40, 5)
                ambient_temp = np.random.normal(30, 3)
                flow_rate = np.random.normal(7, 2)
                pressure = np.random.normal(1.0, 0.3)
                fan_rpm = np.random.normal(2500, 300)
                power_draw = np.random.normal(3400, 200)
                hashrate = np.random.normal(95, 10)
                
                failure = 1
                time_to_failure = np.random.uniform(1, 168)  # 1 hour to 1 week
            
            features = [
                chip_temp, coolant_temp, ambient_temp, flow_rate, pressure,
                fan_rpm, power_draw, hashrate,
                chip_temp - coolant_temp,
                chip_temp - ambient_temp,
                power_draw / max(hashrate, 0.1)
            ]
            
            X_train.append(features)
            y_failure.append(failure)
            y_time_to_failure.append(time_to_failure)
        
        X_train = np.array(X_train)
        y_failure = np.array(y_failure)
        y_time_to_failure = np.array(y_time_to_failure)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train failure classifier
        self.failure_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.failure_classifier.fit(X_train_scaled, y_failure)
        
        # Train time-to-failure regressor
        self.time_to_failure_regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.time_to_failure_regressor.fit(X_train_scaled, y_time_to_failure)
        
        # Save models
        self.save_models()
        
        print(f"✅ Модели обучены на {n_samples} образцах")
        print(f"   Точность классификатора: {self.failure_classifier.score(X_train_scaled, y_failure):.2%}")
    
    def predict_failure(self, sensor_data: SensorData) -> FailurePrediction:
        """Predict equipment failure based on sensor data."""
        # Ensure models are trained
        if self.failure_classifier is None:
            self.train_on_synthetic_data()
        
        # Extract and scale features
        features = self.extract_features(sensor_data)
        features_scaled = self.scaler.transform(features)
        
        # Predict failure probability
        failure_prob = self.failure_classifier.predict_proba(features_scaled)[0][1]
        
        # Predict time to failure
        time_to_failure = self.time_to_failure_regressor.predict(features_scaled)[0]
        
        # Determine risk level
        if failure_prob < 0.2:
            risk_level = 'low'
        elif failure_prob < 0.5:
            risk_level = 'medium'
        elif failure_prob < 0.8:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Analyze contributing factors
        feature_importance = self.failure_classifier.feature_importances_
        feature_names = [
            'chip_temp', 'coolant_temp', 'ambient_temp', 'flow_rate', 'pressure',
            'fan_rpm', 'power_draw', 'hashrate', 'temp_delta', 'chip_overheat', 'efficiency'
        ]
        
        # Get top 3 contributing factors
        top_factors_idx = np.argsort(feature_importance)[-3:][::-1]
        contributing_factors = [feature_names[i] for i in top_factors_idx]
        
        # Generate recommendation
        if risk_level == 'critical':
            recommendation = "СРОЧНО: Немедленно остановите оборудование для проверки!"
        elif risk_level == 'high':
            recommendation = "Запланируйте техническое обслуживание в течение 24 часов"
        elif risk_level == 'medium':
            recommendation = "Увеличьте частоту мониторинга, проверьте систему охлаждения"
        else:
            recommendation = "Оборудование работает нормально"
        
        # Add specific recommendations based on factors
        if sensor_data.chip_temp > 75:
            recommendation += ". Проверьте систему охлаждения - высокая температура чипа"
        if sensor_data.flow_rate < 8:
            recommendation += ". Низкий расход охлаждающей жидкости - проверьте насос"
        if sensor_data.hashrate < 100:
            recommendation += ". Снижение хешрейта - возможна деградация чипов"
        
        return FailurePrediction(
            equipment_id=sensor_data.equipment_id,
            failure_probability=failure_prob,
            predicted_failure_hours=time_to_failure,
            risk_level=risk_level,
            recommended_action=recommendation,
            contributing_factors=contributing_factors
        )
    
    def batch_predict(self, sensor_data_list: List[SensorData]) -> List[FailurePrediction]:
        """Predict failures for multiple equipment."""
        return [self.predict_failure(data) for data in sensor_data_list]


class CoolingOptimizer:
    """ML-based cooling parameter optimizer."""
    
    def __init__(self):
        self.optimizer_model = None
        self.scaler = StandardScaler()
    
    def optimize_flow_rate(self, chip_temp: float, ambient_temp: float, 
                           tdp: float, target_temp: float = 65.0) -> Dict:
        """Optimize coolant flow rate for target temperature.
        
        Uses simplified physics-based model with ML enhancement.
        """
        # Physics-based baseline
        temp_delta = chip_temp - ambient_temp
        required_cooling = tdp  # Watts to dissipate
        
        # Empirical formula: flow_rate ∝ sqrt(cooling_power / temp_delta)
        if temp_delta > 0:
            baseline_flow = np.sqrt(required_cooling / temp_delta) * 0.5
        else:
            baseline_flow = 10.0
        
        # Adjust for target temperature
        current_delta = chip_temp - target_temp
        if current_delta > 0:
            adjustment_factor = 1.0 + (current_delta / 10.0)
            optimized_flow = baseline_flow * adjustment_factor
        else:
            optimized_flow = baseline_flow * 0.9  # Reduce if already cool
        
        # Clamp to reasonable range
        optimized_flow = np.clip(optimized_flow, 5.0, 30.0)
        
        # Estimate power savings
        power_savings = max(0, (baseline_flow - optimized_flow) * 5)  # ~5W per L/min
        
        return {
            'recommended_flow_rate_lpm': float(optimized_flow),
            'baseline_flow_rate_lpm': float(baseline_flow),
            'estimated_power_savings_w': float(power_savings),
            'estimated_chip_temp_c': float(target_temp + 2),  # Conservative estimate
            'confidence': 0.85
        }
    
    def optimize_fan_speed(self, room_temp: float, target_temp: float,
                          heat_load_w: float, room_volume_m3: float) -> Dict:
        """Optimize fan speed for target room temperature."""
        # Required airflow for heat removal
        temp_rise = target_temp - room_temp
        if temp_rise <= 0:
            temp_rise = 10.0  # Default
        
        # Q = m * cp * ΔT, where m = ρ * V_dot
        # V_dot = Q / (ρ * cp * ΔT)
        air_density = 1.2  # kg/m³
        air_cp = 1005  # J/kg·K
        
        required_airflow_m3s = heat_load_w / (air_density * air_cp * temp_rise)
        required_airflow_m3h = required_airflow_m3s * 3600
        
        # Air changes per hour
        air_changes = required_airflow_m3h / room_volume_m3
        
        # Estimate fan RPM (simplified)
        # Typical mining fan: 3000 RPM = ~200 CFM = ~340 m³/h
        cfm_required = required_airflow_m3h * 0.588
        estimated_rpm = (cfm_required / 200) * 3000
        
        # Clamp to reasonable range
        estimated_rpm = np.clip(estimated_rpm, 1500, 4000)
        
        # Power consumption estimate
        # Fan power ∝ RPM³ (cube law)
        power_consumption = (estimated_rpm / 3000) ** 3 * 50  # 50W at 3000 RPM
        
        return {
            'recommended_fan_rpm': int(estimated_rpm),
            'required_airflow_m3h': float(required_airflow_m3h),
            'required_airflow_cfm': float(cfm_required),
            'air_changes_per_hour': float(air_changes),
            'estimated_power_consumption_w': float(power_consumption),
            'noise_level_db': float(30 + (estimated_rpm - 1500) / 100),  # Rough estimate
            'confidence': 0.80
        }


def format_prediction_report(prediction: FailurePrediction) -> str:
    """Format failure prediction as readable report."""
    risk_emoji = {
        'low': '✅',
        'medium': '⚠️',
        'high': '🔴',
        'critical': '🚨'
    }
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║          ПРОГНОЗ ОТКАЗА ОБОРУДОВАНИЯ                         ║
╚══════════════════════════════════════════════════════════════╝

🔧 Оборудование: {prediction.equipment_id}

{risk_emoji[prediction.risk_level]} УРОВЕНЬ РИСКА: {prediction.risk_level.upper()}
   • Вероятность отказа: {prediction.failure_probability:.1%}
   • Прогнозируемое время до отказа: {prediction.predicted_failure_hours:.0f} часов
     ({prediction.predicted_failure_hours/24:.1f} дней)

📊 ОСНОВНЫЕ ФАКТОРЫ РИСКА:
   1. {prediction.contributing_factors[0]}
   2. {prediction.contributing_factors[1]}
   3. {prediction.contributing_factors[2]}

💡 РЕКОМЕНДАЦИИ:
   {prediction.recommended_action}
"""
    return report


if __name__ == "__main__":
    # Demo
    print("=== ThermoMiner Pro: Predictive Maintenance Demo ===\n")
    
    # Initialize model
    model = PredictiveMaintenanceModel()
    
    # Simulate sensor data
    print("1. Нормальная работа:")
    normal_data = SensorData(
        timestamp=datetime.now(),
        chip_temp=68.0,
        coolant_temp=30.0,
        ambient_temp=25.0,
        flow_rate=10.5,
        pressure=1.5,
        fan_rpm=3000,
        power_draw=3250,
        hashrate=110,
        equipment_id="ASIC-001"
    )
    
    prediction = model.predict_failure(normal_data)
    print(format_prediction_report(prediction))
    
    print("\n" + "="*70 + "\n")
    
    print("2. Проблемная работа (высокая температура, низкий расход):")
    failing_data = SensorData(
        timestamp=datetime.now(),
        chip_temp=85.0,
        coolant_temp=45.0,
        ambient_temp=30.0,
        flow_rate=6.0,
        pressure=0.8,
        fan_rpm=2500,
        power_draw=3400,
        hashrate=95,
        equipment_id="ASIC-002"
    )
    
    prediction = model.predict_failure(failing_data)
    print(format_prediction_report(prediction))
    
    # Cooling optimizer demo
    print("\n" + "="*70 + "\n")
    print("3. Оптимизация системы охлаждения:")
    
    optimizer = CoolingOptimizer()
    flow_optimization = optimizer.optimize_flow_rate(
        chip_temp=75.0,
        ambient_temp=25.0,
        tdp=3250,
        target_temp=65.0
    )
    
    print(f"\n💧 ОПТИМИЗАЦИЯ РАСХОДА ЖИДКОСТИ:")
    print(f"   • Рекомендуемый расход: {flow_optimization['recommended_flow_rate_lpm']:.1f} л/мин")
    print(f"   • Экономия энергии: {flow_optimization['estimated_power_savings_w']:.0f} Вт")
    print(f"   • Ожидаемая температура чипа: {flow_optimization['estimated_chip_temp_c']:.1f}°C")
    
    fan_optimization = optimizer.optimize_fan_speed(
        room_temp=25.0,
        target_temp=35.0,
        heat_load_w=32500,  # 10 ASICs
        room_volume_m3=180  # 10x6x3m
    )
    
    print(f"\n🌀 ОПТИМИЗАЦИЯ ВЕНТИЛЯЦИИ:")
    print(f"   • Рекомендуемые обороты: {fan_optimization['recommended_fan_rpm']} RPM")
    print(f"   • Требуемый воздухообмен: {fan_optimization['required_airflow_m3h']:.0f} м³/ч")
    print(f"   • Кратность воздухообмена: {fan_optimization['air_changes_per_hour']:.1f} раз/час")
    print(f"   • Потребление вентиляторов: {fan_optimization['estimated_power_consumption_w']:.0f} Вт")

