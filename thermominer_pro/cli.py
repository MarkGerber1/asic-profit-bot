from __future__ import annotations

import argparse
from typing import Optional

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from coredb import CoreDB
from core.hydro_core import (
    coolant_properties,
    mass_flow_for_heat,
    volumetric_flow_lpm,
    compute_chip_temperature,
    required_UA_for_Q,
    radiator_area_from_UA,
    pump_power_w,
    pump_head_required_m,
    approximate_beta_for_coolant,
    get_radiator_catalog,
    select_radiator_from_catalog,
    expansion_tank_detailed,
    materials_galvanic_check,
    RadiatorSpec,
    Coolant,
)
from core.airflow_core import required_airflow_m3_h, m3h_to_cfm
from core.finance_core import Component, Scenario, compare_scenarios
from core.risk_engine import assess_hydro


def run_hydro_wizard():
    print("=== ThermoMiner Pro :: Hydro Wizard (prototype) ===")
    db = CoreDB()
    vendor = input("Vendor (e.g., Bitmain): ").strip() or "Bitmain"
    model = input("Model (e.g., Antminer S19j Pro): ").strip() or "Antminer S19j Pro"
    asic = db.get_asic(vendor, model)
    if not asic:
        print("Model not found in CoreDB. Enter values manually.")
        tdp = float(input("TDP (W): ").strip())
        theta = float(input("Theta chip->coolant (C/W): ").strip())
        t_jmax = float(input("T_junction max (C): ").strip())
        t_in_coolant = float(input("Coolant inlet (C): ").strip())
    else:
        tdp = (asic.tdp_w_max or asic.tdp_w_min or 3000.0)
        theta = asic.theta_chip_coolant_c_per_w or 0.02
        t_jmax = asic.t_junc_max_c or 95.0
        t_in_coolant = float(input("Coolant inlet (C) [default 25]: ") or "25")

    fluid = input("Coolant medium [water/glycol]: ").strip().lower() or "water"
    glycol_pct = int(input("Glycol % [0-60]: ").strip() or "0")
    amb_air = float(input("Ambient air for radiator (C) [30]: ") or "30")
    allowed_air_rise = float(input("Radiator air ΔT (C) [10]: ") or "10")
    target_chip_margin = 1.0
    props = coolant_properties(fluid, glycol_pct, t_in_coolant)

    # Flow from Q = m*Cp*ΔT; choose ΔT_liquid 5C as conservative
    deltaT_liquid = float(input("Coolant ΔT across block (C) [5]: ") or "5")
    m_dot = mass_flow_for_heat(tdp, props["cp"], deltaT_liquid)
    flow_lpm = volumetric_flow_lpm(m_dot, props["rho"])

    t_chip = compute_chip_temperature(tdp, t_in_coolant, theta)
    print(f"Required coolant flow ~ {flow_lpm:.2f} L/min")
    print(f"Predicted chip temperature ~ {t_chip:.1f} C (limit {t_jmax:.1f} C)")

    # Radiator sizing with catalog selection
    C_hot = m_dot * props["cp"]
    deltaT_air = max(5.0, allowed_air_rise)
    m_dot_air = tdp / (1005.0 * deltaT_air)
    C_cold = m_dot_air * 1005.0
    UA = required_UA_for_Q(tdp, t_in_coolant + deltaT_liquid, amb_air, C_hot, C_cold)
    rad_area = radiator_area_from_UA(UA)

    # Select radiator from catalog
    radiator_catalog = get_radiator_catalog()
    air_flow_m3_s = m_dot_air / 1.225  # Approximate air density
    selected_radiator, margin = select_radiator_from_catalog(UA, radiator_catalog, air_flow_m3_s, flow_lpm)

    print(f"Radiator UA ≈ {UA:.0f} W/K, area ~ {rad_area:.2f} m^2 (with safety)")
    print(f"Recommended radiator: {selected_radiator.name}")
    print(f"  - Face area: {selected_radiator.face_area_m2:.3f} m²")
    print(f"  - Price: ${selected_radiator.price_usd:.0f}")
    print(f"  - Performance margin: {margin:.1%}")

    # Pump estimates
    dp_total = float(input("Estimated loop ΔP (Pa) [50000]: ") or "50000")
    head_m = pump_head_required_m(dp_total, props["rho"])  # with safety
    pump_w = pump_power_w(dp_total, m_dot / props["rho"])  # rough
    print(f"Pump head requirement ~ {head_m:.1f} m, pump power ~ {pump_w:.0f} W")

    # Expansion tank calculation
    system_volume_l = float(input("Estimated system volume (L) [15]: ") or "15")
    max_coolant_temp_c = t_in_coolant + deltaT_liquid + 10  # Add margin for hot spots
    coolant_obj = Coolant(medium=fluid, glycol_percent=glycol_pct, temperature_c=t_in_coolant)
    tank_calc = expansion_tank_detailed(system_volume_l, t_in_coolant, max_coolant_temp_c, coolant_obj)

    print(f"Expansion tank requirements:")
    print(f"  - Expansion volume: {tank_calc['expansion_volume_l']:.2f} L")
    print(f"  - Required tank volume: {tank_calc['required_tank_volume_l']:.1f} L")
    print(f"  - Max system pressure: {tank_calc['max_system_pressure_bar']:.2f} bar")
    print(f"  - Recommended pre-charge: {tank_calc['recommended_precharge_bar']:.1f} bar")

    # Material compatibility check
    materials_input = input("Materials used (comma-separated) [copper, aluminum, stainless steel]: ")
    materials_list = [m.strip() for m in materials_input.split(',')] if materials_input else ["copper", "aluminum", "stainless steel"]
    galvanic_warnings = materials_galvanic_check(materials_list)
    if galvanic_warnings:
        print("\nMATERIAL COMPATIBILITY WARNINGS:")
        for warning in galvanic_warnings:
            print(f"  - {warning}")

    # Finance quick check
    elec = float(input("Electricity price (USD/kWh) [0.10]: ") or "0.10")
    base = Scenario(
        name="Air",
        components=[Component("Stock fans", 0.0, power_w=80.0)],
        baseline_revenue_usd_per_day=10.0,
        electricity_price_usd_per_kwh=elec,
    )
    hydro = Scenario(
        name="Hydro",
        components=[
            Component("Pump", 150.0, power_w=pump_w),
            Component("Radiator", selected_radiator.price_usd, power_w=0.0),
            Component("Radiator Fans", 150.0, power_w=120.0),
            Component("Plumbing", 300.0, power_w=0.0),
            Component("Expansion Tank", 50.0, power_w=0.0),
        ],
        baseline_revenue_usd_per_day=10.0,
        electricity_price_usd_per_kwh=elec,
        additional_revenue_usd_per_day=0.5,
    )
    cmp = compare_scenarios(base, hydro)
    print(f"Hydro Δprofit/day = ${cmp['delta_profit_per_day']:.2f}, Payback ~ {cmp['alt_payback_days'] and round(cmp['alt_payback_days'])} days")

    # Risks
    risks = assess_hydro(
        t_chip_c=t_chip,
        t_junc_max_c=t_jmax,
        dp_total_pa=dp_total,
        pump_head_capable_pa=dp_total * 1.1,
        t_inlet_coolant_c=t_in_coolant,
        t_inlet_coolant_max_c=None,
        ambient_c=amb_air,
        relative_humidity=0.6,
        coolant_outlet_c=t_in_coolant + deltaT_liquid,
    )
    for r in risks:
        print(f"[{r.level.upper()}] {r.code}: {r.message}")


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="ThermoMiner Pro CLI (prototype)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("initdb", help="Initialize CoreDB and import sample CSV")
    p_init.add_argument("--csv", dest="csv_path", default=None, help="Path to ASIC CSV (defaults to sample data)")

    sub.add_parser("hydro", help="Run interactive hydronics wizard")

    args = parser.parse_args(argv)
    if args.command == "initdb":
        db = CoreDB()
        csv_path = args.csv_path
        if not csv_path:
            import os
            csv_path = os.path.join(os.path.dirname(__file__), "coredb", "sample_data", "asic_coredb.csv")
        n = db.import_csv(csv_path)
        print(f"Imported {n} ASIC models from {csv_path}")
    elif args.command == "hydro":
        run_hydro_wizard()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


