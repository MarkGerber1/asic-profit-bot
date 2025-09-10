from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import math


AIR_CP_J_PER_KG_K = 1005.0


def air_density_kg_m3(temperature_c: float = 25.0, relative_humidity: float = 0.5, altitude_m: float = 0.0) -> float:
    """Approximate air density using ISA sea-level corrections.

    This uses a simple barometric correction for altitude and ideal gas for temperature.
    """
    # Standard: rho0 = 1.225 kg/m3 at 15C, sea level
    rho0 = 1.225
    # Temperature correction (ideal gas): rho ∝ 1 / T_abs
    T0_K = 288.15  # 15C
    T_K = temperature_c + 273.15
    rho_T = rho0 * (T0_K / T_K)
    # Altitude correction: rho ≈ rho0 * exp(-h/H), H ~ 8500 m
    H = 8500.0
    rho = rho_T * math.exp(-max(0.0, altitude_m) / H)
    # Ignore humidity for simplicity (minor effect for our purpose)
    return rho


def required_airflow_m3_h(Q_w: float, inlet_temp_c: float, outlet_temp_c: float, altitude_m: float = 0.0) -> float:
    deltaT = max(0.1, outlet_temp_c - inlet_temp_c)
    rho = air_density_kg_m3(temperature_c=inlet_temp_c, altitude_m=altitude_m)
    m_dot = Q_w / (AIR_CP_J_PER_KG_K * deltaT)  # kg/s
    volumetric_m3_s = m_dot / rho
    return volumetric_m3_s * 3600.0


def m3h_to_cfm(m3h: float) -> float:
    return m3h / 1.699


def cfm_to_m3h(cfm: float) -> float:
    return cfm * 1.699


def darcy_friction_factor(Re: float) -> float:
    if Re < 2300:
        return 64.0 / max(Re, 1e-6)
    # Blasius correlation for turbulent smooth ducts: f = 0.3164/Re^0.25
    return 0.3164 / (Re ** 0.25)


def duct_pressure_drop_pa(rho: float, mu: float, volumetric_flow_m3_s: float, diameter_m: float, length_m: float, K_minor: float = 0.0) -> float:
    area = math.pi * (diameter_m ** 2) / 4.0
    velocity = volumetric_flow_m3_s / max(area, 1e-12)
    Re = rho * velocity * diameter_m / mu
    f = darcy_friction_factor(Re)
    dp_friction = f * (length_m / diameter_m) * 0.5 * rho * velocity ** 2
    dp_minor = K_minor * 0.5 * rho * velocity ** 2
    return dp_friction + dp_minor


