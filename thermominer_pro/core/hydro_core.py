from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


GRAVITY_M_S2 = 9.80665


@dataclass
class Coolant:
    medium: str  # "water" or "glycol"
    glycol_percent: int = 0  # 0..60
    temperature_c: float = 25.0

    @property
    def properties(self) -> Dict[str, float]:
        """Return approximate properties at temperature (rho, cp, mu, k).

        Units:
        - rho: kg/m^3
        - cp: J/kg-K
        - mu: Pa*s
        - k: W/m-K
        """
        t = float(self.temperature_c)

        def lerp(a: float, b: float, w: float) -> float:
            return a + (b - a) * w

        # Reference data at ~25C (engineering approximations)
        if self.medium.lower() == "water" or self.glycol_percent == 0:
            return {"rho": 997.0, "cp": 4181.0, "mu": 0.00089, "k": 0.60}

        p = max(0, min(60, int(self.glycol_percent)))
        # Reference points for ethylene glycol-water mixtures at ~25C
        ref = {
            30: {"rho": 1045.0, "cp": 3650.0, "mu": 0.0025, "k": 0.40},
            50: {"rho": 1065.0, "cp": 3300.0, "mu": 0.0050, "k": 0.38},
        }
        if p <= 30:
            a, b, w = {"rho": 997.0, "cp": 4181.0, "mu": 0.00089, "k": 0.60}, ref[30], p / 30.0
        else:
            a, b, w = ref[30], ref[50], (p - 30) / 20.0
        return {
            "rho": lerp(a["rho"], b["rho"], w),
            "cp": lerp(a["cp"], b["cp"], w),
            "mu": lerp(a["mu"], b["mu"], w),
            "k": lerp(a["k"], b["k"], w),
        }


def mass_flow_for_heat(Q_w: float, cp_j_per_kgk: float, deltaT_c: float) -> float:
    """Compute mass flow (kg/s) to remove heat Q at temperature rise deltaT.
    m_dot = Q / (cp * deltaT)
    """
    if deltaT_c <= 0:
        raise ValueError("deltaT must be > 0")
    return Q_w / (cp_j_per_kgk * deltaT_c)


def volumetric_flow_lpm(mass_flow_kg_s: float, rho_kg_m3: float) -> float:
    return mass_flow_kg_s / rho_kg_m3 * 1000.0 * 60.0


def compute_chip_temperature(power_w: float, t_liquid_in_c: float, theta_chip_to_coolant_c_per_w: float, safety_factor: float = 1.25) -> float:
    """Estimate chip junction temperature from inlet coolant temp and thermal resistance.

    T_chip ≈ T_coolant_in + theta_jl * Q, with conservative safety factor.
    """
    theta = max(0.0, float(theta_chip_to_coolant_c_per_w)) * float(safety_factor)
    return t_liquid_in_c + theta * power_w


# Heat exchanger sizing (radiator) using effectiveness-NTU method

def epsilon_counterflow(NTU: float, Cr: float) -> float:
    if Cr == 1.0:
        return NTU / (1.0 + NTU)
    num = 1.0 - math.exp(-NTU * (1.0 - Cr))
    den = 1.0 - Cr * math.exp(-NTU * (1.0 - Cr))
    return num / den


def invert_epsilon_for_NTU_counterflow(epsilon: float, Cr: float, tol: float = 1e-5) -> float:
    # Simple bisection on NTU in [1e-6, 100]
    lo, hi = 1e-6, 100.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        emid = epsilon_counterflow(mid, Cr)
        if emid < epsilon:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def required_UA_for_Q(Q_w: float, T_hot_in_c: float, T_cold_in_c: float, C_hot_w_per_k: float, C_cold_w_per_k: float, hx_flow_arrangement: str = "counterflow") -> float:
    """Compute required UA to transfer Q given inlet temps and capacity rates.

    Q_max = C_min * (T_hot_in - T_cold_in)
    epsilon = Q / Q_max
    NTU = f^-1(epsilon, Cr)
    UA = NTU * C_min
    """
    deltaT_in = T_hot_in_c - T_cold_in_c
    if deltaT_in <= 0:
        raise ValueError("Hot inlet must be higher than cold inlet temperature")
    C_min = min(C_hot_w_per_k, C_cold_w_per_k)
    C_max = max(C_hot_w_per_k, C_cold_w_per_k)
    Q_max = C_min * deltaT_in
    if Q_w >= 0.98 * Q_max:
        # Physically infeasible without approach temperatures going to zero
        raise ValueError("Requested heat duty too high for given flows/temps")
    epsilon = Q_w / Q_max
    Cr = C_min / C_max if C_max > 0 else 0.0

    if hx_flow_arrangement == "counterflow":
        NTU = invert_epsilon_for_NTU_counterflow(epsilon, Cr)
    else:
        # Fallback approximation: treat as counterflow; this is conservative on UA
        NTU = invert_epsilon_for_NTU_counterflow(epsilon, Cr)
    return NTU * C_min


