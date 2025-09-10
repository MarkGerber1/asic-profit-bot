from __future__ import annotations

import csv
import json
import os
import sqlite3
from typing import Iterable, List, Optional, Dict, Any

from .models import AsicModel


ASIC_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS asics (
    id INTEGER PRIMARY KEY,
    vendor TEXT NOT NULL,
    model TEXT NOT NULL,

    tdp_w_min REAL,
    tdp_w_max REAL,

    theta_chip_coolant_c_per_w REAL,
    theta_chip_case_c_per_w REAL,
    theta_case_sink_c_per_w REAL,

    stock_fans_cfm REAL,
    stock_fans_static_pressure_pa REAL,
    fan_curve TEXT,
    noise_db REAL,

    t_junc_max_c REAL,
    t_pcb_max_c REAL,
    t_inlet_air_max_c REAL,

    hydro_req_flow_lpm REAL,
    hydro_deltaT_chip_coolant_c REAL,
    hydro_max_pressure_bar REAL,
    hydro_max_inlet_c REAL,
    block_pressure_drop_kpa REAL,

    dimensions_mm TEXT,
    heat_zones TEXT,
    status TEXT,
    notes TEXT,
    extra TEXT,

    UNIQUE(vendor, model)
);
"""


class CoreDB:
    """SQLite-backed CoreDB with CSV import/export.

    The DB path defaults to a local file in the repository directory. It can be
    overridden by passing db_path.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            db_path = os.path.join(base_dir, "thermominer_core.db")
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(ASIC_SCHEMA_SQL)
            conn.commit()
        finally:
            conn.close()

    def upsert_asic(self, asic: AsicModel) -> None:
        row = asic.to_row()
        columns = ",".join(row.keys())
        placeholders = ":" + ",:".join(row.keys())
        sql = f"""
        INSERT INTO asics ({columns})
        VALUES ({placeholders})
        ON CONFLICT(vendor, model) DO UPDATE SET
        {", ".join([f"{k}=excluded.{k}" for k in row.keys() if k not in ("vendor", "model")])}
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(sql, row)
            conn.commit()
        finally:
            conn.close()

    def get_asic(self, vendor: str, model: str) -> Optional[AsicModel]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM asics WHERE vendor=? AND model=?", (vendor, model)
            )
            r = cur.fetchone()
            if not r:
                return None
            return AsicModel.from_row(dict(r))
        finally:
            conn.close()

    def list_asics(self, vendor: Optional[str] = None, status: Optional[str] = None) -> List[AsicModel]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM asics"
            params: List[Any] = []
            clauses: List[str] = []
            if vendor:
                clauses.append("vendor=?")
                params.append(vendor)
            if status:
                clauses.append("status=?")
                params.append(status)
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += " ORDER BY vendor, model"
            rows = conn.execute(query, params).fetchall()
            return [AsicModel.from_row(dict(r)) for r in rows]
        finally:
            conn.close()

    def import_csv(self, csv_path: str) -> int:
        """Import ASICs from CSV.

        Unknown columns are stored under the `extra` JSON field.
        Returns the number of imported rows.
        """
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                known_fields = {
                    "vendor", "model",
                    "tdp_w_min", "tdp_w_max",
                    "theta_chip_coolant_c_per_w", "theta_chip_case_c_per_w", "theta_case_sink_c_per_w",
                    "stock_fans_cfm", "stock_fans_static_pressure_pa", "noise_db",
                    "t_junc_max_c", "t_pcb_max_c", "t_inlet_air_max_c",
                    "hydro_req_flow_lpm", "hydro_deltaT_chip_coolant_c", "hydro_max_pressure_bar", "hydro_max_inlet_c",
                    "block_pressure_drop_kpa", "status", "notes",
                }
                dict_fields = {"fan_curve", "dimensions_mm", "heat_zones"}

                data: Dict[str, Any] = {}
                extra: Dict[str, Any] = {}
                for k, v in row.items():
                    if k in dict_fields:
                        try:
                            data[k] = json.loads(v) if v else None
                        except Exception:
                            data[k] = None
                    elif k in known_fields:
                        if v == "":
                            data[k] = None
                        else:
                            try:
                                if k in {"vendor", "model", "status", "notes"}:
                                    data[k] = v
                                else:
                                    data[k] = float(v)
                            except ValueError:
                                data[k] = None
                    else:
                        if v:
                            extra[k] = v
                data["extra"] = extra
                asic = AsicModel(**data)
                self.upsert_asic(asic)
                count += 1
        return count

    def export_csv(self, csv_path: str) -> int:
        """Export ASICs to CSV. Returns number of rows written."""
        fields = [
            "vendor", "model",
            "tdp_w_min", "tdp_w_max",
            "theta_chip_coolant_c_per_w", "theta_chip_case_c_per_w", "theta_case_sink_c_per_w",
            "stock_fans_cfm", "stock_fans_static_pressure_pa", "fan_curve", "noise_db",
            "t_junc_max_c", "t_pcb_max_c", "t_inlet_air_max_c",
            "hydro_req_flow_lpm", "hydro_deltaT_chip_coolant_c", "hydro_max_pressure_bar", "hydro_max_inlet_c",
            "block_pressure_drop_kpa",
            "dimensions_mm", "heat_zones", "status", "notes", "extra",
        ]
        rows = [a.to_row() for a in self.list_asics()]
        for r in rows:
            for key in ("fan_curve", "dimensions_mm", "heat_zones", "extra"):
                # Keep JSON as string
                if r.get(key) is None:
                    r[key] = ""
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)