@dataclass
class FanCurve:
    points: List[Tuple[float, float]]  # (flow_cfm, static_pressure_pa)

    def static_pressure_for_flow(self, flow_cfm: float) -> float:
        pts = sorted(self.points)
        if flow_cfm <= pts[0][0]:
            return pts[0][1]
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            if flow_cfm <= x1:
                # linear interpolation
                t = (flow_cfm - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return max(0.0, pts[-1][1] - 2.0 * (flow_cfm - pts[-1][0]))  # extrapolate down


def find_operating_point(fan: FanCurve, system_k_pa_per_cfm2: float) -> Tuple[float, float]:
    """Solve for flow where fan static pressure equals system quadratic resistance.

    system: ΔP = K * Q^2 (Pa), with Q in CFM (converted internally if needed).
    Returns (flow_cfm, static_pressure_pa).
    """
    # Bisection over flow
    lo, hi = 0.0, max(p[0] for p in fan.points) * 1.5
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fan_sp = fan.static_pressure_for_flow(mid)
        sys_sp = system_k_pa_per_cfm2 * (mid ** 2)
        if fan_sp > sys_sp:
            lo = mid
        else:
            hi = mid
        if hi - lo < 0.1:
            break
    flow = 0.5 * (lo + hi)
    return flow, fan.static_pressure_for_flow(flow)


def system_resistance_K_from_point(flow_cfm: float, dp_pa: float) -> float:
    return dp_pa / max(1e-6, flow_cfm ** 2)


def predict_inlet_temperature(ambient_c: float, recirculation_fraction: float, exhaust_temp_c: float) -> float:
    r = max(0.0, min(0.9, recirculation_fraction))
    return ambient_c * (1 - r) + exhaust_temp_c * r


@dataclass
class RackPosition:
    """Represents a mining rack position and orientation."""
    x: float  # Position in room (m)
    y: float
    orientation: str  # "front_to_back" or "side_to_side"
    asic_count: int
    total_tdp_w: float
    inlet_area_m2: float
    exhaust_area_m2: float


@dataclass
class RoomGeometry:
    """Room ventilation geometry and thermal properties."""
    length_m: float
    width_m: float
    height_m: float
    u_value_walls_w_per_m2k: float = 0.5  # Heat loss through walls
    air_changes_per_hour: float = 2.0  # Natural ventilation rate
    floor_area_m2: Optional[float] = None

    @property
    def volume_m3(self) -> float:
        return self.length_m * self.width_m * self.height_m

    @property
    def surface_area_m2(self) -> float:
        # Approximate surface area (walls + ceiling, excluding floor)
        return 2 * (self.length_m * self.height_m + self.width_m * self.height_m) + self.length_m * self.width_m


def calculate_hotspot_temperature_distribution(
    room: RoomGeometry,
    racks: List[RackPosition],
    ambient_temp_c: float,
    total_airflow_m3_s: float,
    fan_positions: List[Tuple[float, float]]  # (x, y) positions
) -> Dict[str, List[float]]:
    """Simplified CFD-lite analysis for temperature distribution and hotspots.

    Returns temperature distribution across the room grid.
    """
    # Create room grid (simplified 2D analysis)
    grid_x = int(room.length_m * 2)  # 0.5m resolution
    grid_y = int(room.width_m * 2)
    temp_grid = [[ambient_temp_c for _ in range(grid_y)] for _ in range(grid_x)]

    # Heat sources from racks
    for rack in racks:
        grid_i = int(rack.x * 2)
        grid_j = int(rack.y * 2)
        if 0 <= grid_i < grid_x and 0 <= grid_j < grid_y:
            # Heat addition based on TDP and airflow
            heat_addition_c = (rack.total_tdp_w * 0.1) / total_airflow_m3_s  # Rough estimate
            temp_grid[grid_i][grid_j] += heat_addition_c

    # Fan cooling effects
    for fan_x, fan_y in fan_positions:
        grid_i = int(fan_x * 2)
        grid_j = int(fan_y * 2)
        if 0 <= grid_i < grid_x and 0 <= grid_j < grid_y:
            # Cooling effect radius
            for di in range(-2, 3):
                for dj in range(-2, 3):
                    if di == 0 and dj == 0:
                        temp_grid[grid_i][grid_j] -= 2.0  # Direct cooling
                    elif abs(di) + abs(dj) <= 2:
                        gi, gj = grid_i + di, grid_j + dj
                        if 0 <= gi < grid_x and 0 <= gj < grid_y:
                            temp_grid[gi][gj] -= 1.0 / (abs(di) + abs(dj) + 1)

    # Extract hotspot analysis
    all_temps = [temp for row in temp_grid for temp in row]
    max_temp = max(all_temps)
    min_temp = min(all_temps)
    avg_temp = sum(all_temps) / len(all_temps)

    # Find hotspots (temperatures > average + 5C)
    hotspots = []
    for i in range(grid_x):
        for j in range(grid_y):
            if temp_grid[i][j] > avg_temp + 5.0:
                hotspots.append({
                    "x": i * 0.5,
                    "y": j * 0.5,
                    "temperature": temp_grid[i][j],
                    "delta_from_ambient": temp_grid[i][j] - ambient_temp_c
                })

    return {
        "temperature_grid": temp_grid,
        "max_temperature": max_temp,
        "min_temperature": min_temp,
        "average_temperature": avg_temp,
        "hotspots": hotspots,
        "temperature_variance": sum((t - avg_temp) ** 2 for t in all_temps) / len(all_temps)
    }


def calculate_ventilation_network_resistance(
    duct_segments: List[Dict[str, float]],
    fittings: List[Dict[str, str]]
) -> Dict[str, float]:
    """Calculate total resistance in ventilation network.

    duct_segments: List of {"length_m": float, "diameter_m": float, "flow_m3_s": float}
    fittings: List of {"type": str, "count": int}
    """
    total_dp_pa = 0.0

    # Duct friction losses
    for segment in duct_segments:
        length = segment["length_m"]
        diameter = segment["diameter_m"]
        flow = segment["flow_m3_s"]

        # Cross-sectional area
        area = math.pi * (diameter ** 2) / 4.0
        velocity = flow / area

        # Reynolds number and friction factor
        re = 1.225 * velocity * diameter / 1.8e-5  # Air at 20C
        f = 0.3164 / (re ** 0.25) if re > 2300 else 64.0 / re

        # Pressure drop
        dp_segment = f * (length / diameter) * 0.5 * 1.225 * velocity ** 2
        total_dp_pa += dp_segment

    # Fitting losses
    fitting_loss_coefficients = {
        "90_degree_elbow": 0.75,
        "45_degree_elbow": 0.35,
        "tee_branch": 1.0,
        "damper_half_open": 2.5,
        "expansion": 0.4,
        "contraction": 0.2
    }

    for fitting in fittings:
        k = fitting_loss_coefficients.get(fitting["type"], 0.5)
        count = fitting.get("count", 1)
        # Use average velocity for fitting losses
        avg_velocity = sum(seg["flow_m3_s"] / (math.pi * (seg["diameter_m"] ** 2) / 4.0)
                          for seg in duct_segments) / len(duct_segments)
        dp_fitting = count * k * 0.5 * 1.225 * avg_velocity ** 2
        total_dp_pa += dp_fitting

    # Dynamic losses at inlets/outlets
    inlet_loss = 0.5 * 1.225 * (sum(seg["flow_m3_s"] / (math.pi * (seg["diameter_m"] ** 2) / 4.0)
                                    for seg in duct_segments) / len(duct_segments)) ** 2
    total_dp_pa += inlet_loss

    return {
        "total_pressure_drop_pa": total_dp_pa,
        "duct_friction_pa": total_dp_pa - inlet_loss,
        "fitting_losses_pa": sum(fitting_loss_coefficients.get(f["type"], 0.5) * f.get("count", 1) * 0.5 * 1.225 *
                                (sum(seg["flow_m3_s"] / (math.pi * (seg["diameter_m"] ** 2) / 4.0)
                                    for seg in duct_segments) / len(duct_segments)) ** 2
                               for f in fittings),
        "inlet_losses_pa": inlet_loss
    }


def optimize_fan_placement(
    room: RoomGeometry,
    racks: List[RackPosition],
    ambient_temp_c: float
) -> Dict[str, List[Tuple[float, float]]]:
    """Optimize fan placement for best cooling distribution."""
    # Simple optimization: place fans to balance temperature distribution
    recommendations = []

    # Calculate centroid of heat sources
    total_heat = sum(rack.total_tdp_w for rack in racks)
    centroid_x = sum(rack.x * rack.total_tdp_w for rack in racks) / total_heat
    centroid_y = sum(rack.y * rack.total_tdp_w for rack in racks) / total_heat

    # Recommend fans around the centroid
    fan_positions = [
        (centroid_x - 1.0, centroid_y),  # Left of centroid
        (centroid_x + 1.0, centroid_y),  # Right of centroid
        (centroid_x, centroid_y - 1.0),  # Front of centroid
        (centroid_x, centroid_y + 1.0),  # Back of centroid
    ]

    # Filter to room boundaries
    valid_positions = [
        (x, y) for x, y in fan_positions
        if 0 <= x <= room.length_m and 0 <= y <= room.width_m
    ]

    recommendations.append(("optimal_fan_positions", valid_positions))

    # Alternative: perimeter placement
    perimeter_positions = [
        (room.length_m * 0.25, 0),  # Front wall
        (room.length_m * 0.75, 0),
        (room.length_m, room.width_m * 0.25),  # Right wall
        (room.length_m, room.width_m * 0.75),
        (room.length_m * 0.75, room.width_m),  # Back wall
        (room.length_m * 0.25, room.width_m),
        (0, room.width_m * 0.75),  # Left wall
        (0, room.width_m * 0.25),
    ]

    recommendations.append(("perimeter_fan_positions", perimeter_positions))

    return dict(recommendations)







