# ThermoMiner Pro - Intelligent Thermal Calculator for Mining Farms

ThermoMiner Pro is a comprehensive engineering tool for mining farm thermal management, providing precise cooling system calculations to prevent capital losses from overheating.

## Features

### 🏗️ **Core Architecture**
- **CoreDB**: SQLite-backed ASIC database with 25+ models from Bitmain and MicroBT
- **Hydrothermal Engine**: Advanced NTU method calculations with material compatibility
- **Airflow Engine**: CFD-lite hotspot analysis and ventilation network modeling
- **Financial Engine**: CAPEX/OPEX analysis and ROI calculations
- **Risk Assessment**: Comprehensive safety and reliability evaluation

### 🎯 **Key Capabilities**
- **ASIC Thermal Database**: Complete specifications for current and legacy models
- **Hydro Cooling Design**: Precise coolant flow, radiator sizing, pump selection
- **Airflow Analysis**: Room ventilation requirements and fan placement optimization
- **Financial Comparison**: Air vs Hydro vs Hybrid cooling scenario analysis
- **Knowledge Base PRO**: Interactive thermal engineering reference guides

### 🔧 **Engineering Precision**
- Fundamental physics-based calculations (thermodynamics, fluid dynamics)
- Conservative safety margins (20-25%) for real-world conditions
- Comprehensive material compatibility analysis
- Risk assessment with critical failure prevention

## Quick Start

### Prerequisites
- Python 3.10+
- SQLite3

### Installation
```bash
# Clone or navigate to the project directory
cd thermominer_pro

# Install dependencies (if using virtual environment)
pip install -r ../requirements.txt
```

### Initialize Database
```bash
# Import sample ASIC data
python -m thermominer_pro.cli initdb
```

### Run CLI Demo
```bash
# Test hydro cooling calculations
python -m thermominer_pro.cli hydro
```

### Launch Desktop GUI
```bash
# Run the graphical user interface
python thermominer_pro/run_gui.py
```

## Architecture Overview

```
thermominer_pro/
├── coredb/                 # ASIC database system
│   ├── coredb.py          # SQLite backend
│   ├── models.py          # ASIC data structures
│   └── sample_data/       # CSV import files
├── core/                  # Physics calculation engines
│   ├── hydro_core.py      # Hydrothermal calculations
│   ├── airflow_core.py    # Ventilation analysis
│   ├── finance_core.py    # Economic evaluation
│   └── risk_engine.py     # Safety assessment
├── data/                  # Component databases
│   ├── fans.json          # Fan specifications
│   └── pumps.json         # Pump specifications
├── knowledge_base_pro.py  # Interactive reference guides
├── thermominer_pro_gui.py # Desktop application
├── run_gui.py            # GUI launcher
└── cli.py                # Command-line interface
```

## Usage Examples

### Hydro Cooling Calculation
```python
from thermominer_pro.core.hydro_core import *
from thermominer_pro.coredb import CoreDB

# Initialize database
db = CoreDB()
asic = db.get_asic("Bitmain", "Antminer S19 Pro")

# Calculate cooling requirements
props = coolant_properties("water", 0, 25)
m_dot = mass_flow_for_heat(100, props["cp"], 5.0)
flow_lpm = volumetric_flow_lpm(m_dot, props["rho"])

print(f"Required flow: {flow_lpm:.2f} L/min")
```

### Airflow Analysis
```python
from thermominer_pro.core.airflow_core import *

# Calculate ventilation requirements
airflow = required_airflow_m3_h(3000, 25, 35)  # 3kW TDP
print(f"Required airflow: {airflow:.0f} m³/h")
```

### Financial Comparison
```python
from thermominer_pro.core.finance_core import *

air_scenario = Scenario(
    name="Air Cooling",
    components=[Component("Fans", 500, 120)],
    baseline_revenue_usd_per_day=100.0,
    electricity_price_usd_per_kwh=0.10
)

comparison = compare_scenarios(air_scenario, hydro_scenario)
print(f"Payback period: {comparison['alt_payback_days']:.0f} days")
```

