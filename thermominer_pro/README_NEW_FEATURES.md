# ThermoMiner Pro - Новые Возможности

## 🎉 Реализованные фичи

### 1. 📊 3D Визуализация Тепловых Карт

**Модуль:** `visualization/thermal_3d.py`

Интерактивная 3D визуализация помещения с тепловыми картами и воздушными потоками.

**Возможности:**
- 3D модель помещения с расстановкой ASIC
- Тепловая карта с цветовой индикацией температур
- Визуализация воздушных потоков
- Анализ горячих точек (hotspots)
- Экспорт в HTML для интерактивного просмотра

**Использование:**
```python
from visualization import ThermalMapper3D, RoomConfig, AsicPosition

# Создание комнаты
room = RoomConfig(length=10, width=6, height=3, inlet_temp=25, outlet_temp=35)
mapper = ThermalMapper3D(room)

# Добавление ASIC
mapper.add_asic_rack(2, 2, 1, count=10, tdp_per_unit=3250, model="Antminer S19")

# Анализ горячих точек
analysis = mapper.get_hotspot_analysis()
print(f"Максимальная температура: {analysis['max_temp']:.1f}°C")

# Создание интерактивной визуализации
fig = mapper.create_plotly_figure()
fig.write_html("thermal_map_3d.html")
```

**Демо:**
```bash
cd thermominer_pro
python -m visualization.thermal_3d
```

---

### 2. 💰 Калькулятор ROI с Криптовалютными API

**Модуль:** `core/roi_calculator.py`

Расчёт окупаемости с интеграцией CoinGecko API для актуальных цен BTC и сложности сети.

**Возможности:**
- Расчёт дневной/месячной/годовой прибыли
- Интеграция с CoinGecko API (актуальная цена BTC)
- Учёт сложности сети и хешрейта
- Сравнение воздушного vs жидкостного охлаждения
- Прогноз на 12 месяцев с учётом роста сложности
- Расчёт точки безубыточности

**Использование:**
```python
from core.roi_calculator import ROICalculator, MiningConfig

config = MiningConfig(
    asic_model="Antminer S19 Pro",
    hashrate_ths=110,
    power_consumption_w=3250,
    quantity=10,
    asic_price_usd=2500,
    cooling_type='hydro',
    cooling_capex_usd=5000,
    cooling_power_w=500,
    electricity_price_kwh=0.08
)

calc = ROICalculator(config)
roi = calc.calculate_roi()

print(f"Прибыль в день: ${roi['profit_per_day']:.2f}")
print(f"Срок окупаемости: {roi['payback_months']:.1f} месяцев")
print(f"ROI за 1 год: {roi['roi_1_year_percent']:.1f}%")

# Прогноз на 12 месяцев
projections = calc.generate_projection(12, difficulty_increase_monthly=3.0)
```

**Демо:**
```bash
cd thermominer_pro
python -m core.roi_calculator
```

---

### 3. 🌙 Тёмная Тема

**Модуль:** `ui/themes.py`

Полная поддержка светлой и тёмной темы с сохранением настроек.

**Возможности:**
- Переключение между светлой и тёмной темой
- Автоматическое сохранение предпочтений
- Поддержка Tkinter, Matplotlib, Plotly
- Кнопка переключения в GUI

**Использование:**
```python
from ui.themes import ThemeManager, create_theme_toggle_button

# Инициализация
theme_manager = ThemeManager()

# Получить текущую тему
current_theme = theme_manager.get_theme()
print(f"Текущая тема: {current_theme['name']}")

# Переключить тему
new_theme = theme_manager.toggle_theme()

# Применить к matplotlib
from ui.themes import apply_theme_to_matplotlib
apply_theme_to_matplotlib(theme_manager)

# Создать кнопку переключения в Tkinter
btn = create_theme_toggle_button(parent_widget, theme_manager, on_toggle_callback)
```

**Интеграция в GUI:**
Тёмная тема автоматически применяется ко всем элементам интерфейса при переключении.

---

### 4. 🤖 ML Оптимизация и Предсказание Отказов

**Модуль:** `ml/predictive_maintenance.py`

Машинное обучение для предсказания отказов оборудования и оптимизации параметров охлаждения.

**Возможности:**
- Предсказание вероятности отказа оборудования
- Прогноз времени до отказа
- Определение факторов риска
- Оптимизация расхода охлаждающей жидкости
- Оптимизация оборотов вентиляторов
- Рекомендации по техобслуживанию

