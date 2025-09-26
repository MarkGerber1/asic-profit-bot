#!/usr/bin/env python3
"""
ThermoMiner Pro GUI Launcher
Run the desktop application for thermal calculations
"""

import sys
import os

# Add the thermominer_pro directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from thermominer_pro_gui import main

if __name__ == "__main__":
    print("Starting ThermoMiner Pro Desktop Application...")
    print("ThermoMiner Pro - Intelligent Thermal Calculator for Mining Farms")
    print("=" * 70)
    main()