## ASIC Database

The system includes comprehensive thermal specifications for:
- **Bitmain**: S17, S19, S19 Pro, S19 XP, S21, S21 XP series
- **MicroBT**: M20, M21, M30, M31, M50, M53, M56 series
- **Legacy Models**: Deprecated models with caution flags

Each entry includes:
- TDP power envelope (min/max)
- Thermal resistances (chip-to-coolant, chip-to-case, case-to-sink)
- Operating temperature limits
- Fan specifications (CFM, static pressure)
- Hydro cooling parameters (when applicable)

## Component Libraries

### Fans Database
- **Axial Fans**: Noctua, Delta, industrial models
- **Inline Duct Fans**: Fantech FG series, AC Infinity
- **Centrifugal Fans**: High-static pressure models
- Complete with power consumption, noise levels, pricing

### Pumps Database
- **D5 Pumps**: EKWB, Laing, Aquacomputer
- **DC Pumps**: Alphacool, Phobya
- **Centrifugal Pumps**: Mining-grade industrial models
- Performance curves and efficiency data

## Risk Assessment

The system evaluates multiple risk categories:
- **Thermal Risks**: T_junction exceedance, hotspot formation
- **Hydraulic Risks**: Cavitation, pump failure, flow restriction
- **Material Risks**: Galvanic corrosion, coolant degradation
- **Operational Risks**: Power consumption, maintenance requirements

## Knowledge Base PRO

Interactive reference system covering:
- **Thermodynamics**: Heat transfer mechanisms, thermal resistance
- **Fluid Dynamics**: Reynolds number, pressure drop calculations
- **Heat Exchangers**: NTU method, effectiveness calculations
- **Ventilation**: Fan laws, duct design, pressure networks
- **Materials**: Compatibility, corrosion prevention
- **Safety**: Risk assessment, emergency procedures

## Development Roadmap

### Phase 2 (Next Release)
- [ ] **Web Application**: Django/React dashboard with advanced analytics
- [ ] **PDF Report Generator**: Professional calculation reports
- [ ] **IoT Integration**: Sensor data collection and predictive maintenance
- [ ] **3D Visualization**: Room layout and thermal mapping
- [ ] **Mobile App**: Remote monitoring and control

### Phase 3 (Future)
- [ ] **Machine Learning**: Predictive failure analysis
- [ ] **Cloud Integration**: Multi-site farm management
- [ ] **API Services**: Third-party integration
- [ ] **Advanced CFD**: Full computational fluid dynamics
- [ ] **Real-time Monitoring**: Live thermal management

## Engineering Validation

The system has been validated against:
- **Manufacturer Specifications**: ASIC and component datasheets
- **Engineering Standards**: ASHRAE, IEEE thermal guidelines
- **Real-world Testing**: Mining farm operational data
- **Peer Review**: Thermal engineering community feedback

## Safety & Reliability

ThermoMiner Pro is designed with engineering conservatism:
- **25% Safety Margins**: All calculations include conservative factors
- **Failure Mode Analysis**: Comprehensive risk assessment
- **Material Science**: Proper selection for longevity
- **Operational Guidelines**: Best practices for maintenance

## Contributing

Contributions welcome! Areas of interest:
- Additional ASIC models and thermal data
- Component specifications and performance curves
- Enhanced calculation algorithms
- UI/UX improvements
- Documentation and tutorials

## License

ThermoMiner Pro is released under MIT License for use in mining operations worldwide.

## Support

For technical support or feature requests:
- Documentation: See Knowledge Base PRO
- Issues: GitHub issue tracker
- Community: Mining thermal engineering forums

---

**ThermoMiner Pro** - Engineering precision meets operational excellence in mining thermal management.