**Использование:**
```python
from ml import PredictiveMaintenanceModel, SensorData, CoolingOptimizer
from datetime import datetime

# Предсказание отказа
model = PredictiveMaintenanceModel()

sensor_data = SensorData(
    timestamp=datetime.now(),
    chip_temp=75.0,
    coolant_temp=35.0,
    ambient_temp=28.0,
    flow_rate=8.5,
    pressure=1.2,
    fan_rpm=2800,
    power_draw=3300,
    hashrate=105,
    equipment_id="ASIC-001"
)

prediction = model.predict_failure(sensor_data)
print(f"Вероятность отказа: {prediction.failure_probability:.1%}")
print(f"Время до отказа: {prediction.predicted_failure_hours:.0f} часов")
print(f"Уровень риска: {prediction.risk_level}")
print(f"Рекомендация: {prediction.recommended_action}")

# Оптимизация охлаждения
optimizer = CoolingOptimizer()

flow_optimization = optimizer.optimize_flow_rate(
    chip_temp=75.0,
    ambient_temp=25.0,
    tdp=3250,
    target_temp=65.0
)

print(f"Рекомендуемый расход: {flow_optimization['recommended_flow_rate_lpm']:.1f} л/мин")
print(f"Экономия энергии: {flow_optimization['estimated_power_savings_w']:.0f} Вт")
```

**Демо:**
```bash
cd thermominer_pro
python -m ml.predictive_maintenance
```

---

### 5. 📱 Мобильное API

**Модуль:** `mobile_api/api_server.py`

REST API для разработки мобильного приложения iOS/Android.

**Возможности:**
- Мониторинг всего оборудования
- Получение алертов в реальном времени
- История данных
- Расчёт ROI через API
- Предсказание отказов
- Оптимизация охлаждения
- Dashboard сводка

**Запуск сервера:**
```bash
cd thermominer_pro
python mobile_api/api_server.py
```

Сервер запустится на `http://0.0.0.0:5000`

**API Endpoints:**
```
GET  /api/status                      - Статус системы
GET  /api/equipment                   - Список оборудования
GET  /api/equipment/<id>              - Данные конкретного ASIC
POST /api/equipment/<id>              - Обновить данные
GET  /api/alerts                      - Получить алерты
POST /api/alerts/<id>/acknowledge     - Подтвердить алерт
GET  /api/history/<id>                - История данных
POST /api/roi                         - Расчёт ROI
POST /api/predict_failure             - Предсказание отказа
POST /api/optimize_cooling            - Оптимизация охлаждения
GET  /api/dashboard                   - Dashboard сводка
```

**Пример использования:**
```python
import requests

# Получить статус
response = requests.get('http://localhost:5000/api/status')
print(response.json())

# Обновить данные ASIC
data = {
    'chip_temp': 68.5,
    'coolant_temp': 30.2,
    'flow_rate': 10.5,
    'hashrate': 110.0
}
response = requests.post('http://localhost:5000/api/equipment/ASIC-001', json=data)
```

**Документация:** См. `mobile_api/README_MOBILE.md`

---

### 6. 🚨 Симулятор Аварийных Сценариев

**Модуль:** `simulation/emergency_simulator.py`

Симуляция отказов оборудования и тепловых процессов.

**Возможности:**
- Симуляция отказа насоса охлаждения
- Симуляция отказа вентилятора
- Симуляция утечки охлаждающей жидкости
- Расчёт времени до критических температур
- Графики температурных процессов
- Рекомендации по резервированию

**Использование:**
```python
from simulation import EmergencySimulator

simulator = EmergencySimulator(
    initial_chip_temp=65.0,
    initial_coolant_temp=30.0,
    ambient_temp=25.0,
    tdp=3250.0
)

# Симуляция отказа насоса
states, analysis = simulator.simulate_pump_failure(
    duration_seconds=600,
    failure_time=60
)

print(f"Время до критической температуры: {analysis['time_to_critical']:.0f} сек")
print(f"Максимальная температура: {analysis['max_temp']:.1f}°C")
print(f"Оборудование выжило: {analysis['equipment_survived']}")

# Построить график
fig = simulator.plot_simulation(states, analysis, 'pump_failure.png')
```

**Демо:**
```bash
cd thermominer_pro
python -m simulation.emergency_simulator
```

Создаст 3 графика:
- `pump_failure_simulation.png` - отказ насоса
- `fan_failure_simulation.png` - отказ вентилятора
- `coolant_leak_simulation.png` - утечка охлаждающей жидкости

---

## 📦 Установка зависимостей

