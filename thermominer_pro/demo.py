#!/usr/bin/env python3
"""
ThermoMiner Pro Demonstration Script
Showcase the core functionality of the thermal calculation system
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from coredb import CoreDB
from core.hydro_core import *
from core.airflow_core import *
from core.finance_core import Component, Scenario, compare_scenarios
from core.risk_engine import assess_hydro
from knowledge_base_pro import get_knowledge_base


def main():
    print("=" * 70)
    print("ThermoMiner Pro - Intelligent Thermal Calculator Demo")
    print("=" * 70)

    # Initialize database
    print("\n1. Initializing ASIC Database...")
    db = CoreDB()
    try:
        n = db.import_csv("coredb/sample_data/asic_coredb.csv")
        print(f"✓ Loaded {n} ASIC models")
    except Exception as e:
        print(f"Note: Database already initialized ({e})")

    # Test ASIC lookup
    print("\n2. ASIC Database Query...")
    asic = db.get_asic("Bitmain", "Antminer S19 Pro")
    if asic:
        print("✓ Found ASIC:")
        print(f"  - TDP: {asic.tdp_w_min}-{asic.tdp_w_max} W")
        print(f"  - Thermal Resistance: {asic.theta_chip_coolant_c_per_w:.3f} °C/W")
        print(f"  - Max Junction Temp: {asic.t_junc_max_c}°C")
    else:
        print("✗ ASIC not found")

    # Hydro cooling calculation
    print("\n3. Hydro Cooling System Design...")
    tdp = 100  # W
    theta = 0.02  # °C/W
    t_in_coolant = 25  # °C

    # Calculate flow requirements
    props = coolant_properties("water", 0, t_in_coolant)
    m_dot = mass_flow_for_heat(tdp, props["cp"], 5.0)  # 5°C rise
    flow_lpm = volumetric_flow_lpm(m_dot, props["rho"])
    t_chip = compute_chip_temperature(tdp, t_in_coolant, theta)

    print("✓ Flow Calculations:")
    print(f"  - Required Flow: {flow_lpm:.2f} L/min")
    print(f"  - Predicted Chip Temperature: {t_chip:.1f} °C")

    # Radiator sizing (simplified)
    print("✓ Radiator Selection:")
    radiator_catalog = get_radiator_catalog()
    selected_radiator = radiator_catalog[0]  # Use first radiator as example
    print(f"  - Recommended: {selected_radiator.name}")
    print(f"  - Face Area: {selected_radiator.face_area_m2:.3f} m²")
    print(f"  - Price: ${selected_radiator.price_usd:.0f}")

    # Airflow calculation
    print("\n4. Airflow System Analysis...")
    total_tdp = 3000  # 3kW total
    airflow = required_airflow_m3_h(total_tdp, 25, 35)  # 25°C to 35°C rise
    print("✓ Ventilation Requirements:")
    print(f"  - Total TDP: {total_tdp} W")
    print(f"  - Required Airflow: {airflow:.0f} m³/h")
    print(f"  - Required Airflow: {airflow * 0.588:.0f} CFM")

    # Financial comparison
    print("\n5. Financial Scenario Comparison...")

    air_scenario = Scenario(
        name="Air Cooling",
        components=[Component("Fans", 500, 120)],
        baseline_revenue_usd_per_day=100.0,
        electricity_price_usd_per_kwh=0.10
    )

    hydro_scenario = Scenario(
        name="Hydro Cooling",
        components=[
            Component("Pump", 120, 45),
            Component("Radiator", selected_radiator.price_usd, 0),
            Component("Radiator Fans", 150, 120),
            Component("Plumbing", 300, 0)
        ],
        baseline_revenue_usd_per_day=105.0,  # 5% hashrate gain
        electricity_price_usd_per_kwh=0.10
    )

    comparison = compare_scenarios(air_scenario, hydro_scenario)

    print("✓ Economic Analysis:")
    print(f"  - Air Cooling Daily Profit: ${air_scenario.gross_profit_per_day():.2f}")
    print(f"  - Hydro Cooling Daily Profit: ${hydro_scenario.gross_profit_per_day():.2f}")
    print(f"  - Daily Profit Difference: ${comparison['delta_profit_per_day']:.2f}")
    print(f"  - Payback Period: {comparison['alt_payback_days']:.0f} days")

    # Risk assessment
    print("\n6. Risk Assessment...")
    risks = assess_hydro(
        t_chip_c=t_chip,
        t_junc_max_c=95.0,
        dp_total_pa=50000,
        pump_head_capable_pa=55000,
        t_inlet_coolant_c=t_in_coolant,
        t_inlet_coolant_max_c=40.0,
        ambient_c=30,
        relative_humidity=0.6,
        coolant_outlet_c=t_in_coolant + 5
    )

    print("✓ Risk Analysis:")
    for risk in risks:
        print(f"  - [{risk.level.upper()}] {risk.code}: {risk.message}")

    # Knowledge Base
    print("\n7. Knowledge Base PRO...")
    kb = get_knowledge_base()
    print(f"✓ Available Articles: {len(kb.articles)}")
    print("  Categories:")
    for category in kb.categories.keys():
        count = len(kb.categories[category])
        print(f"  - {category}: {count} articles")

    # Sample article
    thermo_basics = kb.get_article("thermo_basics")
    if thermo_basics:
        print(f"\n✓ Sample Article: '{thermo_basics.title}'")
        print(f"  Difficulty: {thermo_basics.difficulty}")
        print(f"  Preview: {thermo_basics.content[:100]}...")

    print("\n" + "=" * 70)
    print("ThermoMiner Pro Demo Complete!")
    print("Run 'python thermominer_pro/run_gui.py' to launch the desktop application")
    print("=" * 70)


if __name__ == "__main__":
    main()
