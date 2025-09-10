"""CoreDB: Lightweight ASIC models database (SQLite + CSV import/export).

This module provides a simple schema to store ASIC thermal and mechanical
parameters required by the engines. It favors extensibility via JSON columns
for curves (fan P-Q, pump H-Q) and geometry metadata.
"""

from .coredb import CoreDB
from .models import AsicModel

__all__ = ["CoreDB", "AsicModel"]


