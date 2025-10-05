# ThermoMiner Pro - Mobile API Documentation

## 📱 Мобильное приложение

ThermoMiner Pro предоставляет REST API для разработки мобильного приложения на iOS/Android.

### Запуск API сервера

```bash
cd thermominer_pro
python mobile_api/api_server.py
```

Сервер запустится на `http://0.0.0.0:5000`

### API Endpoints

#### 1. Статус системы
```
GET /api/status
```

**Ответ:**
```json
{
  "status": "online",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0",
  "equipment_count": 10,
  "active_alerts": 2
}
```

#### 2. Список оборудования
```
GET /api/equipment
```

**Ответ:**
```json
{
  "equipment": [
    {
      "id": "ASIC-001",
      "chip_temp": 68.5,
      "coolant_temp": 30.2,
      "ambient_temp": 25.0,
      "flow_rate": 10.5,
      "pressure": 1.5,
      "fan_rpm": 3000,
      "power_draw": 3250,
      "hashrate": 110.0,
      "is_operational": true,
      "last_update": "2024-01-15T10:30:00"
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

#### 3. Данные конкретного ASIC
```
GET /api/equipment/<equipment_id>
```

#### 4. Обновление данных с датчиков
```
POST /api/equipment/<equipment_id>
Content-Type: application/json

{
  "chip_temp": 68.5,
  "coolant_temp": 30.2,
  "ambient_temp": 25.0,
  "flow_rate": 10.5,
  "pressure": 1.5,
  "fan_rpm": 3000,
  "power_draw": 3250,
  "hashrate": 110.0,
  "is_operational": true
}
```

#### 5. Алерты
```
GET /api/alerts?active_only=true
```

**Ответ:**
```json
{
  "alerts": [
    {
      "id": "alert_1_1234567890",
      "equipment_id": "ASIC-001",
      "severity": "warning",
      "message": "Высокая температура чипа: 85.0°C",
      "type": "temperature",
      "timestamp": "2024-01-15T10:25:00",
      "active": true,
      "acknowledged_at": null
    }
  ],
  "count": 1
}
```

#### 6. Подтверждение алерта
```
POST /api/alerts/<alert_id>/acknowledge
```

#### 7. История данных
```
GET /api/history/<equipment_id>?hours=24
```

#### 8. Расчёт ROI
```
POST /api/roi
Content-Type: application/json

{
  "asic_model": "Antminer S19 Pro",
  "hashrate_ths": 110,
  "power_consumption_w": 3250,
  "quantity": 10,
  "asic_price_usd": 2500,
  "cooling_type": "hydro",
  "cooling_capex_usd": 5000,
  "cooling_power_w": 500,
  "electricity_price_kwh": 0.08,
  "pool_fee_percent": 1.0,
  "maintenance_monthly_usd": 200
}
```

#### 9. Предсказание отказа
```
POST /api/predict_failure
Content-Type: application/json

{
  "equipment_id": "ASIC-001",
  "chip_temp": 75.0,
  "coolant_temp": 35.0,
  "ambient_temp": 28.0,
  "flow_rate": 8.5,
  "pressure": 1.2,
  "fan_rpm": 2800,
  "power_draw": 3300,
  "hashrate": 105
}
```

**Ответ:**
```json
{
  "equipment_id": "ASIC-001",
  "failure_probability": 0.35,
  "predicted_failure_hours": 168,
  "risk_level": "medium",
  "recommended_action": "Увеличьте частоту мониторинга, проверьте систему охлаждения",
  "contributing_factors": ["chip_temp", "flow_rate", "hashrate"]
}
```

#### 10. Оптимизация охлаждения
```
POST /api/optimize_cooling
Content-Type: application/json

{
  "cooling_type": "hydro",
  "chip_temp": 75.0,
  "ambient_temp": 25.0,
  "tdp": 3250,
  "target_temp": 65.0
}
```

#### 11. Dashboard сводка
```
GET /api/dashboard
```

**Ответ:**
```json
{
  "summary": {
    "total_equipment": 10,
    "operational": 9,
    "offline": 1,
    "avg_chip_temp": 68.5,
    "total_hashrate_ths": 990,
    "total_power_kw": 29.25
  },
  "active_alerts": 2,
  "critical_alerts": 0,
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## 🔧 Разработка мобильного приложения

### Рекомендуемые технологии:

#### iOS (Swift)
- SwiftUI для UI
- Combine для reactive programming
- URLSession для API calls

#### Android (Kotlin)
- Jetpack Compose для UI
- Retrofit для API calls
- Coroutines для async operations

#### Cross-platform (React Native / Flutter)
- React Native: Expo, React Navigation, Axios
- Flutter: Provider/Riverpod, Dio, Flutter Charts

### Основные экраны:

1. **Dashboard** - общая сводка фермы
2. **Equipment List** - список всех ASIC
3. **Equipment Detail** - детали конкретного ASIC с графиками
4. **Alerts** - список активных алертов
5. **ROI Calculator** - калькулятор окупаемости
6. **Settings** - настройки приложения

### Push-уведомления:

Для push-уведомлений рекомендуется интегрировать:
- Firebase Cloud Messaging (FCM) для Android
- Apple Push Notification Service (APNS) для iOS

### Безопасность:

- Используйте HTTPS (SSL/TLS)
- Добавьте JWT authentication
- Ограничьте доступ по IP (опционально)
- Используйте API keys

---

## 📊 Примеры интеграции

### Python (для тестирования)
```python
import requests

# Get status
response = requests.get('http://localhost:5000/api/status')
print(response.json())

# Update equipment data
data = {
    'chip_temp': 68.5,
    'coolant_temp': 30.2,
    'flow_rate': 10.5,
    'hashrate': 110.0
}
response = requests.post('http://localhost:5000/api/equipment/ASIC-001', json=data)
print(response.json())
```

### JavaScript (React Native)
```javascript
// Get equipment list
fetch('http://YOUR_SERVER_IP:5000/api/equipment')
  .then(response => response.json())
  .then(data => {
    console.log('Equipment:', data.equipment);
  })
  .catch(error => console.error('Error:', error));

// Update equipment
const updateData = {
  chip_temp: 68.5,
  coolant_temp: 30.2,
  flow_rate: 10.5,
  hashrate: 110.0
};

fetch('http://YOUR_SERVER_IP:5000/api/equipment/ASIC-001', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(updateData),
})
  .then(response => response.json())
  .then(data => console.log('Updated:', data))
  .catch(error => console.error('Error:', error));
```

---

## 🚀 Деплой в продакшн

### Использование Gunicorn (рекомендуется)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 mobile_api.api_server:app
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "mobile_api.api_server:app"]
```

### Nginx reverse proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📝 TODO для полноценного мобильного приложения

- [ ] Добавить JWT authentication
- [ ] Реализовать WebSocket для real-time updates
- [ ] Добавить push-уведомления через FCM/APNS
- [ ] Создать базу данных (PostgreSQL/MongoDB)
- [ ] Добавить rate limiting
- [ ] Реализовать user management
- [ ] Добавить графики в API responses
- [ ] Создать admin panel

