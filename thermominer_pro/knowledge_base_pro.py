"""
ThermoMiner Pro - Knowledge Base PRO
Interactive thermal engineering guides and reference materials
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json
import math


@dataclass
class KnowledgeArticle:
    """Structured knowledge article with interactive elements."""
    id: str
    title: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    content: str
    interactive_elements: Dict[str, Any]
    prerequisites: List[str]
    related_articles: List[str]


class KnowledgeBasePRO:
    """Comprehensive knowledge base for thermal engineering in mining."""

    def __init__(self):
        self.articles = {}
        self.categories = {}
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with core thermal engineering content."""

        # Basic Thermodynamics
        self._add_article(KnowledgeArticle(
            id="thermo_basics",
            title="Основы Теплофизики для Майнеров",
            category="thermodynamics",
            difficulty="beginner",
            content="""
# Основы Теплофизики для Майнеров

## Теплопередача: Три Основных Механизма

### 1. Теплопроводность (Conduction)
Передача тепла через материал без перемещения вещества.

**Формула теплопроводности (закон Фурье):**
```
Q = -k * A * dT/dx
```
где:
- Q: Тепловой поток [Вт]
- k: Коэффициент теплопроводности [Вт/м·K]
- A: Площадь поперечного сечения [м²]
- dT/dx: Градиент температуры [K/м]

**Примеры коэффициентов теплопроводности:**
- Медь: 400 Вт/м·K (отличный проводник)
- Алюминий: 237 Вт/м·K
- Вода: 0.6 Вт/м·K
- Воздух: 0.024 Вт/м·K (плохой проводник)

### 2. Конвекция (Convection)
Передача тепла через движение жидкости или газа.

**Формула конвективного теплообмена:**
```
Q = h * A * ΔT
```
где:
- h: Коэффициент теплоотдачи [Вт/м²·K]
- A: Площадь поверхности [м²]
- ΔT: Разность температур [K]

### 3. Тепловое Излучение (Radiation)
Передача тепла через электромагнитные волны.

**Закон Стефана-Больцмана:**
```
Q = ε * σ * A * (T₁⁴ - T₂⁴)
```
где:
- ε: Степень черноты поверхности
- σ: Постоянная Стефана-Больцмана (5.67×10⁻⁸ Вт/м²·K⁴)
- A: Площадь поверхности [м²]
- T: Абсолютная температура [K]
            """,
            interactive_elements={
                "thermal_conductivity_calculator": {
                    "type": "calculator",
                    "formula": "Q = k * A * dT / dx",
                    "inputs": ["k", "A", "dT", "dx"],
                    "units": ["Вт/м·K", "м²", "K", "м"]
                },
                "heat_transfer_comparison": {
                    "type": "comparison_chart",
                    "materials": ["copper", "aluminum", "water", "air"],
                    "property": "thermal_conductivity"
                }
            },
            prerequisites=[],
            related_articles=["convection_basics", "asic_thermal_design"]
        ))

        # Convection Basics
        self._add_article(KnowledgeArticle(
            id="convection_basics",
            title="Конвекция: Естественная и Принудительная",
            category="heat_transfer",
            difficulty="intermediate",
            content="""
# Конвекция: Движение Тепла с Потоком

## Естественная Конвекция
Тепло переносится за счет изменения плотности жидкости/газа при нагреве.

**Критерий Грасгофа (Gr):**
```
Gr = (g * β * ΔT * L³) / ν²
```
где:
- g: Ускорение свободного падения [м/с²]
- β: Коэффициент объемного расширения [1/K]
- ΔT: Разность температур [K]
- L: Характерный размер [м]
- ν: Кинематическая вязкость [м²/с]

## Принудительная Конвекция
Тепло переносится за счет внешнего воздействия (вентиляторы, насосы).

**Критерий Нуссельта (Nu):**
```
Nu = h * L / k
```
где:
- h: Коэффициент теплоотдачи [Вт/м²·K]
- L: Характерный размер [м]
- k: Коэффициент теплопроводности [Вт/м·K]

**Эмпирические корреляции для разных случаев:**

### Плоская Пластина (принудительная конвекция)
```
Nu = 0.664 * Re^0.5 * Pr^0.33  (для ламинарного режима)
Nu = 0.037 * Re^0.8 * Pr^0.33   (для турбулентного режима)
```

### Труба (внутреннее течение)
```
Nu = 3.66  (для ламинарного режима, постоянный тепловой поток)
Nu = 0.023 * Re^0.8 * Pr^0.4   (для турбулентного режима)
```

## Практические Следствия для Майнинга

1. **Вентиляторы ASIC**: Создают принудительную конвекцию
2. **Радиаторы**: Используют естественную + принудительную конвекцию
3. **Горячие Зоны**: Области с недостаточной конвекцией
            """,
            interactive_elements={
                "grashof_calculator": {
                    "type": "calculator",
                    "formula": "Gr = (g * beta * dT * L^3) / nu^2",
                    "inputs": ["g", "beta", "dT", "L", "nu"]
                },
                "nusselt_correlation_selector": {
                    "type": "selector",
                    "options": ["flat_plate_laminar", "flat_plate_turbulent", "pipe_laminar", "pipe_turbulent"],
                    "formulas": {
                        "flat_plate_laminar": "Nu = 0.664 * Re^0.5 * Pr^0.33",
                        "flat_plate_turbulent": "Nu = 0.037 * Re^0.8 * Pr^0.33",
                        "pipe_laminar": "Nu = 3.66",
                        "pipe_turbulent": "Nu = 0.023 * Re^0.8 * Pr^0.4"
                    }
                }
            },
            prerequisites=["thermo_basics"],
            related_articles=["fan_basics", "radiator_design"]
        ))

        # ASIC Thermal Design
        self._add_article(KnowledgeArticle(
            id="asic_thermal_design",
            title="Термический Дизайн ASIC-Майнеров",
            category="asic_engineering",
            difficulty="advanced",
            content="""
# Термический Дизайн ASIC-Майнеров

## Термическое Сопротивление
ASIC можно представить как цепочку термических сопротивлений:

```
T_junction → T_case → T_heatsink → T_ambient
    ↑           ↑           ↑           ↑
  R_jc        R_ch        R_ha      R_conv
```

**Общее термическое сопротивление:**
```
R_total = R_jc + R_ch + R_ha + R_conv
```

## Критические Температуры

### Junction Temperature (T_j)
Максимальная температура полупроводникового перехода.
- **Bitmain S19**: 90-95°C
- **MicroBT M50**: 100-105°C
- **Почему критично**: Превышение вызывает degradation кристалла

### Case Temperature (T_case)
Температура корпуса ASIC.
- **Безопасный предел**: 70-80°C
- **Влияет на**: Надежность компонентов, тепловое расширение

## Тепловые Характеристики Реальных Моделей

### Bitmain Antminer S19 Pro
- TDP: 100W
- R_jc: 0.2°C/W
- Вентиляторы: 120×120×25mm, 120 CFM
- Рекомендуемый ΔT: < 15°C через теплоотвод

### MicroBT Whatsminer M50S
- TDP: 126W
- R_jc: 0.19°C/W
- Вентиляторы: 120×120×25mm, 130 CFM
- Особенности: Более эффективное охлаждение

## Проблемы и Решения

### Hotspots (Горячие Точки)
**Причины:**
- Неравномерный контакт с радиатором
- Воздушные карманы в термопасте
- Недостаточный airflow

**Решения:**
- Использовать quality термопасту
- Применять thermal pads
- Оптимизировать airflow pattern

### Thermal Throttling
**Симптомы:**
- Падение hashrate
- Повышенное энергопотребление
- ASIC выключается

**Профилактика:**
- Мониторинг температуры в реальном времени
- Автоматическое управление вентиляторами
- Резервные охлаждающие системы
            """,
            interactive_elements={
                "thermal_resistance_calculator": {
                    "type": "calculator",
                    "formula": "T_total = T_ambient + Q * R_total",
                    "inputs": ["Q", "R_jc", "R_ch", "R_ha", "R_conv", "T_ambient"]
                },
                "asic_comparison_tool": {
                    "type": "comparison",
                    "asics": ["S19_Pro", "M50S", "S21_XP"],
                    "metrics": ["tdp", "thermal_resistance", "max_temp"]
                }
            },
            prerequisites=["thermo_basics", "convection_basics"],
            related_articles=["fan_basics", "thermal_interface_materials"]
        ))

        # Fan Engineering
        self._add_article(KnowledgeArticle(
            id="fan_basics",
            title="Вентиляторы: От CFM до Статического Давления",
            category="airflow_engineering",
            difficulty="intermediate",
            content="""
# Вентиляторы: Основы Аэродинамики для Майнинга

## Основные Характеристики Вентиляторов

### 1. Расход Воздуха (CFM - Cubic Feet per Minute)
Объем воздуха, перемещаемый вентилятором в минуту.

**Формула:**
```
CFM = (π * D² / 4) * v * 35.31
```
где:
- D: Диаметр вентилятора [м]
- v: Скорость воздуха [м/с]

### 2. Статическое Давление (Static Pressure)
Давление, создаваемое вентилятором против сопротивления.

**Измеряется в:**
- Pa (Паскали)
- mmH₂O (мм водяного столба)
- inH₂O (дюймы водяного столба)

### 3. Кривая P-Q (Pressure-Flow)
Зависимость между давлением и расходом воздуха.

**Важные Точки:**
- **Free Air**: Максимальный CFM при нулевом сопротивлении
- **Operating Point**: Рабочая точка на системе
- **Shut Off**: Нулевой расход при максимальном давлении

## Типы Вентиляторов для Майнинга

### Axial (Осевые)
- **Преимущества**: Высокий CFM, низкая стоимость
- **Применение**: Прямое охлаждение ASIC
- **Примеры**: 120×120×25mm, 80-150 CFM

### Centrifugal (Радиальные)
- **Преимущества**: Высокое статическое давление
- **Применение**: Дуктовая вентиляция, преодоление сопротивления
- **Примеры**: Inline duct fans, 6-12\" diameter

### Mixed Flow
- **Преимущества**: Комбинация высокого CFM и давления
- **Применение**: Баланс производительности и эффективности

## Аэродинамическое Сопротивление Сети

### Компоненты Сопротивления
1. **Фильтры**: 20-50 Pa
2. **Воздуховоды**: 1-5 Pa per meter
3. **Отводы и Колена**: 10-50 Pa
4. **Решетки**: 5-20 Pa

### Расчет Общего Сопротивления
```
ΔP_total = Σ(ζ_i * ρ * v² / 2) + Σ(λ * L / D * ρ * v² / 2)
```
где:
- ζ: Коэффициент местного сопротивления
- λ: Коэффициент трения
- ρ: Плотность воздуха [kg/m³]
- v: Скорость воздуха [m/s]

## Выбор Вентиляторов для ASIC

### Для Прямого Охлаждения
- **Тип**: Axial 120mm
- **CFM**: 80-120 per ASIC
- **Static Pressure**: 20-50 Pa
- **Примеры**: Noctua NF-A12x25, Delta AFB1212HH

### Для Дуктовой Системы
- **Тип**: Inline duct fans
- **CFM**: 400-1200 per duct
- **Static Pressure**: 200-600 Pa
- **Примеры**: Fantech FG series

## Оптимизация Производительности

### 1. Правильное Расположение
- **Push-Pull**: Вентиляторы с обеих сторон радиатора
- **Airflow Direction**: От intake к exhaust
- **Avoid Dead Zones**: Обеспечить равномерный поток

### 2. Управление Скоростью
- **PWM Control**: 4-pin вентиляторы
- **Temperature-Based**: Автоматическая регулировка
- **Power Efficiency**: Баланс между охлаждением и потреблением

### 3. Шум и Вибрация
- **Decoupling**: Антивибрационные крепления
- **Aerodynamic Design**: Оптимизированные лопасти
- **Operating Range**: Работа в оптимальной зоне
            """,
            interactive_elements={
                "fan_curve_analyzer": {
                    "type": "interactive_chart",
                    "x_axis": "CFM",
                    "y_axis": "Static_Pressure",
                    "fan_curves": ["Noctua_NF_A12", "Delta_AFB1212", "Fantech_FG6"]
                },
                "system_resistance_calculator": {
                    "type": "calculator",
                    "formula": "DP_total = sum(K_i * rho * v^2 / 2)",
                    "inputs": ["duct_length", "fittings_count", "filter_pressure_drop"]
                },
                "fan_selector": {
                    "type": "decision_tree",
                    "criteria": ["application", "required_cfm", "static_pressure", "noise_limit"]
                }
            },
            prerequisites=["convection_basics"],
            related_articles=["duct_design", "noise_control"]
        ))

        # Hydronics Engineering
        self._add_article(KnowledgeArticle(
            id="hydronics_basics",
            title="Гидравлика Систем Охлаждения",
            category="hydraulics",
            difficulty="advanced",
            content="""
# Гидравлика Систем Жидкостного Охлаждения

## Основные Параметры

### Расход (Flow Rate)
**Объемный расход:**
```
Q = V / t  [м³/с или л/мин]
```

**Массовый расход:**
```
ṁ = ρ * Q  [kg/с]
```

### Давление и Напор
**Давление:**
```
P = F / A  [Pa = N/м²]
```

**Напор (для насосов):**
```
H = P / (ρ * g)  [м]
```

## Гидравлическое Сопротивление

### Закон Дарси-Вейсбаха
```
ΔP = λ * (L/D) * (ρ * v² / 2)
```
где:
- λ: Коэффициент трения
- L/D: Относительная длина
- ρ: Плотность жидкости
- v: Скорость потока

### Коэффициент Трения
**Ламинарный режим (Re < 2300):**
```
λ = 64 / Re
```

**Турбулентный режим (Re > 2300):**
```
λ = 0.3164 / Re^0.25  (формула Блазиуса)
```

## Местные Сопротивления

### Типичные Коэффициенты ζ
- **Вход в трубу**: 0.5
- **Выход из трубы**: 1.0
- **Отвод 90°**: 1.0-1.5
- **Тройник**: 1.0-2.0
- **Клапан**: 2.0-10.0
- **Радиатор**: 2.0-5.0

### Общее Сопротивление Контура
```
ΔP_total = Σ(ζ_i) * (ρ * v² / 2) + Σ[λ * (L/D) * (ρ * v² / 2)]
```

## Характеристики Насосов

### Кривая H-Q (Напор-Расход)
```
H = H_max - K * Q²
```
где:
- H_max: Максимальный напор
- K: Коэффициент характеристики насоса
- Q: Расход

### Эффективность Насоса
```
η = P_гидр / P_электр
```
где:
- P_гидр = ΔP * Q: Гидравлическая мощность
- P_электр: Электрическая мощность

## Теплогидравлический Расчет

### Тепловой Баланс
```
Q_тепло = ṁ * c_p * ΔT
```
где:
- ṁ: Массовый расход
- c_p: Удельная теплоемкость
- ΔT: Изменение температуры

### Подбор Насоса
1. **Расчет требуемого напора:**
   ```
   H_треб = ΔP_total / (ρ * g) + H_геом + запас
   ```

2. **Выбор рабочей точки:**
   - Пересечение кривой H-Q насоса с характеристикой системы

3. **Проверка эффективности:**
   - Рабочая точка должна быть в зоне максимального КПД

## Практические Аспекты

### Кавитация
**Критическое давление:**
```
P_кав > P_насыщ + ρ * g * H + ρ * v² / 2
```

**Признаки кавитации:**
- Шум и вибрация
- Падение производительности
- Повреждение насоса

### Материалы Контура
**Рекомендации:**
- **Трубы**: Медь, нержавеющая сталь, PEX
- **Фитинги**: Бронза, латунь (избегать алюминия с медью)
- **Насос**: Нержавеющая сталь, бронза

### Антифриз
**Свойства гликоля:**
- **Этиленгликоль**: Точка замерзания -12°C (30%), -50°C (60%)
- **Пропиленгликоль**: Менее токсичен, точка замерзания аналогичная
- **Влияние на вязкость:** Увеличение на 50-100%

## Типовые Конфигурации

### Простой Контур
```
ASIC → Пластина → Насос → Радиатор → (обратно к ASIC)
```

### Сложный Контур
```
Резервуар → Насос → Фильтр → ASIC блоки → Радиатор → (обратно)
```

### Двойной Контур
```
Первичный: ASIC → Пластина → Насос₁
Вторичный: Радиатор → Насос₂ → Пластина
```
            """,
            interactive_elements={
                "darcy_weisbach_calculator": {
                    "type": "calculator",
                    "formula": "DP = lambda * (L/D) * (rho * v^2 / 2)",
                    "inputs": ["lambda", "L", "D", "rho", "v"]
                },
                "pump_curve_analyzer": {
                    "type": "interactive_chart",
                    "pumps": ["D5_Vario", "DDC_3_2", "Laing_D5"],
                    "show_efficiency": True
                },
                "system_characteristic": {
                    "type": "calculator",
                    "formula": "DP = K * Q^2",
                    "inputs": ["flow_rate", "resistance_coefficient"]
                }
            },
            prerequisites=["thermo_basics", "convection_basics"],
            related_articles=["pump_selection", "coolant_chemistry"]
        ))

        # Risk Assessment
        self._add_article(KnowledgeArticle(
            id="thermal_risks",
            title="Термические Риски и Безопасность",
            category="safety",
            difficulty="intermediate",
            content="""
# Термические Риски в Майнинг-Операциях

## Критические Температурные Пределы

### Для ASIC
- **T_junction_max**: 90-110°C (зависит от модели)
- **T_case_max**: 70-85°C
- **T_inlet_max**: 35-45°C (air cooling)

### Последствия Превышения
1. **90-95°C**: Начало degradation производительности
2. **100°C**: Риск permanent damage
3. **110°C+**: Вероятность catastrophic failure

## Риски Систем Охлаждения

### Воздушное Охлаждение
- **Засорение фильтров**: Блокировка airflow
- **Выход вентиляторов из строя**: Каскадный перегрев
- **Неравномерный поток**: Локальные hotspots
- **Внешние факторы**: Высокая ambient температура

### Жидкостное Охлаждение
- **Утечки**: Электрическая опасность + потеря охлаждения
- **Кавитация насоса**: Шум, вибрация, повреждения
- **Коррозия**: Гальваническая, электрохимическая
- **Замерзание**: При использовании антифриза

### Гибридные Системы
- **Отказ компонентов**: Сложность диагностики
- **Дисбаланс**: Недостаточное охлаждение одного типа

## Мониторинг и Предупреждение

### Ключевые Метрики
1. **Температура ASIC**: Junction и case
2. **Температура охлаждающей среды**: Air inlet, coolant inlet/outlet
3. **Расход**: Airflow (CFM), coolant flow (LPM)
4. **Давление**: System pressure, pump head
5. **Электрические параметры**: Напряжение, ток, мощность

### Системы Мониторинга
- **Датчики температуры**: NTC thermistors, digital sensors
- **Датчики потока**: Для воздуха и жидкости
- **Датчики давления**: Differential pressure sensors
- **Power meters**: Для мониторинга энергопотребления

### Автоматическая Защита
- **Thermal throttling**: Автоматическое снижение производительности
- **Emergency shutdown**: При критических температурах
- **Redundant cooling**: Резервные системы
- **Alarm systems**: SMS, email, audible alerts

## Риск-Оценка Проекта

### Quantitative Risk Assessment
```
Risk_Level = (Probability * Impact) / Mitigation
```

### Вероятности (Probability)
- **Очень низкая**: < 1% в год
- **Низкая**: 1-5% в год
- **Средняя**: 5-15% в год
- **Высокая**: 15-30% в год
- **Очень высокая**: > 30% в год

### Влияние (Impact)
- **Низкое**: < $1000 потери
- **Среднее**: $1000-10000 потери
- **Высокое**: $10000-50000 потери
- **Критическое**: > $50000 потери

### Mitigation Strategies
1. **Проектирование**: Redundancy, safety margins
2. **Мониторинг**: Real-time monitoring, alerts
3. **Обслуживание**: Regular maintenance, cleaning
4. **Обучение**: Operator training, procedures
5. **Страхование**: Risk transfer through insurance

## Case Studies

### Incident 1: Fan Failure Cascade
**Сценарий:** Один вентилятор вышел из строя, вызвав цепную реакцию
**Последствия:** Перегрев 20 ASIC, потеря $50,000
**Уроки:** Redundant fans, automatic failover

### Incident 2: Coolant Leak
**Сценарий:** Утечка антифриза из-за коррозии
**Последствия:** Короткое замыкание, пожар
**Уроки:** Material compatibility, leak detection

### Incident 3: Hotspot Development
**Сценарий:** Постепенное развитие hotspot из-за пыли
**Последствия:** Degradation производительности на 30%
**Уроки:** Regular cleaning, thermal imaging
            """,
            interactive_elements={
                "risk_assessment_calculator": {
                    "type": "calculator",
                    "formula": "Risk_Score = (Probability * Impact) / Mitigation",
                    "inputs": ["probability", "impact", "mitigation_factor"]
                },
                "thermal_threshold_monitor": {
                    "type": "dashboard",
                    "metrics": ["asic_temp", "coolant_temp", "flow_rate", "power_consumption"],
                    "thresholds": {"critical": 95, "warning": 85}
                },
                "incident_database": {
                    "type": "searchable_database",
                    "incidents": ["fan_cascade", "coolant_leak", "hotspot_development"],
                    "filters": ["severity", "system_type", "root_cause"]
                }
            },
            prerequisites=["asic_thermal_design"],
            related_articles=["monitoring_systems", "emergency_procedures"]
        ))

    def _add_article(self, article: KnowledgeArticle):
        """Add article to knowledge base."""
        self.articles[article.id] = article
        if article.category not in self.categories:
            self.categories[article.category] = []
        self.categories[article.category].append(article.id)

    def get_article(self, article_id: str) -> Optional[KnowledgeArticle]:
        """Get specific article by ID."""
        return self.articles.get(article_id)

    def get_articles_by_category(self, category: str) -> List[KnowledgeArticle]:
        """Get all articles in a category."""
        return [self.articles[aid] for aid in self.categories.get(category, [])]

    def get_articles_by_difficulty(self, difficulty: str) -> List[KnowledgeArticle]:
        """Get articles by difficulty level."""
        return [article for article in self.articles.values()
                if article.difficulty == difficulty]

    def search_articles(self, query: str) -> List[KnowledgeArticle]:
        """Search articles by title or content."""
        query_lower = query.lower()
        results = []
        for article in self.articles.values():
            if (query_lower in article.title.lower() or
                query_lower in article.content.lower() or
                query_lower in article.category.lower()):
                results.append(article)
        return results

    def get_learning_path(self, target_topic: str) -> List[KnowledgeArticle]:
        """Get recommended learning path for a topic."""
        # Simple learning path generator
        paths = {
            "asic_cooling": ["thermo_basics", "convection_basics", "asic_thermal_design", "fan_basics"],
            "liquid_cooling": ["thermo_basics", "hydronics_basics", "pump_selection", "thermal_risks"],
            "system_design": ["thermo_basics", "convection_basics", "hydronics_basics", "thermal_risks"]
        }

        path_ids = paths.get(target_topic, [])
        return [self.articles[aid] for aid in path_ids if aid in self.articles]

    def get_interactive_element(self, article_id: str, element_id: str) -> Optional[Dict[str, Any]]:
        """Get interactive element from article."""
        article = self.get_article(article_id)
        if article:
            return article.interactive_elements.get(element_id)
        return None


# Global instance
knowledge_base = KnowledgeBasePRO()


def get_knowledge_base() -> KnowledgeBasePRO:
    """Get the global knowledge base instance."""
    return knowledge_base


if __name__ == "__main__":
    # Demo usage
    kb = get_knowledge_base()

    print("=== ThermoMiner Pro Knowledge Base PRO ===")
    print(f"Total articles: {len(kb.articles)}")
    print(f"Categories: {list(kb.categories.keys())}")

    # Show beginner articles
    print("\n=== Beginner Level Articles ===")
    for article in kb.get_articles_by_difficulty("beginner"):
        print(f"- {article.title} ({article.category})")

    # Show learning path
    print("\n=== ASIC Cooling Learning Path ===")
    for article in kb.get_learning_path("asic_cooling"):
        print(f"- {article.title} ({article.difficulty})")