def radiator_area_from_UA(UA_w_per_k: float, assumed_U_w_per_m2k: float = 70.0, safety_factor: float = 1.25) -> float:
    """Estimate required radiator face area (m^2) from UA and assumed U.

    Air-side U for compact finned radiators commonly 50-120 W/m^2-K. We use a
    conservative default and add safety factor for fouling and non-idealities.
    """
    U = max(1.0, float(assumed_U_w_per_m2k))
    return (UA_w_per_k / U) * float(safety_factor)


# Hydraulics: Darcy–Weisbach and minor losses

def reynolds_number(rho: float, velocity_m_s: float, diameter_m: float, mu: float) -> float:
    return rho * velocity_m_s * diameter_m / mu


def haaland_friction_factor(Re: float, rel_roughness: float) -> float:
    if Re < 2300:
        # Laminar
        return 64.0 / max(Re, 1e-6)
    # Turbulent: Haaland explicit approximation
    inv_sqrt_f = -1.8 * math.log10((rel_roughness / 3.7) ** 1.11 + 6.9 / max(Re, 1e-6))
    return 1.0 / (inv_sqrt_f ** 2)


def pressure_drop_straight_tube(rho: float, mu: float, volumetric_flow_m3_s: float, diameter_m: float, length_m: float, roughness_m: float) -> float:
    area = math.pi * (diameter_m ** 2) / 4.0
    velocity = volumetric_flow_m3_s / max(area, 1e-12)
    Re = reynolds_number(rho, velocity, diameter_m, mu)
    rel_roughness = roughness_m / diameter_m
    f = haaland_friction_factor(Re, rel_roughness)
    dp = f * (length_m / diameter_m) * 0.5 * rho * velocity ** 2
    return dp


def pressure_drop_local_losses(rho: float, volumetric_flow_m3_s: float, K_sum: float) -> float:
    velocity_head = 0.5 * rho * (volumetric_flow_m3_s) ** 2  # Not dimensionally correct; need area
    # For local losses, K is defined with velocity at section; here we expect caller to provide K* (v^2/2) already scaled
    # Provide a safer helper below that accounts for area.
    return K_sum * velocity_head


def local_loss_dp_from_velocity(rho: float, velocity_m_s: float, K_sum: float) -> float:
    return K_sum * 0.5 * rho * velocity_m_s ** 2


def pump_head_required_m(dp_total_pa: float, rho: float, safety_factor: float = 1.2) -> float:
    return float(safety_factor) * dp_total_pa / (rho * GRAVITY_M_S2)


def pump_power_w(dp_total_pa: float, volumetric_flow_m3_s: float, pump_efficiency: float = 0.35) -> float:
    eta = max(0.05, min(0.9, float(pump_efficiency)))
    hydraulic_power = dp_total_pa * volumetric_flow_m3_s
    return hydraulic_power / eta


def expansion_tank_volume(system_volume_l: float, beta_per_k: float, deltaT_c: float, safety_factor: float = 1.3) -> float:
    """Compute minimum expansion tank volume (liters).

    V_tank >= beta * ΔT * V_system * SF
    beta ~ 0.00021 1/K for water; higher for glycol mixtures.
    """
    return system_volume_l * beta_per_k * deltaT_c * float(safety_factor)


def approximate_beta_for_coolant(coolant: Coolant) -> float:
    if coolant.medium.lower() == "water" and coolant.glycol_percent == 0:
        return 0.00021
    # crude scaling
    return 0.00021 + 0.000004 * min(60, max(0, coolant.glycol_percent))


@dataclass
class RadiatorSpec:
    """Radiator specification for heat exchanger calculations."""
    name: str
    face_area_m2: float
    core_volume_l: float
    tube_count: int
    fin_density_fpi: int  # fins per inch
    tube_diameter_mm: float
    air_side_area_m2: float
    coolant_side_area_m2: float
    price_usd: float = 0.0


