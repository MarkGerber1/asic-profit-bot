"""ThermoMiner Pro core package.

This package contains the physics-based calculation engines, lightweight CoreDB,
and a simple CLI for early validation. It is framework-agnostic and can be wired
into a Django/React or PyQt UI later.

Design principles:
- Physics-first with conservative safety margins
- Modular, testable components
- No heavy dependencies by default; graceful fallbacks where possible
"""

__all__ = [
    "core",
    "coredb",
]


