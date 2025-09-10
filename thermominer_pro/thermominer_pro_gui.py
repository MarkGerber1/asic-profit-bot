"""
ThermoMiner Pro Desktop Application
Simple GUI demonstrating core thermal calculation functionality
"""

import sys
import json
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Try to import PyQt6, fallback to PyQt5 or Tkinter
try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    PYQT_VERSION = 6
except ImportError:
    try:
        from PyQt5.QtWidgets import *
        from PyQt5.QtCore import *
        from PyQt5.QtGui import *
        PYQT_VERSION = 5
    except ImportError:
        print("PyQt not available, using Tkinter")
        import tkinter as tk
        from tkinter import ttk, messagebox
        PYQT_VERSION = None

# Import ThermoMiner Pro modules
from coredb import CoreDB
from core.hydro_core import *
from core.airflow_core import *
from core.finance_core import Component, Scenario, compare_scenarios
from core.risk_engine import assess_hydro
from knowledge_base_pro import get_knowledge_base


if PYQT_VERSION:
    class ThermoMinerProApp(QMainWindow):
        """Main application window for ThermoMiner Pro."""

        def __init__(self):
            super().__init__()
            self.db = CoreDB()
            self.kb = get_knowledge_base()

            self.init_ui()
            self.load_sample_data()

        def init_ui(self):
            """Initialize the main UI components."""
            self.setWindowTitle("ThermoMiner Pro - Thermal Calculator for Mining Farms")
            self.setGeometry(100, 100, 1200, 800)

            # Create central widget with tab widget
            self.tabs = QTabWidget()
            self.setCentralWidget(self.tabs)

            # Add tabs
            self.tabs.addTab(self.create_hydro_tab(), "Hydro Cooling")
            self.tabs.addTab(self.create_airflow_tab(), "Air Cooling")
            self.tabs.addTab(self.create_comparison_tab(), "Comparison")
            self.tabs.addTab(self.create_knowledge_tab(), "Knowledge Base")

            # Status bar
            self.statusBar().showMessage("Ready")

            # Menu bar
            self.create_menu()

        def create_hydro_tab(self):
            """Create hydro cooling calculation tab."""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Input section
            input_group = QGroupBox("Input Parameters")
            input_layout = QFormLayout(input_group)

            # ASIC selection
            self.vendor_combo = QComboBox()
            self.vendor_combo.addItems(["Bitmain", "MicroBT"])
            self.vendor_combo.currentTextChanged.connect(self.update_models)
            input_layout.addRow("Vendor:", self.vendor_combo)

            self.model_combo = QComboBox()
            input_layout.addRow("Model:", self.model_combo)

            # Parameters
            self.tdp_input = QDoubleSpinBox()
            self.tdp_input.setRange(50, 500)
            self.tdp_input.setValue(100)
            input_layout.addRow("TDP (W):", self.tdp_input)

            self.theta_input = QDoubleSpinBox()
            self.theta_input.setRange(0.01, 1.0)
            self.theta_input.setDecimals(3)
            self.theta_input.setValue(0.02)
            input_layout.addRow("Thermal Resistance (°C/W):", self.theta_input)

            self.coolant_temp_input = QDoubleSpinBox()
            self.coolant_temp_input.setRange(10, 50)
            self.coolant_temp_input.setValue(25)
            input_layout.addRow("Coolant Inlet (°C):", self.coolant_temp_input)

            layout.addWidget(input_group)

            # Calculate button
            self.calc_hydro_btn = QPushButton("Calculate Hydro System")
            self.calc_hydro_btn.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; padding: 10px; }")
            self.calc_hydro_btn.clicked.connect(self.calculate_hydro)
            layout.addWidget(self.calc_hydro_btn)

            # Results section
            results_group = QGroupBox("Results")
            results_layout = QVBoxLayout(results_group)

            self.hydro_results = QTextEdit()
            self.hydro_results.setReadOnly(True)
            results_layout.addWidget(self.hydro_results)

            layout.addWidget(results_group)

            # Update models initially
            self.update_models()

            return tab

        def create_airflow_tab(self):
            """Create airflow calculation tab."""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Room configuration
            room_group = QGroupBox("Room Configuration")
            room_layout = QFormLayout(room_group)

            self.room_length = QDoubleSpinBox()
            self.room_length.setRange(3, 50)
            self.room_length.setValue(10)
            room_layout.addRow("Length (m):", self.room_length)

            self.room_width = QDoubleSpinBox()
            self.room_width.setRange(3, 30)
            self.room_width.setValue(6)
            room_layout.addRow("Width (m):", self.room_width)

            self.room_height = QDoubleSpinBox()
            self.room_height.setRange(2, 10)
            self.room_height.setValue(3)
            room_layout.addRow("Height (m):", self.room_height)

            layout.addWidget(room_group)

            # ASIC configuration
            asic_group = QGroupBox("ASIC Configuration")
            asic_layout = QFormLayout(asic_group)

            self.total_tdp = QDoubleSpinBox()
            self.total_tdp.setRange(1000, 100000)
            self.total_tdp.setValue(3000)
            asic_layout.addRow("Total TDP (W):", self.total_tdp)

            layout.addWidget(asic_group)

            # Calculate button
            self.calc_airflow_btn = QPushButton("Calculate Airflow Requirements")
            self.calc_airflow_btn.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; padding: 10px; }")
            self.calc_airflow_btn.clicked.connect(self.calculate_airflow)
            layout.addWidget(self.calc_airflow_btn)

            # Results
            self.airflow_results = QTextEdit()
            self.airflow_results.setReadOnly(True)
            layout.addWidget(self.airflow_results)

            return tab

        def create_comparison_tab(self):
            """Create scenario comparison tab."""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            layout.addWidget(QLabel("Scenario Comparison Tool"))

            # Scenario inputs
            scenarios_layout = QHBoxLayout()

            # Air cooling
            air_group = QGroupBox("Air Cooling Scenario")
            air_layout = QFormLayout(air_group)

            self.air_capex = QDoubleSpinBox()
            self.air_capex.setRange(0, 10000)
            self.air_capex.setValue(500)
            air_layout.addRow("CAPEX ($):", self.air_capex)

            self.air_power = QDoubleSpinBox()
            self.air_power.setRange(0, 1000)
            self.air_power.setValue(120)
            air_layout.addRow("Power (W):", self.air_power)

            scenarios_layout.addWidget(air_group)

            # Hydro cooling
            hydro_group = QGroupBox("Hydro Cooling Scenario")
            hydro_layout = QFormLayout(hydro_group)

            self.hydro_capex = QDoubleSpinBox()
            self.hydro_capex.setRange(0, 20000)
            self.hydro_capex.setValue(1200)
            hydro_layout.addRow("CAPEX ($):", self.hydro_capex)

            self.hydro_power = QDoubleSpinBox()
            self.hydro_power.setRange(0, 1000)
            self.hydro_power.setValue(80)
            hydro_layout.addRow("Power (W):", self.hydro_power)

            scenarios_layout.addWidget(hydro_group)

            layout.addLayout(scenarios_layout)

            # Electricity price
            price_layout = QHBoxLayout()
            price_layout.addWidget(QLabel("Electricity Price ($/kWh):"))
            self.elec_price = QDoubleSpinBox()
            self.elec_price.setRange(0.01, 1.0)
            self.elec_price.setValue(0.10)
            self.elec_price.setDecimals(3)
            price_layout.addWidget(self.elec_price)
            price_layout.addStretch()
            layout.addLayout(price_layout)

            # Compare button
            self.compare_btn = QPushButton("Compare Scenarios")
            self.compare_btn.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; padding: 10px; }")
            self.compare_btn.clicked.connect(self.compare_scenarios_gui)
            layout.addWidget(self.compare_btn)

            # Results
            self.comparison_results = QTextEdit()
            self.comparison_results.setReadOnly(True)
            layout.addWidget(self.comparison_results)

            return tab

        def create_knowledge_tab(self):
            """Create knowledge base tab."""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Search
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("Search:"))
            self.kb_search = QLineEdit()
            self.kb_search.textChanged.connect(self.search_kb)
            search_layout.addWidget(self.kb_search)
            layout.addLayout(search_layout)

            # Content
            splitter = QSplitter(Qt.Orientation.Horizontal)

            self.article_list = QListWidget()
            self.article_list.itemClicked.connect(self.show_article)
            splitter.addWidget(self.article_list)

            self.article_content = QTextEdit()
            self.article_content.setReadOnly(True)
            splitter.addWidget(self.article_content)

            layout.addWidget(splitter)

            # Populate articles
            self.populate_kb_list()

            return tab

        def create_menu(self):
            """Create application menu."""
            menubar = self.menuBar()

            # File menu
            file_menu = menubar.addMenu('File')
            exit_action = QAction('Exit', self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            # Help menu
            help_menu = menubar.addMenu('Help')
            about_action = QAction('About', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)

        def update_models(self):
            """Update model combo box."""
            vendor = self.vendor_combo.currentText()
            self.model_combo.clear()
            self.model_combo.addItem("Custom")

            asics = self.db.list_asics(vendor=vendor)
            for asic in asics[:10]:  # Limit to 10 for UI
                self.model_combo.addItem(asic.model)

        def calculate_hydro(self):
            """Calculate hydro cooling system."""
            try:
                tdp = self.tdp_input.value()
                theta = self.theta_input.value()
                t_in = self.coolant_temp_input.value()

                # Calculate flow requirements
                props = coolant_properties("water", 0, t_in)
                m_dot = mass_flow_for_heat(tdp, props["cp"], 5.0)  # 5°C rise
                flow_lpm = volumetric_flow_lpm(m_dot, props["rho"])
                t_chip = compute_chip_temperature(tdp, t_in, theta)

                # Radiator sizing
                UA = required_UA_for_Q(tdp, t_in + 5, 30, m_dot * props["cp"], tdp / (1005.0 * 10) * 1005.0)

                # Select radiator
                radiator_catalog = get_radiator_catalog()
                selected_radiator, margin = select_radiator_from_catalog(
                    UA, radiator_catalog, tdp / (1005.0 * 10), flow_lpm
                )

                results = f"""
=== HYDRO COOLING CALCULATION ===

ASIC Parameters:
- TDP: {tdp:.0f} W
- Thermal Resistance: {theta:.3f} °C/W
- Coolant Inlet: {t_in:.1f} °C

Flow Requirements:
- Required Flow: {flow_lpm:.2f} L/min
- Predicted Chip Temperature: {t_chip:.1f} °C

Radiator System:
- Required UA: {UA:.0f} W/K
- Recommended: {selected_radiator.name}
- Price: ${selected_radiator.price_usd:.0f}
- Performance Margin: {margin:.1%}
"""
                self.hydro_results.setText(results)
                self.statusBar().showMessage("Hydro calculation completed")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")

        def calculate_airflow(self):
            """Calculate airflow requirements."""
            try:
                length = self.room_length.value()
                width = self.room_width.value()
                height = self.room_height.value()
                tdp = self.total_tdp.value()

                # Calculate required airflow
                airflow = required_airflow_m3_h(tdp, 25, 35)  # 25°C to 35°C rise

                # Room volume
                volume = length * width * height

                results = f"""
=== AIRFLOW CALCULATION ===

Room Configuration:
- Dimensions: {length:.1f} × {width:.1f} × {height:.1f} m
- Volume: {volume:.1f} m³

ASIC Load:
- Total TDP: {tdp:.0f} W

Airflow Requirements:
- Required Airflow: {airflow:.0f} m³/h
- Required Airflow: {airflow * 0.588:.0f} CFM
- Air Changes per Hour: {airflow / volume:.1f}

Recommended Fan Configuration:
- Intake Fans: 2 × {airflow/2 * 0.588 / 1000:.1f}k CFM each
- Exhaust Fans: 2 × {airflow/2 * 0.588 / 1000:.1f}k CFM each
"""
                self.airflow_results.setText(results)
                self.statusBar().showMessage("Airflow calculation completed")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")

        def compare_scenarios_gui(self):
            """Compare cooling scenarios."""
            try:
                air_capex = self.air_capex.value()
                air_power = self.air_power.value()
                hydro_capex = self.hydro_capex.value()
                hydro_power = self.hydro_power.value()
                elec_price = self.elec_price.value()

                # Create scenarios
                air_scenario = Scenario(
                    name="Air Cooling",
                    components=[Component("Fans", air_capex, air_power)],
                    baseline_revenue_usd_per_day=100.0,
                    electricity_price_usd_per_kwh=elec_price
                )

                hydro_scenario = Scenario(
                    name="Hydro Cooling",
                    components=[
                        Component("Pump", hydro_capex * 0.3, hydro_power),
                        Component("Radiator", hydro_capex * 0.7, 0)
                    ],
                    baseline_revenue_usd_per_day=105.0,  # 5% hashrate gain
                    electricity_price_usd_per_kwh=elec_price
                )

                # Compare
                comparison = compare_scenarios(air_scenario, hydro_scenario)

                results = f"""
=== SCENARIO COMPARISON ===

Air Cooling:
- CAPEX: ${air_capex:.0f}
- Daily Power Cost: ${air_scenario.opex_electricity_per_day():.2f}
- Daily Profit: ${air_scenario.gross_profit_per_day():.2f}

Hydro Cooling:
- CAPEX: ${hydro_capex:.0f}
- Daily Power Cost: ${hydro_scenario.opex_electricity_per_day():.2f}
- Daily Profit: ${hydro_scenario.gross_profit_per_day():.2f}

Comparison:
- Daily Profit Difference: ${comparison['delta_profit_per_day']:.2f}
- Payback Period: {comparison['alt_payback_days']:.0f} days
- ROI: {comparison['alt_roi_per_year']*100:.1f}% per year
"""
                self.comparison_results.setText(results)
                self.statusBar().showMessage("Scenario comparison completed")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Comparison failed: {str(e)}")

        def populate_kb_list(self):
            """Populate knowledge base article list."""
            self.article_list.clear()
            for article_id, article in self.kb.articles.items():
                self.article_list.addItem(f"{article.title} ({article.difficulty})")

        def search_kb(self):
            """Search knowledge base."""
            query = self.kb_search.text().lower()
            self.article_list.clear()

            for article_id, article in self.kb.articles.items():
                if (query in article.title.lower() or
                    query in article.content.lower() or
                    query in article.category.lower()):
                    self.article_list.addItem(f"{article.title} ({article.difficulty})")

        def show_article(self, item):
            """Show selected article content."""
            title = item.text().split(" (")[0]
            for article in self.kb.articles.values():
                if article.title == title:
                    self.article_content.setText(article.content)
                    break

        def load_sample_data(self):
            """Load sample ASIC data."""
            try:
                n = self.db.import_csv("thermominer_pro/coredb/sample_data/asic_coredb.csv")
                self.statusBar().showMessage(f"Loaded {n} ASIC models")
            except Exception as e:
                print(f"Could not load sample data: {e}")

        def show_about(self):
            """Show about dialog."""
            QMessageBox.about(self, "About ThermoMiner Pro",
                "ThermoMiner Pro v1.0\n\n"
                "Intelligent Thermal Calculator for Mining Farm Survival\n\n"
                "Features:\n"
                "- ASIC thermal database\n"
                "- Hydro cooling system design\n"
                "- Airflow analysis\n"
                "- Financial comparison\n"
                "- Knowledge base\n\n"
                "Developed with engineering precision for mining operations.")

else:
    # Tkinter fallback
    class ThermoMinerProApp:
        """Tkinter version of ThermoMiner Pro."""

        def __init__(self):
            self.db = CoreDB()
            self.kb = get_knowledge_base()

            self.root = tk.Tk()
            self.root.title("ThermoMiner Pro - Thermal Calculator for Mining Farms")
            self.root.geometry("1000x700")

            self.create_ui()
            self.load_sample_data()

        def create_ui(self):
            """Create Tkinter UI."""
            # Create notebook (tabs)
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True)

            # Hydro tab
            hydro_frame = ttk.Frame(self.notebook)
            self.notebook.add(hydro_frame, text='Hydro Cooling')
            self.create_hydro_tab(hydro_frame)

            # Airflow tab
            airflow_frame = ttk.Frame(self.notebook)
            self.notebook.add(airflow_frame, text='Air Cooling')
            self.create_airflow_tab(airflow_frame)

            # Comparison tab
            compare_frame = ttk.Frame(self.notebook)
            self.notebook.add(compare_frame, text='Comparison')
            self.create_comparison_tab(compare_frame)

        def create_hydro_tab(self, parent):
            """Create hydro cooling tab."""
            # Input section
            input_frame = ttk.LabelFrame(parent, text="Input Parameters")
            input_frame.pack(fill='x', padx=10, pady=5)

            # TDP input
            ttk.Label(input_frame, text="TDP (W):").grid(row=0, column=0, sticky='w')
            self.tdp_var = tk.StringVar(value="100")
            ttk.Entry(input_frame, textvariable=self.tdp_var).grid(row=0, column=1)

            # Thermal resistance
            ttk.Label(input_frame, text="Thermal Resistance (°C/W):").grid(row=1, column=0, sticky='w')
            self.theta_var = tk.StringVar(value="0.02")
            ttk.Entry(input_frame, textvariable=self.theta_var).grid(row=1, column=1)

            # Coolant temperature
            ttk.Label(input_frame, text="Coolant Inlet (°C):").grid(row=2, column=0, sticky='w')
            self.coolant_temp_var = tk.StringVar(value="25")
            ttk.Entry(input_frame, textvariable=self.coolant_temp_var).grid(row=2, column=1)

            # Calculate button
            ttk.Button(input_frame, text="Calculate Hydro System",
                      command=self.calculate_hydro_tk).grid(row=3, column=0, columnspan=2, pady=10)

            # Results
            results_frame = ttk.LabelFrame(parent, text="Results")
            results_frame.pack(fill='both', expand=True, padx=10, pady=5)

            self.hydro_results_text = tk.Text(results_frame, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(results_frame, command=self.hydro_results_text.yview)
            self.hydro_results_text.config(yscrollcommand=scrollbar.set)

            self.hydro_results_text.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

        def create_airflow_tab(self, parent):
            """Create airflow tab."""
            # Room configuration
            room_frame = ttk.LabelFrame(parent, text="Room Configuration")
            room_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(room_frame, text="Length (m):").grid(row=0, column=0, sticky='w')
            self.room_length_var = tk.StringVar(value="10")
            ttk.Entry(room_frame, textvariable=self.room_length_var).grid(row=0, column=1)

            ttk.Label(room_frame, text="Width (m):").grid(row=1, column=0, sticky='w')
            self.room_width_var = tk.StringVar(value="6")
            ttk.Entry(room_frame, textvariable=self.room_width_var).grid(row=1, column=1)

            ttk.Label(room_frame, text="Height (m):").grid(row=2, column=0, sticky='w')
            self.room_height_var = tk.StringVar(value="3")
            ttk.Entry(room_frame, textvariable=self.room_height_var).grid(row=2, column=1)

            ttk.Label(room_frame, text="Total TDP (W):").grid(row=3, column=0, sticky='w')
            self.total_tdp_var = tk.StringVar(value="3000")
            ttk.Entry(room_frame, textvariable=self.total_tdp_var).grid(row=3, column=1)

            ttk.Button(room_frame, text="Calculate Airflow",
                      command=self.calculate_airflow_tk).grid(row=4, column=0, columnspan=2, pady=10)

            # Results
            self.airflow_results_text = tk.Text(parent, wrap=tk.WORD)
            self.airflow_results_text.pack(fill='both', expand=True, padx=10, pady=5)

        def create_comparison_tab(self, parent):
            """Create comparison tab."""
            # Scenario inputs
            scenarios_frame = ttk.Frame(parent)
            scenarios_frame.pack(fill='x', padx=10, pady=5)

            # Air cooling
            air_frame = ttk.LabelFrame(scenarios_frame, text="Air Cooling")
            air_frame.pack(side='left', fill='both', expand=True, padx=5)

            ttk.Label(air_frame, text="CAPEX ($):").grid(row=0, column=0, sticky='w')
            self.air_capex_var = tk.StringVar(value="500")
            ttk.Entry(air_frame, textvariable=self.air_capex_var).grid(row=0, column=1)

            ttk.Label(air_frame, text="Power (W):").grid(row=1, column=0, sticky='w')
            self.air_power_var = tk.StringVar(value="120")
            ttk.Entry(air_frame, textvariable=self.air_power_var).grid(row=1, column=1)

            # Hydro cooling
            hydro_frame = ttk.LabelFrame(scenarios_frame, text="Hydro Cooling")
            hydro_frame.pack(side='right', fill='both', expand=True, padx=5)

            ttk.Label(hydro_frame, text="CAPEX ($):").grid(row=0, column=0, sticky='w')
            self.hydro_capex_var = tk.StringVar(value="1200")
            ttk.Entry(hydro_frame, textvariable=self.hydro_capex_var).grid(row=0, column=1)

            ttk.Label(hydro_frame, text="Power (W):").grid(row=1, column=0, sticky='w')
            self.hydro_power_var = tk.StringVar(value="80")
            ttk.Entry(hydro_frame, textvariable=self.hydro_power_var).grid(row=1, column=1)

            # Electricity price
            price_frame = ttk.Frame(parent)
            price_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(price_frame, text="Electricity Price ($/kWh):").pack(side='left')
            self.elec_price_var = tk.StringVar(value="0.10")
            ttk.Entry(price_frame, textvariable=self.elec_price_var).pack(side='left')

            ttk.Button(price_frame, text="Compare Scenarios",
                      command=self.compare_scenarios_tk).pack(side='right')

            # Results
            self.comparison_results_text = tk.Text(parent, wrap=tk.WORD)
            self.comparison_results_text.pack(fill='both', expand=True, padx=10, pady=5)

        def calculate_hydro_tk(self):
            """Calculate hydro cooling system (Tkinter version)."""
            try:
                tdp = float(self.tdp_var.get())
                theta = float(self.theta_var.get())
                t_in = float(self.coolant_temp_var.get())

                # Calculate flow requirements
                props = coolant_properties("water", 0, t_in)
                m_dot = mass_flow_for_heat(tdp, props["cp"], 5.0)
                flow_lpm = volumetric_flow_lpm(m_dot, props["rho"])
                t_chip = compute_chip_temperature(tdp, t_in, theta)

                # Radiator sizing
                UA = required_UA_for_Q(tdp, t_in + 5, 30, m_dot * props["cp"], tdp / (1005.0 * 10) * 1005.0)

                results = f"""
=== HYDRO COOLING CALCULATION ===

ASIC Parameters:
- TDP: {tdp:.0f} W
- Thermal Resistance: {theta:.3f} °C/W
- Coolant Inlet: {t_in:.1f} °C

Flow Requirements:
- Required Flow: {flow_lpm:.2f} L/min
- Predicted Chip Temperature: {t_chip:.1f} °C

Radiator System:
- Required UA: {UA:.0f} W/K

Calculation completed successfully!
"""
                self.hydro_results_text.delete(1.0, tk.END)
                self.hydro_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Error", f"Calculation failed: {str(e)}")

        def calculate_airflow_tk(self):
            """Calculate airflow requirements (Tkinter version)."""
            try:
                length = float(self.room_length_var.get())
                width = float(self.room_width_var.get())
                height = float(self.room_height_var.get())
                tdp = float(self.total_tdp_var.get())

                # Calculate required airflow
                airflow = required_airflow_m3_h(tdp, 25, 35)
                volume = length * width * height

                results = f"""
=== AIRFLOW CALCULATION ===

Room Configuration:
- Dimensions: {length:.1f} × {width:.1f} × {height:.1f} m
- Volume: {volume:.1f} m³

ASIC Load:
- Total TDP: {tdp:.0f} W

Airflow Requirements:
- Required Airflow: {airflow:.0f} m³/h
- Required Airflow: {airflow * 0.588:.0f} CFM
- Air Changes per Hour: {airflow / volume:.1f}

Calculation completed successfully!
"""
                self.airflow_results_text.delete(1.0, tk.END)
                self.airflow_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Error", f"Calculation failed: {str(e)}")

        def compare_scenarios_tk(self):
            """Compare cooling scenarios (Tkinter version)."""
            try:
                air_capex = float(self.air_capex_var.get())
                air_power = float(self.air_power_var.get())
                hydro_capex = float(self.hydro_capex_var.get())
                hydro_power = float(self.hydro_power_var.get())
                elec_price = float(self.elec_price_var.get())

                # Simple comparison calculation
                air_daily_cost = air_power * 24 / 1000 * elec_price
                hydro_daily_cost = hydro_power * 24 / 1000 * elec_price

                air_daily_profit = 100.0 - air_daily_cost  # Assume $100 baseline revenue
                hydro_daily_profit = 105.0 - hydro_daily_cost  # 5% hashrate gain

                delta_profit = hydro_daily_profit - air_daily_profit
                payback_days = hydro_capex / delta_profit if delta_profit > 0 else float('inf')

                results = f"""
=== SCENARIO COMPARISON ===

Air Cooling:
- CAPEX: ${air_capex:.0f}
- Daily Power Cost: ${air_daily_cost:.2f}
- Daily Profit: ${air_daily_profit:.2f}

Hydro Cooling:
- CAPEX: ${hydro_capex:.0f}
- Daily Power Cost: ${hydro_daily_cost:.2f}
- Daily Profit: ${hydro_daily_profit:.2f}

Comparison:
- Daily Profit Difference: ${delta_profit:.2f}
- Payback Period: {payback_days:.0f} days

Calculation completed successfully!
"""
                self.comparison_results_text.delete(1.0, tk.END)
                self.comparison_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Error", f"Comparison failed: {str(e)}")

        def load_sample_data(self):
            """Load sample ASIC data."""
            try:
                n = self.db.import_csv("thermominer_pro/coredb/sample_data/asic_coredb.csv")
                print(f"Loaded {n} ASIC models")
            except Exception as e:
                print(f"Could not load sample data: {e}")

        def run(self):
            """Run the application."""
            self.root.mainloop()


def main():
    """Main entry point for ThermoMiner Pro GUI."""
    if PYQT_VERSION:
        app = QApplication(sys.argv)
        window = ThermoMinerProApp()
        window.show()
        sys.exit(app.exec())
    else:
        app = ThermoMinerProApp()
        app.run()


if __name__ == "__main__":
    main()