def radiator_performance_factor(radiator: RadiatorSpec, air_velocity_m_s: float, coolant_velocity_m_s: float) -> float:
    """Calculate radiator performance factor based on design parameters.

    Returns a factor that modifies the base UA value for specific operating conditions.
    """
    # Air-side enhancement factor (based on fin density and air velocity)
    air_enhancement = 1.0 + 0.1 * (radiator.fin_density_fpi / 10.0) * (air_velocity_m_s / 2.0)

    # Coolant-side enhancement factor (based on tube design and flow velocity)
    coolant_enhancement = 1.0 + 0.05 * (coolant_velocity_m_s / 1.5)

    # Overall factor with safety margin
    return air_enhancement * coolant_enhancement * 0.9  # 10% safety reduction


def select_radiator_from_catalog(required_ua_w_per_k: float, available_radiators: List[RadiatorSpec],
                                air_flow_m3_s: float, coolant_flow_lpm: float) -> Tuple[RadiatorSpec, float]:
    """Select optimal radiator from catalog based on required UA and operating conditions."""
    coolant_flow_m3_s = coolant_flow_lpm / 60000.0  # Convert to m³/s
    coolant_velocity_m_s = coolant_flow_m3_s / 0.0002  # Approximate velocity in tubes (m/s)

    air_velocity_m_s = air_flow_m3_s / (0.1 * 0.2)  # Approximate face velocity (m/s)

    best_radiator = None
    best_margin = float('inf')

    for radiator in available_radiators:
        perf_factor = radiator_performance_factor(radiator, air_velocity_m_s, coolant_velocity_m_s)
        effective_ua = radiator.face_area_m2 * 70.0 * perf_factor  # Base U ~70 W/m²K

        if effective_ua >= required_ua_w_per_k:
            margin = effective_ua / required_ua_w_per_k - 1.0
            if margin < best_margin:
                best_margin = margin
                best_radiator = radiator

    if best_radiator is None:
        # Fallback to largest radiator if none meets requirements
        best_radiator = max(available_radiators, key=lambda r: r.face_area_m2)
        perf_factor = radiator_performance_factor(best_radiator, air_velocity_m_s, coolant_velocity_m_s)
        effective_ua = best_radiator.face_area_m2 * 70.0 * perf_factor
        best_margin = effective_ua / required_ua_w_per_k - 1.0

    return best_radiator, best_margin


def expansion_tank_detailed(system_volume_l: float, operating_temp_c: float, max_temp_c: float,
                           coolant: Coolant, tank_precharge_bar: float = 1.5) -> Dict[str, float]:
    """Detailed expansion tank calculation with thermal expansion and safety margins."""
    # Thermal expansion coefficient for coolant
    if coolant.medium.lower() == "water":
        beta_per_c = 0.00021  # 1/K
    else:
        # Glycol mixtures have higher expansion
        base_beta = 0.00021
        glycol_factor = 1.0 + 0.0005 * coolant.glycol_percent
        beta_per_c = base_beta * glycol_factor

    delta_t = max_temp_c - operating_temp_c
    expansion_volume_l = system_volume_l * beta_per_c * delta_t

    # Safety margins: 20% for uncertainty, 10% for air pocket
    safety_factor = 1.3
    required_tank_volume_l = expansion_volume_l * safety_factor

    # Pre-charge pressure consideration
    # Atmospheric pressure at tank location (assume sea level)
    atm_pressure_bar = 1.013
    max_pressure_bar = atm_pressure_bar + (system_volume_l * 9.81 * 0.001) / 100000  # Hydrostatic

    return {
        "expansion_volume_l": expansion_volume_l,
        "required_tank_volume_l": required_tank_volume_l,
        "max_system_pressure_bar": max_pressure_bar,
        "recommended_precharge_bar": tank_precharge_bar,
        "safety_margin_percent": (safety_factor - 1.0) * 100
    }


def materials_galvanic_series() -> Dict[str, int]:
    """Galvanic series ranking (lower number = more anodic = more likely to corrode)."""
    return {
        "magnesium": 1,
        "zinc": 2,
        "aluminum": 3,
        "carbon steel": 4,
        "cast iron": 5,
        "stainless_steel_410": 6,
        "stainless_steel_304": 7,
        "stainless_steel_316": 8,
        "brass": 9,
        "copper": 10,
        "bronze": 11,
        "stainless_steel_316l": 12,
        "titanium": 13,
        "platinum": 14
    }