```bash
cd thermominer_pro
pip install -r requirements.txt
```

**Новые зависимости:**
- `plotly` - интерактивные 3D графики
- `scikit-learn` - машинное обучение
- `Flask` - REST API сервер
- `Flask-CORS` - CORS для мобильного API
- `gunicorn` - production сервер

---

## 🚀 Быстрый старт

### 1. Запуск GUI с новыми фичами
```bash
cd thermominer_pro
python run_gui.py
```

В GUI теперь доступны:
- Кнопка переключения темы (🌙/☀️)
- Расширенный ROI калькулятор
- Интеграция с ML предсказаниями

### 2. Демонстрация всех фич
```bash
# 3D визуализация
python -m visualization.thermal_3d

# ROI калькулятор
python -m core.roi_calculator

# ML предсказания
python -m ml.predictive_maintenance

# Симулятор аварий
python -m simulation.emergency_simulator

# Мобильное API
python mobile_api/api_server.py
```

---

## 📊 Примеры использования

### Пример 1: Комплексный анализ фермы

```python
from visualization import ThermalMapper3D, RoomConfig
from core.roi_calculator import ROICalculator, MiningConfig
from ml import PredictiveMaintenanceModel, SensorData
from datetime import datetime

# 1. Создать 3D модель
room = RoomConfig(length=10, width=6, height=3)
mapper = ThermalMapper3D(room)
mapper.add_asic_rack(2, 2, 1, count=10, tdp_per_unit=3250)

# 2. Анализ горячих точек
hotspots = mapper.get_hotspot_analysis()
print(f"Максимальная температура: {hotspots['max_temp']:.1f}°C")

# 3. Расчёт ROI
config = MiningConfig(
    asic_model="Antminer S19 Pro",
    hashrate_ths=110,
    power_consumption_w=3250,
    quantity=10,
    asic_price_usd=2500,
    cooling_type='hydro',
    cooling_capex_usd=5000,
    cooling_power_w=500,
    electricity_price_kwh=0.08
)

calc = ROICalculator(config)
roi = calc.calculate_roi()
print(f"ROI за 1 год: {roi['roi_1_year_percent']:.1f}%")

# 4. Предсказание отказов
model = PredictiveMaintenanceModel()
sensor_data = SensorData(
    timestamp=datetime.now(),
    chip_temp=hotspots['max_temp'],
    coolant_temp=30.0,
    ambient_temp=25.0,
    flow_rate=10.0,
    pressure=1.5,
    fan_rpm=3000,
    power_draw=3250,
    hashrate=110,
    equipment_id="ASIC-001"
)

prediction = model.predict_failure(sensor_data)
print(f"Риск отказа: {prediction.risk_level}")
```

### Пример 2: Мониторинг через мобильное API

```python
import requests
import time

API_URL = "http://localhost:5000"

# Цикл мониторинга
while True:
    # Обновить данные с датчиков
    sensor_data = {
        'chip_temp': read_temperature_sensor(),
        'coolant_temp': read_coolant_temp(),
        'flow_rate': read_flow_meter(),
        'hashrate': read_hashrate()
    }
    
    response = requests.post(
        f"{API_URL}/api/equipment/ASIC-001",
        json=sensor_data
    )
    
    # Проверить алерты
    alerts = requests.get(f"{API_URL}/api/alerts?active_only=true").json()
    
    if alerts['count'] > 0:
        print(f"⚠️ Активных алертов: {alerts['count']}")
        for alert in alerts['alerts']:
            print(f"  - {alert['message']}")
    
    time.sleep(60)  # Обновление каждую минуту
```

---

## 🎯 Следующие шаги

### Готово ✅
- [x] 3D визуализация тепловых карт
- [x] ROI калькулятор с криптовалютными API
- [x] Тёмная тема
- [x] ML оптимизация и предсказание отказов
- [x] Мобильное API
- [x] Симулятор аварийных сценариев

### В разработке 🚧
- [ ] Web-интерфейс (Django + React)
- [ ] PDF генератор отчётов
- [ ] Автообновление базы данных ASIC
- [ ] WebSocket для real-time обновлений
- [ ] Мобильное приложение (React Native)

---

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте логи в консоли
2. Убедитесь, что все зависимости установлены
3. Проверьте версию Python (требуется 3.11+)

**Основные команды для диагностики:**
```bash
# Проверить версию Python
python --version

# Установить зависимости
pip install -r requirements.txt

# Запустить тесты
python -m pytest

# Проверить API
curl http://localhost:5000/api/status
```

