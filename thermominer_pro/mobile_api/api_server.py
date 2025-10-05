"""
REST API Server for ThermoMiner Pro Mobile App
Provides endpoints for monitoring and control
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from typing import Dict, List
import json
from pathlib import Path


app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app


# In-memory storage (replace with database in production)
equipment_data = {}
alerts = []
historical_data = []


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get overall system status."""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'equipment_count': len(equipment_data),
        'active_alerts': len([a for a in alerts if a['active']])
    })


@app.route('/api/equipment', methods=['GET'])
def get_all_equipment():
    """Get all equipment status."""
    return jsonify({
        'equipment': list(equipment_data.values()),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/equipment/<equipment_id>', methods=['GET'])
def get_equipment(equipment_id: str):
    """Get specific equipment status."""
    if equipment_id in equipment_data:
        return jsonify(equipment_data[equipment_id])
    else:
        return jsonify({'error': 'Equipment not found'}), 404


@app.route('/api/equipment/<equipment_id>', methods=['POST'])
def update_equipment(equipment_id: str):
    """Update equipment data (from sensors)."""
    data = request.json
    
    equipment_data[equipment_id] = {
        'id': equipment_id,
        'chip_temp': data.get('chip_temp', 0),
        'coolant_temp': data.get('coolant_temp', 0),
        'ambient_temp': data.get('ambient_temp', 0),
        'flow_rate': data.get('flow_rate', 0),
        'pressure': data.get('pressure', 0),
        'fan_rpm': data.get('fan_rpm', 0),
        'power_draw': data.get('power_draw', 0),
        'hashrate': data.get('hashrate', 0),
        'is_operational': data.get('is_operational', True),
        'last_update': datetime.now().isoformat()
    }
    
    # Check for alerts
    check_alerts(equipment_id, equipment_data[equipment_id])
    
    # Store historical data
    historical_data.append({
        'equipment_id': equipment_id,
        'timestamp': datetime.now().isoformat(),
        'data': equipment_data[equipment_id].copy()
    })
    
    # Keep only last 1000 records
    if len(historical_data) > 1000:
        historical_data.pop(0)
    
    return jsonify({'status': 'updated', 'equipment': equipment_data[equipment_id]})


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts."""
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    
    if active_only:
        filtered_alerts = [a for a in alerts if a['active']]
    else:
        filtered_alerts = alerts
    
    return jsonify({
        'alerts': filtered_alerts,
        'count': len(filtered_alerts)
    })


@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    for alert in alerts:
        if alert['id'] == alert_id:
            alert['active'] = False
            alert['acknowledged_at'] = datetime.now().isoformat()
            return jsonify({'status': 'acknowledged', 'alert': alert})
    
    return jsonify({'error': 'Alert not found'}), 404


@app.route('/api/history/<equipment_id>', methods=['GET'])
def get_history(equipment_id: str):
    """Get historical data for equipment."""
    hours = int(request.args.get('hours', 24))
    
    equipment_history = [
        h for h in historical_data
        if h['equipment_id'] == equipment_id
    ]
    
    # Limit to requested time range
    equipment_history = equipment_history[-hours*60:]  # Assuming 1 reading per minute
    
    return jsonify({
        'equipment_id': equipment_id,
        'history': equipment_history,
        'count': len(equipment_history)
    })


@app.route('/api/roi', methods=['POST'])
def calculate_roi():
    """Calculate ROI based on provided parameters."""
    data = request.json
    
    # Import ROI calculator
    from core.roi_calculator import ROICalculator, MiningConfig
    
    config = MiningConfig(
        asic_model=data.get('asic_model', 'Unknown'),
        hashrate_ths=data.get('hashrate_ths', 110),
        power_consumption_w=data.get('power_consumption_w', 3250),
        quantity=data.get('quantity', 1),
        asic_price_usd=data.get('asic_price_usd', 2500),
        cooling_type=data.get('cooling_type', 'air'),
        cooling_capex_usd=data.get('cooling_capex_usd', 500),
        cooling_power_w=data.get('cooling_power_w', 120),
        electricity_price_kwh=data.get('electricity_price_kwh', 0.10),
        pool_fee_percent=data.get('pool_fee_percent', 1.0),
        maintenance_monthly_usd=data.get('maintenance_monthly_usd', 0)
    )
    
    calculator = ROICalculator(config)
    roi = calculator.calculate_roi()
    
    return jsonify(roi)


@app.route('/api/predict_failure', methods=['POST'])
def predict_failure():
    """Predict equipment failure based on sensor data."""
    data = request.json
    
    from ml.predictive_maintenance import PredictiveMaintenanceModel, SensorData
    
    sensor_data = SensorData(
        timestamp=datetime.now(),
        chip_temp=data.get('chip_temp', 65),
        coolant_temp=data.get('coolant_temp', 30),
        ambient_temp=data.get('ambient_temp', 25),
        flow_rate=data.get('flow_rate', 10),
        pressure=data.get('pressure', 1.5),
        fan_rpm=data.get('fan_rpm', 3000),
        power_draw=data.get('power_draw', 3250),
        hashrate=data.get('hashrate', 110),
        equipment_id=data.get('equipment_id', 'unknown')
    )
    
    model = PredictiveMaintenanceModel()
    prediction = model.predict_failure(sensor_data)
    
    return jsonify({
        'equipment_id': prediction.equipment_id,
        'failure_probability': prediction.failure_probability,
        'predicted_failure_hours': prediction.predicted_failure_hours,
        'risk_level': prediction.risk_level,
        'recommended_action': prediction.recommended_action,
        'contributing_factors': prediction.contributing_factors
    })


@app.route('/api/optimize_cooling', methods=['POST'])
def optimize_cooling():
    """Get cooling optimization recommendations."""
    data = request.json
    
    from ml.predictive_maintenance import CoolingOptimizer
    
    optimizer = CoolingOptimizer()
    
    if data.get('cooling_type') == 'hydro':
        optimization = optimizer.optimize_flow_rate(
            chip_temp=data.get('chip_temp', 70),
            ambient_temp=data.get('ambient_temp', 25),
            tdp=data.get('tdp', 3250),
            target_temp=data.get('target_temp', 65)
        )
    else:
        optimization = optimizer.optimize_fan_speed(
            room_temp=data.get('room_temp', 25),
            target_temp=data.get('target_temp', 35),
            heat_load_w=data.get('heat_load_w', 32500),
            room_volume_m3=data.get('room_volume_m3', 180)
        )
    
    return jsonify(optimization)


def check_alerts(equipment_id: str, data: Dict):
    """Check for alert conditions and create alerts."""
    # Temperature alerts
    if data['chip_temp'] > 80:
        create_alert(
            equipment_id=equipment_id,
            severity='warning' if data['chip_temp'] < 90 else 'critical',
            message=f"Высокая температура чипа: {data['chip_temp']:.1f}°C",
            type='temperature'
        )
    
    # Flow rate alerts
    if data.get('flow_rate', 10) < 5:
        create_alert(
            equipment_id=equipment_id,
            severity='warning',
            message=f"Низкий расход охлаждающей жидкости: {data['flow_rate']:.1f} л/мин",
            type='flow_rate'
        )
    
    # Hashrate alerts
    if data.get('hashrate', 110) < 90:
        create_alert(
            equipment_id=equipment_id,
            severity='info',
            message=f"Снижение хешрейта: {data['hashrate']:.1f} TH/s",
            type='performance'
        )


def create_alert(equipment_id: str, severity: str, message: str, type: str):
    """Create a new alert."""
    alert = {
        'id': f"alert_{len(alerts)}_{datetime.now().timestamp()}",
        'equipment_id': equipment_id,
        'severity': severity,
        'message': message,
        'type': type,
        'timestamp': datetime.now().isoformat(),
        'active': True,
        'acknowledged_at': None
    }
    
    alerts.append(alert)
    
    # Keep only last 100 alerts
    if len(alerts) > 100:
        alerts.pop(0)


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard summary data."""
    total_equipment = len(equipment_data)
    operational = sum(1 for e in equipment_data.values() if e.get('is_operational', True))
    
    avg_chip_temp = 0
    total_hashrate = 0
    total_power = 0
    
    if equipment_data:
        avg_chip_temp = sum(e.get('chip_temp', 0) for e in equipment_data.values()) / total_equipment
        total_hashrate = sum(e.get('hashrate', 0) for e in equipment_data.values())
        total_power = sum(e.get('power_draw', 0) for e in equipment_data.values())
    
    return jsonify({
        'summary': {
            'total_equipment': total_equipment,
            'operational': operational,
            'offline': total_equipment - operational,
            'avg_chip_temp': avg_chip_temp,
            'total_hashrate_ths': total_hashrate,
            'total_power_kw': total_power / 1000
        },
        'active_alerts': len([a for a in alerts if a['active']]),
        'critical_alerts': len([a for a in alerts if a['active'] and a['severity'] == 'critical']),
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("🚀 ThermoMiner Pro API Server")
    print("=" * 50)
    print("API Endpoints:")
    print("  GET  /api/status")
    print("  GET  /api/equipment")
    print("  GET  /api/equipment/<id>")
    print("  POST /api/equipment/<id>")
    print("  GET  /api/alerts")
    print("  POST /api/alerts/<id>/acknowledge")
    print("  GET  /api/history/<id>")
    print("  POST /api/roi")
    print("  POST /api/predict_failure")
    print("  POST /api/optimize_cooling")
    print("  GET  /api/dashboard")
    print("=" * 50)
    print("\nServer starting on http://0.0.0.0:5000")
    print("Для мобильного приложения используйте: http://<your-ip>:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