def materials_galvanic_check(materials: List[str], coolant_conductivity_us_cm: float = 500) -> List[str]:
    """Enhanced galvanic corrosion risk assessment."""
    warnings = []
    galvanic_series = materials_galvanic_series()

    # Normalize material names
    normalized_materials = {}
    for mat in materials:
        mat_lower = mat.strip().lower().replace(' ', '_')
        # Basic mapping for common materials
        if 'aluminum' in mat_lower or 'aluminium' in mat_lower:
            normalized_materials['aluminum'] = galvanic_series['aluminum']
        elif 'copper' in mat_lower:
            normalized_materials['copper'] = galvanic_series['copper']
        elif 'brass' in mat_lower:
            normalized_materials['brass'] = galvanic_series['brass']
        elif 'stainless' in mat_lower or 'ss' in mat_lower:
            if '316' in mat_lower:
                normalized_materials['stainless_steel_316'] = galvanic_series['stainless_steel_316']
            elif '304' in mat_lower:
                normalized_materials['stainless_steel_304'] = galvanic_series['stainless_steel_304']
            else:
                normalized_materials['stainless_steel_304'] = galvanic_series['stainless_steel_304']

    if len(normalized_materials) < 2:
        return warnings  # Need at least 2 materials for galvanic corrosion

    # Check for high-risk pairs
    materials_list = list(normalized_materials.keys())
    potentials = [normalized_materials[mat] for mat in materials_list]

    max_potential_diff = max(potentials) - min(potentials)

    if max_potential_diff >= 7:  # Significant galvanic difference
        anode = materials_list[potentials.index(min(potentials))]
        cathode = materials_list[potentials.index(max(potentials))]
        warnings.append(f"CRITICAL: High galvanic corrosion risk between {anode} and {cathode}. "
                       f"Potential difference: {max_potential_diff} positions in galvanic series.")

    if coolant_conductivity_us_cm > 100:  # Conductive coolant increases risk
        warnings.append("WARNING: Coolant conductivity is high, increasing galvanic corrosion risk. "
                       "Consider deionized water or corrosion inhibitors.")

    return warnings


def get_radiator_catalog() -> List[RadiatorSpec]:
    """Standard radiator catalog for mining applications."""
    return [
        RadiatorSpec(
            name="Alphacool NexXxoS XT45",
            face_area_m2=0.024,
            core_volume_l=0.15,
            tube_count=11,
            fin_density_fpi=18,
            tube_diameter_mm=4.0,
            air_side_area_m2=0.15,
            coolant_side_area_m2=0.014,
            price_usd=85.0
        ),
        RadiatorSpec(
            name="EKWB EK-CoolStream XE 360",
            face_area_m2=0.039,
            core_volume_l=0.25,
            tube_count=16,
            fin_density_fpi=16,
            tube_diameter_mm=4.0,
            air_side_area_m2=0.25,
            coolant_side_area_m2=0.020,
            price_usd=120.0
        ),
        RadiatorSpec(
            name="Corsair H100i Elite Capellix",
            face_area_m2=0.028,
            core_volume_l=0.20,
            tube_count=12,
            fin_density_fpi=20,
            tube_diameter_mm=4.0,
            air_side_area_m2=0.18,
            coolant_side_area_m2=0.015,
            price_usd=110.0
        ),
        RadiatorSpec(
            name="Noctua NH-D15S",
            face_area_m2=0.016,
            core_volume_l=0.12,
            tube_count=6,
            fin_density_fpi=22,
            tube_diameter_mm=3.0,
            air_side_area_m2=0.12,
            coolant_side_area_m2=0.008,
            price_usd=75.0
        ),
        RadiatorSpec(
            name="Mining-grade Bar & Plate 500mm",
            face_area_m2=0.062,
            core_volume_l=0.40,
            tube_count=24,
            fin_density_fpi=14,
            tube_diameter_mm=5.0,
            air_side_area_m2=0.40,
            coolant_side_area_m2=0.030,
            price_usd=200.0
        ),
        RadiatorSpec(
            name="Industrial Heat Exchanger 800mm",
            face_area_m2=0.096,
            core_volume_l=0.60,
            tube_count=36,
            fin_density_fpi=12,
            tube_diameter_mm=6.0,
            air_side_area_m2=0.60,
            coolant_side_area_m2=0.045,
            price_usd=350.0
        )
    ]


def coolant_properties(medium: str, glycol_percent: int, temperature_c: float) -> Dict[str, float]:
    return Coolant(medium=medium, glycol_percent=glycol_percent, temperature_c=temperature_c).properties





