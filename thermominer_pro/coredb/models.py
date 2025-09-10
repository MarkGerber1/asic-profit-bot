from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import json


@dataclass
class AsicModel:
    """ASIC model technical record.

    Notes:
    - Thermal resistances are represented on the path from chip to coolant/air.
    - Use None when data is unknown. Engines will apply conservative defaults.
    - Curves are stored as JSON in the DB (e.g., fan P-Q curves).
    """

    vendor: str
    model: str

    # Power (heat) envelope
    tdp_w_min: Optional[float] = None
    tdp_w_max: Optional[float] = None

    # Thermal resistances (C/W)
    theta_chip_coolant_c_per_w: Optional[float] = None  # immersion/hydro path
    theta_chip_case_c_per_w: Optional[float] = None     # air/hybrid path
    theta_case_sink_c_per_w: Optional[float] = None     # air/hybrid path

    # Stock fans (air cooling)
    stock_fans_cfm: Optional[float] = None
    stock_fans_static_pressure_pa: Optional[float] = None
    fan_curve: Optional[Dict[str, Any]] = None  # {cfm: Pa} points or arrays
    noise_db: Optional[float] = None

    # Critical temperatures
    t_junc_max_c: Optional[float] = None
    t_pcb_max_c: Optional[float] = None
    t_inlet_air_max_c: Optional[float] = None

    # Hydro parameters (if applicable)
    hydro_req_flow_lpm: Optional[float] = None
    hydro_deltaT_chip_coolant_c: Optional[float] = None
    hydro_max_pressure_bar: Optional[float] = None
    hydro_max_inlet_c: Optional[float] = None
    block_pressure_drop_kpa: Optional[float] = None  # at nominal flow

    # Geometry, heat zones, and metadata
    dimensions_mm: Optional[Dict[str, float]] = None  # {L,W,H,Weight}
    heat_zones: Optional[Dict[str, Any]] = None
    status: str = "active"  # active|deprecated|rare
    notes: Optional[str] = None

    # Flexible extra fields to capture vendor-specific data
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> Dict[str, Any]:
        row = asdict(self)
        # Serialize dict fields to JSON strings for DB
        for key in ("fan_curve", "dimensions_mm", "heat_zones", "extra"):
            value = row.get(key)
            row[key] = json.dumps(value) if value is not None else None
        return row

    @staticmethod
    def from_row(row: Dict[str, Any]) -> "AsicModel":
        def parse_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
            if value is None:
                return None
            try:
                return json.loads(value)
            except Exception:
                return None

        return AsicModel(
            vendor=row["vendor"],
            model=row["model"],
            tdp_w_min=row.get("tdp_w_min"),
            tdp_w_max=row.get("tdp_w_max"),
            theta_chip_coolant_c_per_w=row.get("theta_chip_coolant_c_per_w"),
            theta_chip_case_c_per_w=row.get("theta_chip_case_c_per_w"),
            theta_case_sink_c_per_w=row.get("theta_case_sink_c_per_w"),
            stock_fans_cfm=row.get("stock_fans_cfm"),
            stock_fans_static_pressure_pa=row.get("stock_fans_static_pressure_pa"),
            fan_curve=parse_json(row.get("fan_curve")),
            noise_db=row.get("noise_db"),
            t_junc_max_c=row.get("t_junc_max_c"),
            t_pcb_max_c=row.get("t_pcb_max_c"),
            t_inlet_air_max_c=row.get("t_inlet_air_max_c"),
            hydro_req_flow_lpm=row.get("hydro_req_flow_lpm"),
            hydro_deltaT_chip_coolant_c=row.get("hydro_deltaT_chip_coolant_c"),
            hydro_max_pressure_bar=row.get("hydro_max_pressure_bar"),
            hydro_max_inlet_c=row.get("hydro_max_inlet_c"),
            block_pressure_drop_kpa=row.get("block_pressure_drop_kpa"),
            dimensions_mm=parse_json(row.get("dimensions_mm")),
            heat_zones=parse_json(row.get("heat_zones")),
            status=row.get("status", "active"),
            notes=row.get("notes"),
            extra=parse_json(row.get("extra")) or {},
        )





