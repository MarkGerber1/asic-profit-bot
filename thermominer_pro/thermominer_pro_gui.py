"""
ThermoMiner Pro Desktop Application
Simple GUI demonstrating core thermal calculation functionality
"""

import sys
import json
import os
from pathlib import Path
import subprocess
import webbrowser
import traceback

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

# Import messagebox for Tkinter version
if not PYQT_VERSION:
    import tkinter.messagebox as messagebox

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
            self.setWindowTitle("ThermoMiner Pro - Интеллектуальный Калькулятор Охлаждения Майнинг-Ферм")
            self.setGeometry(100, 100, 1200, 800)

            # Create central widget with tab widget
            self.tabs = QTabWidget()
            self.setCentralWidget(self.tabs)

            # Add tabs
            self.tabs.addTab(self.create_hydro_tab(), "Жидкостное Охлаждение")
            self.tabs.addTab(self.create_airflow_tab(), "Воздушное Охлаждение")
            self.tabs.addTab(self.create_comparison_tab(), "Сравнение")
            self.tabs.addTab(self.create_knowledge_tab(), "База Знаний")

            # Status bar
            self.statusBar().showMessage("Готов")

            # Menu bar
            self.create_menu()

        def create_hydro_tab(self):
            """Create hydro cooling calculation tab."""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Input section
            input_group = QGroupBox("Входные Параметры")
            input_layout = QFormLayout(input_group)

            # ASIC selection
            self.vendor_combo = QComboBox()
            self.vendor_combo.addItems(["Bitmain", "MicroBT"])
            self.vendor_combo.currentTextChanged.connect(self.update_models)
            input_layout.addRow("Производитель:", self.vendor_combo)

            self.model_combo = QComboBox()
            input_layout.addRow("Модель:", self.model_combo)

            # Parameters
            self.tdp_input = QDoubleSpinBox()
            self.tdp_input.setRange(50, 500)
            self.tdp_input.setValue(100)
            input_layout.addRow("Мощность TDP (Вт):", self.tdp_input)

            self.theta_input = QDoubleSpinBox()
            self.theta_input.setRange(0.01, 1.0)
            self.theta_input.setDecimals(3)
            self.theta_input.setValue(0.02)
            input_layout.addRow("Термическое сопротивление (°C/Вт):", self.theta_input)

            self.coolant_temp_input = QDoubleSpinBox()
            self.coolant_temp_input.setRange(10, 50)
            self.coolant_temp_input.setValue(25)
            input_layout.addRow("Входная температура (°C):", self.coolant_temp_input)

            layout.addWidget(input_group)

            # Calculate button
            self.calc_hydro_btn = QPushButton("Рассчитать Систему Жидкостного Охлаждения")
            self.calc_hydro_btn.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; padding: 10px; }")
            self.calc_hydro_btn.clicked.connect(self.calculate_hydro)
            layout.addWidget(self.calc_hydro_btn)

            # Results section
            results_group = QGroupBox("Результаты")
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
            room_group = QGroupBox("Конфигурация Помещения")
            room_layout = QFormLayout(room_group)

            self.room_length = QDoubleSpinBox()
            self.room_length.setRange(3, 50)
            self.room_length.setValue(10)
            room_layout.addRow("Длина (м):", self.room_length)

            self.room_width = QDoubleSpinBox()
            self.room_width.setRange(3, 30)
            self.room_width.setValue(6)
            room_layout.addRow("Ширина (м):", self.room_width)

            self.room_height = QDoubleSpinBox()
            self.room_height.setRange(2, 10)
            self.room_height.setValue(3)
            room_layout.addRow("Высота (м):", self.room_height)

            layout.addWidget(room_group)

            # ASIC configuration
            asic_group = QGroupBox("Конфигурация ASIC")
            asic_layout = QFormLayout(asic_group)

            self.total_tdp = QDoubleSpinBox()
            self.total_tdp.setRange(1000, 100000)
            self.total_tdp.setValue(3000)
            asic_layout.addRow("Общая мощность TDP (Вт):", self.total_tdp)

            layout.addWidget(asic_group)

            # Calculate button
            self.calc_airflow_btn = QPushButton("Рассчитать Требования к Вентиляции")
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

            layout.addWidget(QLabel("Инструмент Сравнения Сценариев"))

            # Scenario inputs
            scenarios_layout = QHBoxLayout()

            # Air cooling
            air_group = QGroupBox("Сценарий Воздушного Охлаждения")
            air_layout = QFormLayout(air_group)

            self.air_capex = QDoubleSpinBox()
            self.air_capex.setRange(0, 10000)
            self.air_capex.setValue(500)
            air_layout.addRow("CAPEX ($):", self.air_capex)

            self.air_power = QDoubleSpinBox()
            self.air_power.setRange(0, 1000)
            self.air_power.setValue(120)
            air_layout.addRow("Мощность (Вт):", self.air_power)

            scenarios_layout.addWidget(air_group)

            # Hydro cooling
            hydro_group = QGroupBox("Сценарий Жидкостного Охлаждения")
            hydro_layout = QFormLayout(hydro_group)

            self.hydro_capex = QDoubleSpinBox()
            self.hydro_capex.setRange(0, 20000)
            self.hydro_capex.setValue(1200)
            hydro_layout.addRow("CAPEX ($):", self.hydro_capex)

            self.hydro_power = QDoubleSpinBox()
            self.hydro_power.setRange(0, 1000)
            self.hydro_power.setValue(80)
            hydro_layout.addRow("Мощность (Вт):", self.hydro_power)

            scenarios_layout.addWidget(hydro_group)

            layout.addLayout(scenarios_layout)

            # Electricity price
            price_layout = QHBoxLayout()
            price_layout.addWidget(QLabel("Цена Электроэнергии ($/кВт·ч):"))
            self.elec_price = QDoubleSpinBox()
            self.elec_price.setRange(0.01, 1.0)
            self.elec_price.setValue(0.10)
            self.elec_price.setDecimals(3)
            price_layout.addWidget(self.elec_price)
            price_layout.addStretch()
            layout.addLayout(price_layout)

            # Compare button
            self.compare_btn = QPushButton("Сравнить Сценарии")
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
            search_layout.addWidget(QLabel("Поиск:"))
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
            file_menu = menubar.addMenu('Файл')
            exit_action = QAction('Выход', self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            # Help menu
            help_menu = menubar.addMenu('Справка')
            about_action = QAction('О программе', self)
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

        def update_hydro_models(self, event=None):
            """Update hydro model combo box based on vendor selection."""
            vendor = self.hydro_vendor_var.get()
            print(f"Фильтрация моделей по производителю: {vendor}")

            try:
                if vendor in ["Bitmain", "MicroBT"]:
                    asics = self.db.list_asics(vendor=vendor)
                    models = ["Ручной ввод TDP"] + sorted([asic.model for asic in asics])
                    self.hydro_model_combo['values'] = models
                    print(f"Отфильтровано {len(asics)} моделей для {vendor}")
                elif vendor == "Другой":
                    self.hydro_model_combo['values'] = ["Ручной ввод TDP"]
                else:
                    # Show all models if no vendor selected
                    all_asics = self.db.list_asics()
                    all_models = ["Ручной ввод TDP"] + sorted([asic.model for asic in all_asics])
                    self.hydro_model_combo['values'] = all_models
                    print(f"Показаны все {len(all_asics)} модели")

                self.hydro_model_combo.set("")
            except Exception as e:
                print(f"Ошибка при фильтрации моделей: {e}")
                self.hydro_model_combo['values'] = ["Ручной ввод TDP"]

        def update_hydro_tdp(self, event=None):
            """Update TDP when model is selected."""
            vendor = self.hydro_vendor_var.get()
            model = self.hydro_model_var.get()

            if model and model != "Ручной ввод TDP":
                try:
                    asic = self.db.get_asic(vendor, model)
                    if asic:
                        # Используем среднее значение TDP для более точного расчета
                        tdp_min = asic.tdp_w_min or asic.tdp_w_max or 100
                        tdp_max = asic.tdp_w_max or asic.tdp_w_min or 100
                        tdp_avg = (tdp_min + tdp_max) / 2
                        self.hydro_tdp_var.set(str(int(tdp_avg)))
                        # Автоматически рассчитать общий TDP
                        self.update_total_tdp()
                        print(f"✅ Выбрана модель {model}, TDP: {int(tdp_avg)}W на ASIC")
                except Exception as e:
                    print(f"❌ Ошибка при получении данных ASIC: {e}")
                    self.hydro_tdp_var.set("")
                    self.hydro_total_tdp_var.set("0 Вт")
            elif model == "Ручной ввод TDP":
                self.hydro_tdp_var.set("")
                self.hydro_total_tdp_var.set("0 Вт")
                print("ℹ️ Выбран ручной ввод TDP")

        def update_total_tdp(self):
            """Calculate and display total TDP when quantity changes."""
            try:
                tdp_str = self.hydro_tdp_var.get().strip()
                quantity_str = self.hydro_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.hydro_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"📊 Общий TDP рассчитан: {quantity} × {tdp_per_unit}W = {total_tdp:.0f}W")
                else:
                    self.hydro_total_tdp_var.set("0 Вт")
            except Exception as e:
                print(f"❌ Ошибка расчета TDP: {e}")
                self.hydro_total_tdp_var.set("0 Вт")

        def update_total_tdp_from_tdp_change(self):
            """Calculate and display total TDP when TDP per unit changes."""
            # Avoid infinite recursion by checking if we're already updating
            try:
                tdp_str = self.hydro_tdp_var.get().strip()
                quantity_str = self.hydro_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.hydro_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"🔄 TDP на ASIC изменен на {tdp_per_unit}W, общий TDP: {total_tdp:.0f}W")
            except:
                pass  # Silent fail for TDP changes

        def update_air_models(self, event=None):
            """Update air model combo box based on vendor selection."""
            vendor = self.air_vendor_var.get()
            print(f"Фильтрация воздушных моделей по производителю: {vendor}")

            try:
                if vendor in ["Bitmain", "MicroBT"]:
                    asics = self.db.list_asics(vendor=vendor)
                    models = ["Ручной ввод TDP"] + sorted([asic.model for asic in asics])
                    self.air_model_combo['values'] = models
                    print(f"Отфильтровано {len(asics)} воздушных моделей для {vendor}")
                elif vendor == "Другой":
                    self.air_model_combo['values'] = ["Ручной ввод TDP"]
                else:
                    # Show all models if no vendor selected
                    all_asics = self.db.list_asics()
                    all_models = ["Ручной ввод TDP"] + sorted([asic.model for asic in all_asics])
                    self.air_model_combo['values'] = all_models
                    print(f"Показаны все {len(all_asics)} воздушные модели")

                self.air_model_combo.set("")
            except Exception as e:
                print(f"Ошибка при фильтрации воздушных моделей: {e}")
                self.air_model_combo['values'] = ["Ручной ввод TDP"]

        def update_air_tdp(self, event=None):
            """Update TDP when model is selected."""
            vendor = self.air_vendor_var.get()
            model = self.air_model_var.get()

            if model and model != "Ручной ввод TDP":
                try:
                    asic = self.db.get_asic(vendor, model)
                    if asic:
                        # Используем среднее значение TDP для более точного расчета
                        tdp_min = asic.tdp_w_min or asic.tdp_w_max or 100
                        tdp_max = asic.tdp_w_max or asic.tdp_w_min or 100
                        tdp_avg = (tdp_min + tdp_max) / 2
                        self.air_tdp_var.set(str(int(tdp_avg)))
                        # Автоматически рассчитать общий TDP
                        self.update_total_air_tdp()
                        print(f"✅ Выбрана модель {model} для воздушного охлаждения, TDP: {int(tdp_avg)}W на ASIC")
                except Exception as e:
                    print(f"❌ Ошибка при получении данных ASIC: {e}")
                    self.air_tdp_var.set("")
                    self.air_total_tdp_var.set("0 Вт")
            elif model == "Ручной ввод TDP":
                self.air_tdp_var.set("")
                self.air_total_tdp_var.set("0 Вт")
                print("ℹ️ Выбран ручной ввод TDP для воздушного охлаждения")

        def update_total_air_tdp(self):
            """Calculate and display total TDP when quantity changes."""
            try:
                tdp_str = self.air_tdp_var.get().strip()
                quantity_str = self.air_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.air_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"📊 Общий TDP воздушного охлаждения рассчитан: {quantity} × {tdp_per_unit}W = {total_tdp:.0f}W")
                else:
                    self.air_total_tdp_var.set("0 Вт")
            except Exception as e:
                print(f"❌ Ошибка расчета TDP воздушного охлаждения: {e}")
                self.air_total_tdp_var.set("0 Вт")

        def update_total_air_tdp_from_tdp_change(self):
            """Calculate and display total TDP when TDP per unit changes."""
            try:
                tdp_str = self.air_tdp_var.get().strip()
                quantity_str = self.air_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.air_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"🔄 TDP на ASIC воздушного охлаждения изменен на {tdp_per_unit}W, общий TDP: {total_tdp:.0f}W")
            except:
                pass  # Silent fail for TDP changes

        def initialize_combos(self):
            """Initialize combo boxes after data loading."""
            try:
                # Initialize hydro combos
                self.hydro_vendor_combo.set("")
                self.hydro_model_combo['values'] = ["Ручной ввод TDP"]

                # Initialize air combos
                self.air_vendor_combo.set("")
                self.air_model_combo['values'] = ["Ручной ввод TDP"]

                print("Выпадающие списки инициализированы")
            except Exception as e:
                print(f"Ошибка инициализации: {e}")

        def select_pump(self, required_flow_lpm):
            """Select appropriate pump based on required flow."""
            try:
                # Simple pump selection logic
                if required_flow_lpm <= 20:
                    return {
                        'name': 'Alphacool DC-LT 50/60',
                        'power': 12,
                        'head': 2.8,
                        'price': 80
                    }
                elif required_flow_lpm <= 50:
                    return {
                        'name': 'EKWB D5 Vario',
                        'power': 23,
                        'head': 4.0,
                        'price': 120
                    }
                elif required_flow_lpm <= 100:
                    return {
                        'name': 'EKWB DDC 3.2',
                        'power': 25,
                        'head': 5.2,
                        'price': 130
                    }
                else:
                    return {
                        'name': 'Swiftech MCP35X',
                        'power': 35,
                        'head': 5.0,
                        'price': 160
                    }
            except:
                return {
                    'name': 'Alphacool DC-LT 50/60',
                    'power': 12,
                    'head': 2.8,
                    'price': 80
                }

        def select_fans(self, required_airflow_m3_h):
            """Select appropriate fans based on required airflow."""
            try:
                # Convert m3/h to CFM for fan selection
                required_cfm = required_airflow_m3_h / 1.699

                # More realistic fan selection for mining applications
                if required_cfm <= 500:
                    # Small fans for low airflow
                    cfm_per_fan = 140
                    fan_data = {
                        'model': 'Noctua NF-A14 PWM',
                        'size': '140mm',
                        'cfm': cfm_per_fan,
                        'power': 1.5,
                        'noise': 24.6,
                        'price': 30
                    }
                elif required_cfm <= 1500:
                    # Medium fans for medium airflow
                    cfm_per_fan = 170
                    fan_data = {
                        'model': 'Noctua NF-P14s redux-1200 PWM',
                        'size': '140mm',
                        'cfm': cfm_per_fan,
                        'power': 1.2,
                        'noise': 31.5,
                        'price': 35
                    }
                elif required_cfm <= 4000:
                    # Large fans for high airflow
                    cfm_per_fan = 250
                    fan_data = {
                        'model': 'be quiet! Silent Wings 3 140mm',
                        'size': '140mm',
                        'cfm': cfm_per_fan,
                        'power': 2.5,
                        'noise': 35.0,
                        'price': 45
                    }
                else:
                    # Industrial fans for very high airflow
                    cfm_per_fan = 400
                    fan_data = {
                        'model': 'Noctua NF-A20 PWM',
                        'size': '200mm',
                        'cfm': cfm_per_fan,
                        'power': 3.0,
                        'noise': 38.0,
                        'price': 80
                    }

                # Calculate required quantity with 20% safety margin
                required_quantity = max(1, int((required_cfm * 1.2) / fan_data['cfm']) + 1)

                return {
                    'model': fan_data['model'],
                    'size': fan_data['size'],
                    'cfm': fan_data['cfm'],
                    'power': fan_data['power'],
                    'noise': fan_data['noise'],
                    'price': fan_data['price'],
                    'quantity': required_quantity
                }

            except Exception as e:
                print(f"Ошибка подбора вентиляторов: {e}")
                return {
                    'model': 'Noctua NF-A14 PWM',
                    'size': '140mm',
                    'cfm': 140,
                    'power': 1.5,
                    'noise': 24.6,
                    'price': 30,
                    'quantity': max(4, int(required_airflow_m3_h / 240) + 2)
                }

        def calculate_hydro(self):
            """Calculate hydro cooling system."""
            try:
                # Get TDP per unit and quantity
                tdp_str = self.hydro_tdp_var.get().strip()
                if not tdp_str:
                    raise ValueError("TDP не указан. Выберите модель ASIC или введите TDP вручную.")

                tdp_per_unit = float(tdp_str)
                if tdp_per_unit <= 0:
                    raise ValueError("TDP должен быть положительным числом.")

                quantity_str = self.hydro_quantity_var.get().strip()
                if not quantity_str:
                    raise ValueError("Количество ASIC не указано.")

                quantity = int(quantity_str)
                if quantity <= 0:
                    raise ValueError("Количество ASIC должно быть положительным числом.")

                total_tdp = tdp_per_unit * quantity

                t_in = float(self.coolant_temp_var.get() or "25")

                # Calculate flow requirements (per ASIC, then total)
                props = coolant_properties("water", 0, t_in)
                m_dot_per_unit = mass_flow_for_heat(tdp_per_unit, props["cp"], 5.0)
                flow_lpm_per_unit = volumetric_flow_lpm(m_dot_per_unit, props["rho"])
                total_flow_lpm = flow_lpm_per_unit * quantity

                # For temperature calculation, use conservative approach
                t_chip = compute_chip_temperature(tdp_per_unit, t_in, 0.02)  # Conservative thermal resistance

                # Select radiator based on total TDP
                try:
                    radiator_catalog = get_radiator_catalog()
                    # Select radiator based on total TDP (larger radiator for more heat)
                    if total_tdp <= 500:
                        selected_radiator = radiator_catalog[0]  # Small radiator
                    elif total_tdp <= 1500:
                        selected_radiator = radiator_catalog[1]  # Medium radiator
                    else:
                        selected_radiator = radiator_catalog[2]  # Large radiator

                    radiator_name = selected_radiator.name
                    radiator_price = selected_radiator.price_usd
                    radiator_area = selected_radiator.face_area_m2
                    radiator_volume = selected_radiator.core_volume_l
                    radiator_tubes = selected_radiator.tube_count
                except:
                    radiator_name = "Alphacool NexXxoS XT45"
                    radiator_price = 85.0
                    radiator_area = 0.024
                    radiator_volume = 0.15
                    radiator_tubes = 11

                # Pump selection based on flow requirements
                pump_specs = self.select_pump(total_flow_lpm)

                results = f"""
=== РАСЧЕТ СИСТЕМЫ ЖИДКОСТНОГО ОХЛАЖДЕНИЯ ===

Конфигурация ASIC:
- Модель: {self.hydro_model_var.get() or 'Ручной ввод'}
- TDP на 1 ASIC: {tdp_per_unit:.0f} Вт
- Количество: {quantity} шт
- Общая мощность: {total_tdp:.0f} Вт

Требования к охлаждению:
- Расход на 1 ASIC: {flow_lpm_per_unit:.2f} л/мин
- Общий расход: {total_flow_lpm:.2f} л/мин
- Температура чипа: ~{t_chip:.1f} °C

РЕКОМЕНДУЕМЫЙ РАДИАТОР:
- Модель: {radiator_name}
- Площадь поверхности: {radiator_area:.3f} м²
- Объем ядра: {radiator_volume:.2f} л
- Количество трубок: {radiator_tubes} шт
- Цена: ${radiator_price:.0f}

НАСОСНАЯ СТАНЦИЯ:
- Модель: {pump_specs['name']}
- Мощность: {pump_specs['power']} Вт
- Макс. напор: {pump_specs['head']} м
- Цена: ${pump_specs['price']:.0f}
"""
                self.hydro_results.setText(results)
                self.statusBar().showMessage("Расчет гидроохлаждения завершен")

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
                self.statusBar().showMessage("Расчет вентиляции завершен")

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
                self.statusBar().showMessage("Сравнение сценариев завершено")

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
                n = self.db.import_csv("coredb/sample_data/asic_coredb.csv")
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

            # Initialize UI variables
            self.initialize_variables()

            self.root = tk.Tk()
            self.root.title("ThermoMiner Pro - Интеллектуальный Калькулятор Охлаждения Майнинг-Ферм")
            self.root.geometry("1000x700")

            self.create_ui()
            self.load_sample_data()

        def initialize_variables(self):
            """Initialize all UI variables."""
            # Hydro cooling variables
            self.hydro_vendor_var = tk.StringVar()
            self.hydro_model_var = tk.StringVar()
            self.hydro_quantity_var = tk.StringVar(value="1")
            self.hydro_tdp_var = tk.StringVar(value="")
            self.hydro_total_tdp_var = tk.StringVar(value="0 Вт")
            self.coolant_temp_var = tk.StringVar(value="25")

            # Air cooling variables
            self.air_vendor_var = tk.StringVar()
            self.air_model_var = tk.StringVar()
            self.air_quantity_var = tk.StringVar(value="1")
            self.air_tdp_var = tk.StringVar(value="")
            self.air_total_tdp_var = tk.StringVar(value="0 Вт")

            # Room variables
            self.room_length_var = tk.StringVar(value="10")
            self.room_width_var = tk.StringVar(value="6")
            self.room_height_var = tk.StringVar(value="3")

            # Comparison variables
            self.air_capex_var = tk.StringVar(value="500")
            self.air_power_var = tk.StringVar(value="120")
            self.hydro_capex_var = tk.StringVar(value="1200")
            self.hydro_power_var = tk.StringVar(value="80")
            self.elec_price_var = tk.StringVar(value="0.10")

            # 3D Visualization variables
            self.viz_length_var = tk.StringVar(value="10")
            self.viz_width_var = tk.StringVar(value="6")
            self.viz_height_var = tk.StringVar(value="3")
            self.viz_quantity_var = tk.StringVar(value="10")
            self.viz_tdp_var = tk.StringVar(value="3250")
            self.viz_position_var = tk.StringVar(value="2,2,1")

            # ROI Calculator variables
            self.roi_model_var = tk.StringVar(value="Antminer S19 Pro")
            self.roi_hashrate_var = tk.StringVar(value="110")
            self.roi_power_var = tk.StringVar(value="3250")
            self.roi_quantity_var = tk.StringVar(value="10")
            self.roi_price_var = tk.StringVar(value="2500")
            self.roi_cooling_type_var = tk.StringVar(value="hydro")
            self.roi_cooling_capex_var = tk.StringVar(value="5000")
            self.roi_cooling_power_var = tk.StringVar(value="500")
            self.roi_elec_price_var = tk.StringVar(value="0.08")

            # ML Analysis variables
            self.ml_equipment_id_var = tk.StringVar(value="ASIC-001")
            self.ml_chip_temp_var = tk.StringVar(value="75")
            self.ml_coolant_temp_var = tk.StringVar(value="30")
            self.ml_flow_rate_var = tk.StringVar(value="10")
            self.ml_hashrate_var = tk.StringVar(value="110")

            # Simulation variables
            self.sim_type_var = tk.StringVar(value="pump_failure")
            self.sim_duration_var = tk.StringVar(value="600")
            self.sim_failure_time_var = tk.StringVar(value="60")

            # API status
            self.api_status_label = None

            # Current mapper for 3D visualization
            self.current_mapper = None

        def create_ui(self):
            """Create Tkinter UI."""
            # Initialize theme manager
            from ui.themes import ThemeManager, create_theme_toggle_button
            self.theme_manager = ThemeManager()

            # Top toolbar with theme toggle
            toolbar = ttk.Frame(self.root)
            toolbar.pack(fill='x', padx=10, pady=5)

            # Theme toggle button
            self.theme_toggle_btn = create_theme_toggle_button(
                toolbar,
                self.theme_manager,
                self.on_theme_change
            )
            self.theme_toggle_btn.pack(side='right')

            # Title label
            title_label = ttk.Label(toolbar, text="ThermoMiner Pro - Новые Возможности", font=('Arial', 12, 'bold'))
            title_label.pack(side='left')

            # Create notebook (tabs)
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True)

            # Hydro tab
            hydro_frame = ttk.Frame(self.notebook)
            self.notebook.add(hydro_frame, text='Жидкостное Охлаждение')
            self.create_hydro_tab(hydro_frame)

            # Airflow tab
            airflow_frame = ttk.Frame(self.notebook)
            self.notebook.add(airflow_frame, text='Воздушное Охлаждение')
            self.create_airflow_tab(airflow_frame)

            # Comparison tab
            compare_frame = ttk.Frame(self.notebook)
            self.notebook.add(compare_frame, text='Сравнение')
            self.create_comparison_tab(compare_frame)

            # 3D Visualization tab
            viz_frame = ttk.Frame(self.notebook)
            self.notebook.add(viz_frame, text='3D Визуализация')
            self.create_visualization_tab(viz_frame)

            # ROI Calculator tab
            roi_frame = ttk.Frame(self.notebook)
            self.notebook.add(roi_frame, text='ROI Калькулятор')
            self.create_roi_tab(roi_frame)

            # ML Analysis tab
            ml_frame = ttk.Frame(self.notebook)
            self.notebook.add(ml_frame, text='ML Анализ')
            self.create_ml_tab(ml_frame)

            # Emergency Simulator tab
            sim_frame = ttk.Frame(self.notebook)
            self.notebook.add(sim_frame, text='Симулятор Аварий')
            self.create_simulation_tab(sim_frame)

            # Mobile API tab
            api_frame = ttk.Frame(self.notebook)
            self.notebook.add(api_frame, text='Мобильное API')
            self.create_api_tab(api_frame)

        def create_hydro_tab(self, parent):
            """Create hydro cooling tab."""
            # ASIC Selection section
            asic_frame = ttk.LabelFrame(parent, text="Выбор ASIC")
            asic_frame.pack(fill='x', padx=10, pady=5)

            # Vendor selection
            ttk.Label(asic_frame, text="Производитель:").grid(row=0, column=0, sticky='w')
            self.hydro_vendor_var = tk.StringVar()
            self.hydro_vendor_combo = ttk.Combobox(asic_frame, textvariable=self.hydro_vendor_var,
                                                 values=["Bitmain", "MicroBT", "Другой"])
            self.hydro_vendor_combo.grid(row=0, column=1, padx=5, pady=2)
            self.hydro_vendor_combo.bind('<<ComboboxSelected>>', self.update_hydro_models)

            # Model selection
            ttk.Label(asic_frame, text="Модель ASIC:").grid(row=1, column=0, sticky='w')
            self.hydro_model_var = tk.StringVar()
            self.hydro_model_combo = ttk.Combobox(asic_frame, textvariable=self.hydro_model_var)
            self.hydro_model_combo.grid(row=1, column=1, padx=5, pady=2)
            self.hydro_model_combo.bind('<<ComboboxSelected>>', self.update_hydro_tdp)

            # Quantity
            ttk.Label(asic_frame, text="Количество ASIC:").grid(row=2, column=0, sticky='w')
            self.hydro_quantity_var = tk.StringVar(value="1")
            quantity_entry = ttk.Entry(asic_frame, textvariable=self.hydro_quantity_var)
            quantity_entry.grid(row=2, column=1, padx=5, pady=2)
            self.hydro_quantity_var.trace('w', lambda *args: self.update_total_tdp())

            # TDP per ASIC (auto-filled from model selection, but editable)
            ttk.Label(asic_frame, text="TDP на 1 ASIC (Вт):").grid(row=3, column=0, sticky='w')
            self.hydro_tdp_var = tk.StringVar(value="")
            self.hydro_tdp_entry = ttk.Entry(asic_frame, textvariable=self.hydro_tdp_var)
            self.hydro_tdp_entry.grid(row=3, column=1, padx=5, pady=2)
            # Update total TDP when TDP per unit changes
            self.hydro_tdp_var.trace('w', lambda *args: self.update_total_tdp_from_tdp_change())

            # Total TDP display
            ttk.Label(asic_frame, text="Общая мощность TDP:").grid(row=4, column=0, sticky='w')
            self.hydro_total_tdp_var = tk.StringVar(value="0 Вт")
            ttk.Label(asic_frame, textvariable=self.hydro_total_tdp_var,
                     font=('Arial', 10, 'bold'), foreground='blue').grid(row=4, column=1, sticky='w')

            # Operating conditions
            conditions_frame = ttk.LabelFrame(parent, text="Условия эксплуатации")
            conditions_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(conditions_frame, text="Входная температура (°C):").grid(row=0, column=0, sticky='w')
            self.coolant_temp_var = tk.StringVar(value="25")
            ttk.Entry(conditions_frame, textvariable=self.coolant_temp_var).grid(row=0, column=1, padx=5, pady=2)

            # Calculate button
            ttk.Button(parent, text="Рассчитать Систему Жидкостного Охлаждения",
                      command=self.calculate_hydro).pack(pady=10)

            # Results
            results_frame = ttk.LabelFrame(parent, text="Результаты")
            results_frame.pack(fill='both', expand=True, padx=10, pady=5)

            self.hydro_results_text = tk.Text(results_frame, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(results_frame, command=self.hydro_results_text.yview)
            self.hydro_results_text.config(yscrollcommand=scrollbar.set)

            self.hydro_results_text.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

        def create_airflow_tab(self, parent):
            """Create airflow tab."""
            # ASIC Selection section
            asic_frame = ttk.LabelFrame(parent, text="Выбор ASIC")
            asic_frame.pack(fill='x', padx=10, pady=5)

            # Vendor selection
            ttk.Label(asic_frame, text="Производитель:").grid(row=0, column=0, sticky='w')
            self.air_vendor_var = tk.StringVar()
            self.air_vendor_combo = ttk.Combobox(asic_frame, textvariable=self.air_vendor_var,
                                                values=["Bitmain", "MicroBT", "Другой"])
            self.air_vendor_combo.grid(row=0, column=1, padx=5, pady=2)
            self.air_vendor_combo.bind('<<ComboboxSelected>>', self.update_air_models)

            # Model selection
            ttk.Label(asic_frame, text="Модель ASIC:").grid(row=1, column=0, sticky='w')
            self.air_model_var = tk.StringVar()
            self.air_model_combo = ttk.Combobox(asic_frame, textvariable=self.air_model_var)
            self.air_model_combo.grid(row=1, column=1, padx=5, pady=2)
            self.air_model_combo.bind('<<ComboboxSelected>>', self.update_air_tdp)

            # Quantity
            ttk.Label(asic_frame, text="Количество ASIC:").grid(row=2, column=0, sticky='w')
            self.air_quantity_var = tk.StringVar(value="1")
            air_quantity_entry = ttk.Entry(asic_frame, textvariable=self.air_quantity_var)
            air_quantity_entry.grid(row=2, column=1, padx=5, pady=2)
            self.air_quantity_var.trace('w', lambda *args: self.update_total_air_tdp())

            # TDP per ASIC (auto-filled from model selection, but editable)
            ttk.Label(asic_frame, text="TDP на 1 ASIC (Вт):").grid(row=3, column=0, sticky='w')
            self.air_tdp_var = tk.StringVar(value="")
            self.air_tdp_entry = ttk.Entry(asic_frame, textvariable=self.air_tdp_var)
            self.air_tdp_entry.grid(row=3, column=1, padx=5, pady=2)
            # Update total TDP when TDP per unit changes
            self.air_tdp_var.trace('w', lambda *args: self.update_total_air_tdp_from_tdp_change())

            # Total TDP display
            ttk.Label(asic_frame, text="Общая мощность TDP:").grid(row=4, column=0, sticky='w')
            self.air_total_tdp_var = tk.StringVar(value="0 Вт")
            ttk.Label(asic_frame, textvariable=self.air_total_tdp_var,
                     font=('Arial', 10, 'bold'), foreground='blue').grid(row=4, column=1, sticky='w')

            # Room configuration
            room_frame = ttk.LabelFrame(parent, text="Конфигурация Помещения")
            room_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(room_frame, text="Длина (м):").grid(row=0, column=0, sticky='w')
            self.room_length_var = tk.StringVar(value="10")
            ttk.Entry(room_frame, textvariable=self.room_length_var).grid(row=0, column=1)

            ttk.Label(room_frame, text="Ширина (м):").grid(row=1, column=0, sticky='w')
            self.room_width_var = tk.StringVar(value="6")
            ttk.Entry(room_frame, textvariable=self.room_width_var).grid(row=1, column=1)

            ttk.Label(room_frame, text="Высота (м):").grid(row=2, column=0, sticky='w')
            self.room_height_var = tk.StringVar(value="3")
            ttk.Entry(room_frame, textvariable=self.room_height_var).grid(row=2, column=1)

            ttk.Button(parent, text="Рассчитать Требования к Вентиляции",
                      command=self.calculate_airflow).pack(pady=10)

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

            ttk.Label(price_frame, text="Цена Электроэнергии ($/кВт·ч):").pack(side='left')
            self.elec_price_var = tk.StringVar(value="0.10")
            ttk.Entry(price_frame, textvariable=self.elec_price_var).pack(side='left')

            ttk.Button(price_frame, text="Сравнить Сценарии",
                      command=self.compare_scenarios_gui).pack(side='right')

            # Results
            self.comparison_results_text = tk.Text(parent, wrap=tk.WORD)
            self.comparison_results_text.pack(fill='both', expand=True, padx=10, pady=5)

        def calculate_hydro(self):
            """Calculate hydro cooling system (Tkinter version)."""
            try:
                # Get TDP per unit and quantity from new interface
                tdp_str = self.hydro_tdp_var.get().strip()
                if not tdp_str:
                    raise ValueError("TDP не указан. Выберите модель ASIC или введите TDP вручную.")

                # Support comma as decimal separator
                tdp_per_unit = float(tdp_str.replace(',', '.'))
                if tdp_per_unit <= 0:
                    raise ValueError("TDP должен быть положительным числом.")

                quantity_str = self.hydro_quantity_var.get().strip()
                if not quantity_str:
                    raise ValueError("Количество ASIC не указано.")

                quantity = int(quantity_str)
                if quantity <= 0:
                    raise ValueError("Количество ASIC должно быть положительным числом.")

                total_tdp = tdp_per_unit * quantity
                # Coolant inlet temperature with comma support
                t_in = float((self.coolant_temp_var.get() or "25").replace(',', '.'))

                # Calculate flow requirements (per ASIC, then total)
                props = coolant_properties("water", 0, t_in)
                m_dot_per_unit = mass_flow_for_heat(tdp_per_unit, props["cp"], 5.0)
                flow_lpm_per_unit = volumetric_flow_lpm(m_dot_per_unit, props["rho"])
                total_flow_lpm = flow_lpm_per_unit * quantity

                # For temperature calculation, use conservative approach
                t_chip = compute_chip_temperature(tdp_per_unit, t_in, 0.02)  # Conservative thermal resistance

                # Select radiator based on total TDP
                try:
                    radiator_catalog = get_radiator_catalog()
                    # Select radiator based on total TDP (larger radiator for more heat)
                    if total_tdp <= 500:
                        selected_radiator = radiator_catalog[0]  # Small radiator
                    elif total_tdp <= 1500:
                        selected_radiator = radiator_catalog[1]  # Medium radiator
                    else:
                        selected_radiator = radiator_catalog[2]  # Large radiator

                    radiator_name = selected_radiator.name
                    radiator_price = selected_radiator.price_usd
                    radiator_area = selected_radiator.face_area_m2
                    radiator_volume = selected_radiator.core_volume_l
                    radiator_tubes = selected_radiator.tube_count
                except Exception as e:
                    print(f"Ошибка подбора радиатора: {e}")
                    radiator_name = "Alphacool NexXxoS XT45"
                    radiator_price = 85.0
                    radiator_area = 0.024
                    radiator_volume = 0.15
                    radiator_tubes = 11

                # Pump selection based on flow requirements
                pump_specs = self.select_pump(total_flow_lpm)

                results = f"""
=== РАСЧЕТ СИСТЕМЫ ЖИДКОСТНОГО ОХЛАЖДЕНИЯ ===

Конфигурация ASIC:
- Модель: {self.hydro_model_var.get() or 'Ручной ввод'}
- TDP на 1 ASIC: {tdp_per_unit:.0f} Вт
- Количество: {quantity} шт
- Общая мощность: {total_tdp:.0f} Вт

Требования к охлаждению:
- Расход на 1 ASIC: {flow_lpm_per_unit:.2f} л/мин
- Общий расход: {total_flow_lpm:.2f} л/мин
- Температура чипа: ~{t_chip:.1f} °C

РЕКОМЕНДУЕМЫЙ РАДИАТОР:
- Модель: {radiator_name}
- Площадь поверхности: {radiator_area:.3f} м²
- Объем ядра: {radiator_volume:.2f} л
- Количество трубок: {radiator_tubes} шт
- Цена: ${radiator_price:.0f}

НАСОСНАЯ СТАНЦИЯ:
- Модель: {pump_specs['name']}
- Мощность: {pump_specs['power']} Вт
- Макс. напор: {pump_specs['head']} м
- Цена: ${pump_specs['price']:.0f}

Расчет завершен успешно!
"""
                self.hydro_results_text.delete(1.0, tk.END)
                self.hydro_results_text.insert(tk.END, results)

            except Exception as e:
                # Print full traceback for diagnostics in console and show user-friendly message
                traceback.print_exc()
                messagebox.showerror("Ошибка", f"Расчет не удался: {str(e)}")

        def calculate_airflow(self):
            """Calculate airflow requirements (Tkinter version)."""
            try:
                # Get TDP per unit and quantity
                tdp_str = self.air_tdp_var.get().strip()
                if not tdp_str:
                    raise ValueError("TDP не указан. Выберите модель ASIC или введите TDP вручную.")

                tdp_per_unit = float(tdp_str)
                if tdp_per_unit <= 0:
                    raise ValueError("TDP должен быть положительным числом.")

                quantity_str = self.air_quantity_var.get().strip()
                if not quantity_str:
                    raise ValueError("Количество ASIC не указано.")

                quantity = int(quantity_str)
                if quantity <= 0:
                    raise ValueError("Количество ASIC должно быть положительным числом.")

                total_tdp = tdp_per_unit * quantity

                length = float(self.room_length_var.get())
                width = float(self.room_width_var.get())
                height = float(self.room_height_var.get())

                # Calculate required airflow with mining-specific logic
                # Basic thermal calculation
                basic_airflow = required_airflow_m3_h(total_tdp, 25, 35)
                volume = length * width * height

                # Mining-specific requirements:
                # 1. Minimum 150 CFM per ASIC for proper cooling
                min_cfm_per_asic = 150
                min_airflow_cfm = quantity * min_cfm_per_asic
                min_airflow_m3h = min_airflow_cfm * 1.699

                # 2. Room air exchange: 8x per hour minimum
                room_exchange_m3h = volume * 8

                # Use the maximum of all requirements
                airflow = max(basic_airflow, min_airflow_m3h, room_exchange_m3h)

                print(f"Расчет вентиляции: TDP={total_tdp}W, базовый={basic_airflow:.0f}m³/h, мин.на ASIC={min_airflow_m3h:.0f}m³/h, помещение={room_exchange_m3h:.0f}m³/h → итого={airflow:.0f}m³/h")

                # Select fans based on airflow requirements
                fan_specs = self.select_fans(airflow)

                results = f"""
=== РАСЧЕТ ТРЕБОВАНИЙ К ВЕНТИЛЯЦИИ ===

Конфигурация ASIC:
- Модель: {self.air_model_var.get() or 'Ручной ввод'}
- TDP на 1 ASIC: {tdp_per_unit:.0f} Вт
- Количество: {quantity} шт
- Общая мощность: {total_tdp:.0f} Вт

Конфигурация помещения:
- Размеры: {length:.1f} × {width:.1f} × {height:.1f} м
- Объем: {volume:.1f} м³

Требования к вентиляции:
- Необходимый воздухообмен: {airflow:.0f} м³/ч
- Необходимый воздухообмен: {airflow * 0.588:.0f} CFM
- Кратность воздухообмена: {airflow / volume:.1f} 1/ч

РЕКОМЕНДУЕМЫЕ ВЕНТИЛЯТОРЫ:
- Модель: {fan_specs['model']}
- Размер: {fan_specs['size']}
- Производительность: {fan_specs['cfm']:.0f} CFM ({fan_specs['cfm'] * 1.699:.0f} м³/ч)
- Мощность на 1 вентилятор: {fan_specs['power']:.1f} Вт
- Уровень шума: {fan_specs['noise']:.1f} дБ
- Цена за 1 вентилятор: ${fan_specs['price']:.0f}
- Рекомендуемое количество: {fan_specs['quantity']} шт
- Общая стоимость вентиляторов: ${fan_specs['price'] * fan_specs['quantity']:.0f}
- Общая мощность вентиляторов: {fan_specs['power'] * fan_specs['quantity']:.1f} Вт

Расчет завершен успешно!
"""
                self.airflow_results_text.delete(1.0, tk.END)
                self.airflow_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Расчет не удался: {str(e)}")

        def compare_scenarios_gui(self):
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
=== СРАВНЕНИЕ СЦЕНАРИЕВ ===

Воздушное охлаждение:
- CAPEX: ${air_capex:.0f}
- Суточные затраты на электроэнергию: ${air_daily_cost:.2f}
- Суточная прибыль: ${air_daily_profit:.2f}

Жидкостное охлаждение:
- CAPEX: ${hydro_capex:.0f}
- Суточные затраты на электроэнергию: ${hydro_daily_cost:.2f}
- Суточная прибыль: ${hydro_daily_profit:.2f}

Сравнение:
- Разница в суточной прибыли: ${delta_profit:.2f}
- Срок окупаемости: {payback_days:.0f} дней

Расчет завершен успешно!
"""
                self.comparison_results_text.delete(1.0, tk.END)
                self.comparison_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Сравнение не удалось: {str(e)}")

        def load_sample_data(self):
            """Load sample ASIC data."""
            try:
                n = self.db.import_csv("coredb/sample_data/asic_coredb.csv")
                print(f"Loaded {n} ASIC models")

                # Initialize combo boxes after loading data
                self.initialize_combos()
            except Exception as e:
                print(f"Could not load sample data: {e}")

        def update_hydro_models(self, event=None):
            """Update hydro model combo box based on vendor selection."""
            vendor = self.hydro_vendor_var.get()
            print(f"Фильтрация моделей по производителю: {vendor}")

            try:
                if vendor in ["Bitmain", "MicroBT"]:
                    asics = self.db.list_asics(vendor=vendor)
                    models = ["Ручной ввод TDP"] + sorted([asic.model for asic in asics])
                    self.hydro_model_combo['values'] = models
                    print(f"Отфильтровано {len(asics)} моделей для {vendor}")
                elif vendor == "Другой":
                    self.hydro_model_combo['values'] = ["Ручной ввод TDP"]
                else:
                    # Show all models if no vendor selected
                    all_asics = self.db.list_asics()
                    all_models = ["Ручной ввод TDP"] + sorted([asic.model for asic in all_asics])
                    self.hydro_model_combo['values'] = all_models
                    print(f"Показаны все {len(all_asics)} модели")

                self.hydro_model_combo.set("")
            except Exception as e:
                print(f"Ошибка при фильтрации моделей: {e}")
                self.hydro_model_combo['values'] = ["Ручной ввод TDP"]

        def update_hydro_tdp(self, event=None):
            """Update TDP when model is selected."""
            vendor = self.hydro_vendor_var.get()
            model = self.hydro_model_var.get()

            if model and model != "Ручной ввод TDP":
                try:
                    asic = self.db.get_asic(vendor, model)
                    if asic:
                        # Используем среднее значение TDP для более точного расчета
                        tdp_min = asic.tdp_w_min or asic.tdp_w_max or 100
                        tdp_max = asic.tdp_w_max or asic.tdp_w_min or 100
                        tdp_avg = (tdp_min + tdp_max) / 2
                        self.hydro_tdp_var.set(str(int(tdp_avg)))
                        # Автоматически рассчитать общий TDP
                        self.update_total_tdp()
                        print(f"✅ Выбрана модель {model}, TDP: {int(tdp_avg)}W на ASIC")
                except Exception as e:
                    print(f"❌ Ошибка при получении данных ASIC: {e}")
                    self.hydro_tdp_var.set("")
                    self.hydro_total_tdp_var.set("0 Вт")
            elif model == "Ручной ввод TDP":
                self.hydro_tdp_var.set("")
                self.hydro_total_tdp_var.set("0 Вт")
                print("ℹ️ Выбран ручной ввод TDP")

        def update_total_tdp(self):
            """Calculate and display total TDP when quantity changes."""
            try:
                tdp_str = self.hydro_tdp_var.get().strip()
                quantity_str = self.hydro_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.hydro_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"📊 Общий TDP рассчитан: {quantity} × {tdp_per_unit}W = {total_tdp:.0f}W")
                else:
                    self.hydro_total_tdp_var.set("0 Вт")
            except Exception as e:
                print(f"❌ Ошибка расчета TDP: {e}")
                self.hydro_total_tdp_var.set("0 Вт")

        def update_total_tdp_from_tdp_change(self):
            """Calculate and display total TDP when TDP per unit changes."""
            # Avoid infinite recursion by checking if we're already updating
            try:
                tdp_str = self.hydro_tdp_var.get().strip()
                quantity_str = self.hydro_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.hydro_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"🔄 TDP на ASIC изменен на {tdp_per_unit}W, общий TDP: {total_tdp:.0f}W")
            except:
                pass  # Silent fail for TDP changes

        def update_air_models(self, event=None):
            """Update air model combo box based on vendor selection."""
            vendor = self.air_vendor_var.get()
            print(f"Фильтрация воздушных моделей по производителю: {vendor}")

            try:
                if vendor in ["Bitmain", "MicroBT"]:
                    asics = self.db.list_asics(vendor=vendor)
                    models = ["Ручной ввод TDP"] + sorted([asic.model for asic in asics])
                    self.air_model_combo['values'] = models
                    print(f"Отфильтровано {len(asics)} воздушных моделей для {vendor}")
                elif vendor == "Другой":
                    self.air_model_combo['values'] = ["Ручной ввод TDP"]
                else:
                    # Show all models if no vendor selected
                    all_asics = self.db.list_asics()
                    all_models = ["Ручной ввод TDP"] + sorted([asic.model for asic in all_asics])
                    self.air_model_combo['values'] = all_models
                    print(f"Показаны все {len(all_asics)} воздушные модели")

                self.air_model_combo.set("")
            except Exception as e:
                print(f"Ошибка при фильтрации воздушных моделей: {e}")
                self.air_model_combo['values'] = ["Ручной ввод TDP"]

        def update_air_tdp(self, event=None):
            """Update TDP when model is selected."""
            vendor = self.air_vendor_var.get()
            model = self.air_model_var.get()

            if model and model != "Ручной ввод TDP":
                try:
                    asic = self.db.get_asic(vendor, model)
                    if asic:
                        # Используем среднее значение TDP для более точного расчета
                        tdp_min = asic.tdp_w_min or asic.tdp_w_max or 100
                        tdp_max = asic.tdp_w_max or asic.tdp_w_min or 100
                        tdp_avg = (tdp_min + tdp_max) / 2
                        self.air_tdp_var.set(str(int(tdp_avg)))
                        # Автоматически рассчитать общий TDP
                        self.update_total_air_tdp()
                        print(f"✅ Выбрана модель {model} для воздушного охлаждения, TDP: {int(tdp_avg)}W на ASIC")
                except Exception as e:
                    print(f"❌ Ошибка при получении данных ASIC: {e}")
                    self.air_tdp_var.set("")
                    self.air_total_tdp_var.set("0 Вт")
            elif model == "Ручной ввод TDP":
                self.air_tdp_var.set("")
                self.air_total_tdp_var.set("0 Вт")
                print("ℹ️ Выбран ручной ввод TDP для воздушного охлаждения")

        def update_total_air_tdp(self):
            """Calculate and display total TDP when quantity changes."""
            try:
                tdp_str = self.air_tdp_var.get().strip()
                quantity_str = self.air_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.air_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"📊 Общий TDP воздушного охлаждения рассчитан: {quantity} × {tdp_per_unit}W = {total_tdp:.0f}W")
                else:
                    self.air_total_tdp_var.set("0 Вт")
            except Exception as e:
                print(f"❌ Ошибка расчета TDP воздушного охлаждения: {e}")
                self.air_total_tdp_var.set("0 Вт")

        def update_total_air_tdp_from_tdp_change(self):
            """Calculate and display total TDP when TDP per unit changes."""
            try:
                tdp_str = self.air_tdp_var.get().strip()
                quantity_str = self.air_quantity_var.get().strip()

                if tdp_str and quantity_str:
                    tdp_per_unit = float(tdp_str)
                    quantity = int(quantity_str)
                    total_tdp = tdp_per_unit * quantity
                    self.air_total_tdp_var.set(f"{total_tdp:.0f} Вт")
                    print(f"🔄 TDP на ASIC воздушного охлаждения изменен на {tdp_per_unit}W, общий TDP: {total_tdp:.0f}W")
            except:
                pass  # Silent fail for TDP changes

        def select_pump(self, required_flow_lpm):
            """Select appropriate pump based on required flow."""
            try:
                # Simple pump selection logic
                if required_flow_lpm <= 20:
                    return {
                        'name': 'Alphacool DC-LT 50/60',
                        'power': 12,
                        'head': 2.8,
                        'price': 80
                    }
                elif required_flow_lpm <= 50:
                    return {
                        'name': 'EKWB D5 Vario',
                        'power': 23,
                        'head': 4.0,
                        'price': 120
                    }
                elif required_flow_lpm <= 100:
                    return {
                        'name': 'EKWB DDC 3.2',
                        'power': 25,
                        'head': 5.2,
                        'price': 130
                    }
                else:
                    return {
                        'name': 'Swiftech MCP35X',
                        'power': 35,
                        'head': 5.0,
                        'price': 160
                    }
            except:
                return {
                    'name': 'Alphacool DC-LT 50/60',
                    'power': 12,
                    'head': 2.8,
                    'price': 80
                }

        def select_fans(self, required_airflow_m3_h):
            """Select appropriate fans based on required airflow."""
            try:
                # Convert m3/h to CFM for fan selection
                required_cfm = required_airflow_m3_h / 1.699

                # More realistic fan selection for mining applications
                if required_cfm <= 500:
                    # Small fans for low airflow
                    cfm_per_fan = 140
                    fan_data = {
                        'model': 'Noctua NF-A14 PWM',
                        'size': '140mm',
                        'cfm': cfm_per_fan,
                        'power': 1.5,
                        'noise': 24.6,
                        'price': 30
                    }
                elif required_cfm <= 1500:
                    # Medium fans for medium airflow
                    cfm_per_fan = 170
                    fan_data = {
                        'model': 'Noctua NF-P14s redux-1200 PWM',
                        'size': '140mm',
                        'cfm': cfm_per_fan,
                        'power': 1.2,
                        'noise': 31.5,
                        'price': 35
                    }
                elif required_cfm <= 4000:
                    # Large fans for high airflow
                    cfm_per_fan = 250
                    fan_data = {
                        'model': 'be quiet! Silent Wings 3 140mm',
                        'size': '140mm',
                        'cfm': cfm_per_fan,
                        'power': 2.5,
                        'noise': 35.0,
                        'price': 45
                    }
                else:
                    # Industrial fans for very high airflow
                    cfm_per_fan = 400
                    fan_data = {
                        'model': 'Noctua NF-A20 PWM',
                        'size': '200mm',
                        'cfm': cfm_per_fan,
                        'power': 3.0,
                        'noise': 38.0,
                        'price': 80
                    }

                # Calculate required quantity with 20% safety margin
                required_quantity = max(1, int((required_cfm * 1.2) / fan_data['cfm']) + 1)

                return {
                    'model': fan_data['model'],
                    'size': fan_data['size'],
                    'cfm': fan_data['cfm'],
                    'power': fan_data['power'],
                    'noise': fan_data['noise'],
                    'price': fan_data['price'],
                    'quantity': required_quantity
                }

            except Exception as e:
                print(f"Ошибка подбора вентиляторов: {e}")
                return {
                    'model': 'Noctua NF-A14 PWM',
                    'size': '140mm',
                    'cfm': 140,
                    'power': 1.5,
                    'noise': 24.6,
                    'price': 30,
                    'quantity': max(4, int(required_airflow_m3_h / 240) + 2)
                }

        def initialize_combos(self):
            """Initialize combo boxes after data loading."""
            try:
                # Initialize hydro combos
                self.hydro_vendor_combo.set("")
                # Get all ASIC models and create a combined list
                all_asics = self.db.list_asics()
                all_models = ["Ручной ввод TDP"] + sorted([asic.model for asic in all_asics])
                self.hydro_model_combo['values'] = all_models

                # Initialize air combos
                self.air_vendor_combo.set("")
                self.air_model_combo['values'] = all_models

                print(f"Выпадающие списки инициализированы. Загружено {len(all_asics)} моделей ASIC")
            except Exception as e:
                print(f"Ошибка инициализации: {e}")
                # Fallback initialization
                self.hydro_vendor_combo.set("")
                self.hydro_model_combo['values'] = ["Ручной ввод TDP"]
                self.air_vendor_combo.set("")
                self.air_model_combo['values'] = ["Ручной ввод TDP"]

        def run(self):
            """Run the application."""
            # Ensure combos are initialized
            try:
                self.initialize_combos()
            except:
                pass
            self.root.mainloop()

        def on_theme_change(self, new_theme):
            """Handle theme change."""
            print(f"Тема изменена на: {new_theme['name']}")
            # Apply theme to matplotlib if used
            try:
                from ui.themes import apply_theme_to_matplotlib
                apply_theme_to_matplotlib(self.theme_manager)
            except:
                pass

        def create_visualization_tab(self, parent):
            """Create 3D visualization tab."""
            # Room configuration
            config_frame = ttk.LabelFrame(parent, text="Конфигурация Помещения")
            config_frame.pack(fill='x', padx=10, pady=5)

            # Room dimensions
            ttk.Label(config_frame, text="Длина (м):").grid(row=0, column=0, sticky='w')
            self.viz_length_var = tk.StringVar(value="10")
            ttk.Entry(config_frame, textvariable=self.viz_length_var).grid(row=0, column=1, padx=5)

            ttk.Label(config_frame, text="Ширина (м):").grid(row=1, column=0, sticky='w')
            self.viz_width_var = tk.StringVar(value="6")
            ttk.Entry(config_frame, textvariable=self.viz_width_var).grid(row=1, column=1, padx=5)

            ttk.Label(config_frame, text="Высота (м):").grid(row=2, column=0, sticky='w')
            self.viz_height_var = tk.StringVar(value="3")
            ttk.Entry(config_frame, textvariable=self.viz_height_var).grid(row=2, column=1, padx=5)

            # ASIC configuration
            asic_frame = ttk.LabelFrame(parent, text="Конфигурация ASIC")
            asic_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(asic_frame, text="Количество ASIC:").grid(row=0, column=0, sticky='w')
            self.viz_quantity_var = tk.StringVar(value="10")
            ttk.Entry(asic_frame, textvariable=self.viz_quantity_var).grid(row=0, column=1, padx=5)

            ttk.Label(asic_frame, text="TDP на ASIC (Вт):").grid(row=1, column=0, sticky='w')
            self.viz_tdp_var = tk.StringVar(value="3250")
            ttk.Entry(asic_frame, textvariable=self.viz_tdp_var).grid(row=1, column=1, padx=5)

            ttk.Label(asic_frame, text="Расположение:").grid(row=2, column=0, sticky='w')
            self.viz_position_var = tk.StringVar(value="2,2,1")
            ttk.Entry(asic_frame, textvariable=self.viz_position_var).grid(row=2, column=1, padx=5)
            ttk.Label(asic_frame, text="(x,y,z)").grid(row=2, column=2)

            # Control buttons
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(fill='x', padx=10, pady=5)

            ttk.Button(btn_frame, text="Создать 3D Визуализацию",
                      command=self.create_3d_visualization).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Сохранить в HTML",
                      command=self.save_3d_visualization).pack(side='left', padx=5)

            # Results
            self.viz_results_text = tk.Text(parent, wrap=tk.WORD, height=10)
            scrollbar = ttk.Scrollbar(parent, command=self.viz_results_text.yview)
            self.viz_results_text.config(yscrollcommand=scrollbar.set)

            self.viz_results_text.pack(side='left', fill='both', expand=True, padx=10, pady=5)
            scrollbar.pack(side='right', fill='y')

        def create_roi_tab(self, parent):
            """Create ROI calculator tab."""
            # Mining configuration
            config_frame = ttk.LabelFrame(parent, text="Конфигурация Майнинга")
            config_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(config_frame, text="Модель ASIC:").grid(row=0, column=0, sticky='w')
            self.roi_model_var = tk.StringVar(value="Antminer S19 Pro")
            ttk.Entry(config_frame, textvariable=self.roi_model_var).grid(row=0, column=1, padx=5)

            ttk.Label(config_frame, text="Хешрейт (TH/s):").grid(row=1, column=0, sticky='w')
            self.roi_hashrate_var = tk.StringVar(value="110")
            ttk.Entry(config_frame, textvariable=self.roi_hashrate_var).grid(row=1, column=1, padx=5)

            ttk.Label(config_frame, text="Мощность (Вт):").grid(row=2, column=0, sticky='w')
            self.roi_power_var = tk.StringVar(value="3250")
            ttk.Entry(config_frame, textvariable=self.roi_power_var).grid(row=2, column=1, padx=5)

            ttk.Label(config_frame, text="Количество:").grid(row=3, column=0, sticky='w')
            self.roi_quantity_var = tk.StringVar(value="10")
            ttk.Entry(config_frame, textvariable=self.roi_quantity_var).grid(row=3, column=1, padx=5)

            ttk.Label(config_frame, text="Цена ASIC ($):").grid(row=4, column=0, sticky='w')
            self.roi_price_var = tk.StringVar(value="2500")
            ttk.Entry(config_frame, textvariable=self.roi_price_var).grid(row=4, column=1, padx=5)

            # Cooling costs
            cooling_frame = ttk.LabelFrame(parent, text="Охлаждение")
            cooling_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(cooling_frame, text="Тип охлаждения:").grid(row=0, column=0, sticky='w')
            self.roi_cooling_type_var = tk.StringVar(value="hydro")
            ttk.Combobox(cooling_frame, textvariable=self.roi_cooling_type_var,
                         values=["air", "hydro"]).grid(row=0, column=1, padx=5)

            ttk.Label(cooling_frame, text="CAPEX ($):").grid(row=1, column=0, sticky='w')
            self.roi_cooling_capex_var = tk.StringVar(value="5000")
            ttk.Entry(cooling_frame, textvariable=self.roi_cooling_capex_var).grid(row=1, column=1, padx=5)

            ttk.Label(cooling_frame, text="Мощность (Вт):").grid(row=2, column=0, sticky='w')
            self.roi_cooling_power_var = tk.StringVar(value="500")
            ttk.Entry(cooling_frame, textvariable=self.roi_cooling_power_var).grid(row=2, column=1, padx=5)

            # Electricity
            elec_frame = ttk.LabelFrame(parent, text="Электроэнергия")
            elec_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(elec_frame, text="Цена ($/кВт·ч):").grid(row=0, column=0, sticky='w')
            self.roi_elec_price_var = tk.StringVar(value="0.08")
            ttk.Entry(elec_frame, textvariable=self.roi_elec_price_var).grid(row=0, column=1, padx=5)

            # Control buttons
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(fill='x', padx=10, pady=5)

            ttk.Button(btn_frame, text="Рассчитать ROI",
                      command=self.calculate_roi_gui).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Прогноз на 12 месяцев",
                      command=self.generate_roi_projection).pack(side='left', padx=5)

            # Results
            self.roi_results_text = tk.Text(parent, wrap=tk.WORD, height=15)
            scrollbar = ttk.Scrollbar(parent, command=self.roi_results_text.yview)
            self.roi_results_text.config(yscrollcommand=scrollbar.set)

            self.roi_results_text.pack(side='left', fill='both', expand=True, padx=10, pady=5)
            scrollbar.pack(side='right', fill='y')

        def create_ml_tab(self, parent):
            """Create ML analysis tab."""
            # Sensor data input
            sensor_frame = ttk.LabelFrame(parent, text="Данные Датчиков")
            sensor_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(sensor_frame, text="ID Оборудования:").grid(row=0, column=0, sticky='w')
            self.ml_equipment_id_var = tk.StringVar(value="ASIC-001")
            ttk.Entry(sensor_frame, textvariable=self.ml_equipment_id_var).grid(row=0, column=1, padx=5)

            ttk.Label(sensor_frame, text="Температура чипа (°C):").grid(row=1, column=0, sticky='w')
            self.ml_chip_temp_var = tk.StringVar(value="75")
            ttk.Entry(sensor_frame, textvariable=self.ml_chip_temp_var).grid(row=1, column=1, padx=5)

            ttk.Label(sensor_frame, text="Температура жидкости (°C):").grid(row=2, column=0, sticky='w')
            self.ml_coolant_temp_var = tk.StringVar(value="30")
            ttk.Entry(sensor_frame, textvariable=self.ml_coolant_temp_var).grid(row=2, column=1, padx=5)

            ttk.Label(sensor_frame, text="Расход (л/мин):").grid(row=3, column=0, sticky='w')
            self.ml_flow_rate_var = tk.StringVar(value="10")
            ttk.Entry(sensor_frame, textvariable=self.ml_flow_rate_var).grid(row=3, column=1, padx=5)

            ttk.Label(sensor_frame, text="Хешрейт (TH/s):").grid(row=4, column=0, sticky='w')
            self.ml_hashrate_var = tk.StringVar(value="110")
            ttk.Entry(sensor_frame, textvariable=self.ml_hashrate_var).grid(row=4, column=1, padx=5)

            # Control buttons
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(fill='x', padx=10, pady=5)

            ttk.Button(btn_frame, text="Предсказать Отказ",
                      command=self.predict_failure_gui).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Оптимизировать Охлаждение",
                      command=self.optimize_cooling_gui).pack(side='left', padx=5)

            # Results
            self.ml_results_text = tk.Text(parent, wrap=tk.WORD, height=15)
            scrollbar = ttk.Scrollbar(parent, command=self.ml_results_text.yview)
            self.ml_results_text.config(yscrollcommand=scrollbar.set)

            self.ml_results_text.pack(side='left', fill='both', expand=True, padx=10, pady=5)
            scrollbar.pack(side='right', fill='y')

        def create_simulation_tab(self, parent):
            """Create emergency simulation tab."""
            # Simulation type
            sim_type_frame = ttk.LabelFrame(parent, text="Тип Симуляции")
            sim_type_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(sim_type_frame, text="Сценарий:").grid(row=0, column=0, sticky='w')
            self.sim_type_var = tk.StringVar(value="pump_failure")
            ttk.Combobox(sim_type_frame, textvariable=self.sim_type_var,
                         values=["pump_failure", "fan_failure", "coolant_leak"]).grid(row=0, column=1, padx=5)

            ttk.Label(sim_type_frame, text="Длительность (сек):").grid(row=1, column=0, sticky='w')
            self.sim_duration_var = tk.StringVar(value="600")
            ttk.Entry(sim_type_frame, textvariable=self.sim_duration_var).grid(row=1, column=1, padx=5)

            ttk.Label(sim_type_frame, text="Время отказа (сек):").grid(row=2, column=0, sticky='w')
            self.sim_failure_time_var = tk.StringVar(value="60")
            ttk.Entry(sim_type_frame, textvariable=self.sim_failure_time_var).grid(row=2, column=1, padx=5)

            # Control buttons
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(fill='x', padx=10, pady=5)

            ttk.Button(btn_frame, text="Запустить Симуляцию",
                      command=self.run_emergency_simulation).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Сохранить График",
                      command=self.save_simulation_plot).pack(side='left', padx=5)

            # Results
            self.sim_results_text = tk.Text(parent, wrap=tk.WORD, height=15)
            scrollbar = ttk.Scrollbar(parent, command=self.sim_results_text.yview)
            self.sim_results_text.config(yscrollcommand=scrollbar.set)

            self.sim_results_text.pack(side='left', fill='both', expand=True, padx=10, pady=5)
            scrollbar.pack(side='right', fill='y')

        def create_api_tab(self, parent):
            """Create mobile API tab."""
            # API status
            status_frame = ttk.LabelFrame(parent, text="Статус API Сервера")
            status_frame.pack(fill='x', padx=10, pady=5)

            self.api_status_label = ttk.Label(status_frame, text="Сервер не запущен")
            self.api_status_label.pack(pady=10)

            # Control buttons
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(fill='x', padx=10, pady=5)

            ttk.Button(btn_frame, text="Запустить API Сервер",
                      command=self.start_api_server).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Открыть Документацию",
                      command=self.open_api_docs).pack(side='left', padx=5)

            # API endpoints info
            info_frame = ttk.LabelFrame(parent, text="API Endpoints")
            info_frame.pack(fill='both', expand=True, padx=10, pady=5)

            endpoints_text = """Доступные API endpoints:

GET  /api/status                 - Статус системы
GET  /api/equipment              - Список оборудования
GET  /api/equipment/<id>         - Данные ASIC
POST /api/equipment/<id>         - Обновить данные
GET  /api/alerts                 - Получить алерты
POST /api/roi                    - Расчёт ROI
POST /api/predict_failure        - Предсказание отказа
POST /api/optimize_cooling       - Оптимизация охлаждения
GET  /api/dashboard              - Dashboard сводка

Сервер запускается на: http://0.0.0.0:5000"""

            text_widget = tk.Text(info_frame, wrap=tk.WORD, height=15)
            scrollbar = ttk.Scrollbar(info_frame, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)

            text_widget.insert(tk.END, endpoints_text)
            text_widget.config(state='disabled')

            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

        # Implementation of the methods
        def create_3d_visualization(self):
            """Create 3D thermal visualization."""
            try:
                from visualization import ThermalMapper3D, RoomConfig, AsicPosition

                # Get parameters
                length = float(self.viz_length_var.get())
                width = float(self.viz_width_var.get())
                height = float(self.viz_height_var.get())
                quantity = int(self.viz_quantity_var.get())
                tdp = float(self.viz_tdp_var.get())

                # Parse position
                pos_parts = self.viz_position_var.get().split(',')
                start_x, start_y, start_z = map(float, pos_parts)

                # Create room and ASICs
                room = RoomConfig(length=length, width=width, height=height)
                mapper = ThermalMapper3D(room)
                mapper.add_asic_rack(start_x, start_y, start_z, count=quantity, tdp_per_unit=tdp, model="ASIC")

                # Get analysis
                analysis = mapper.get_hotspot_analysis()

                # Show results
                results = f"""3D ТЕПЛОВАЯ ВИЗУАЛИЗАЦИЯ

Конфигурация помещения:
- Размеры: {length:.1f} × {width:.1f} × {height:.1f} м
- Объём: {length * width * height:.1f} м³

Конфигурация ASIC:
- Количество: {quantity} шт
- TDP на ASIC: {tdp:.0f} Вт
- Общая мощность: {tdp * quantity:.0f} Вт
- Расположение: ({start_x}, {start_y}, {start_z})

АНАЛИЗ ГОРЯЧИХ ТОЧЕК:
- Максимальная температура: {analysis['max_temp']:.1f}°C
- Средняя температура: {analysis['avg_temp']:.1f}°C
- Стандартное отклонение: {analysis['temp_std']:.1f}°C
- Критический объём (>45°C): {analysis['critical_volume_percent']:.1f}%

{'⚠️ ВНИМАНИЕ: Обнаружены критические зоны перегрева!' if analysis['hotspot_warning'] else '✅ Температурный режим в норме'}

Для просмотра 3D визуализации нажмите 'Сохранить в HTML'
"""

                self.viz_results_text.delete(1.0, tk.END)
                self.viz_results_text.insert(tk.END, results)

                # Store mapper for saving
                self.current_mapper = mapper

                messagebox.showinfo("Успех", "3D визуализация создана! Нажмите 'Сохранить в HTML' для просмотра.")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {str(e)}")

        def save_3d_visualization(self):
            """Save 3D visualization to HTML."""
            try:
                if hasattr(self, 'current_mapper'):
                    fig = self.current_mapper.create_plotly_figure()
                    fig.write_html("thermal_3d_visualization.html")
                    messagebox.showinfo("Успех", "3D визуализация сохранена в thermal_3d_visualization.html")
                else:
                    messagebox.showwarning("Предупреждение", "Сначала создайте визуализацию")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить визуализацию: {str(e)}")

        def calculate_roi_gui(self):
            """Calculate ROI using GUI inputs."""
            try:
                from core.roi_calculator import ROICalculator, MiningConfig

                config = MiningConfig(
                    asic_model=self.roi_model_var.get(),
                    hashrate_ths=float(self.roi_hashrate_var.get()),
                    power_consumption_w=float(self.roi_power_var.get()),
                    quantity=int(self.roi_quantity_var.get()),
                    asic_price_usd=float(self.roi_price_var.get()),
                    cooling_type=self.roi_cooling_type_var.get(),
                    cooling_capex_usd=float(self.roi_cooling_capex_var.get()),
                    cooling_power_w=float(self.roi_cooling_power_var.get()),
                    electricity_price_kwh=float(self.roi_elec_price_var.get())
                )

                calc = ROICalculator(config)
                roi = calc.calculate_roi()

                # Format results
                results = f"""РАСЧЁТ ROI - {config.asic_model}

КОНФИГУРАЦИЯ:
- ASIC: {config.asic_model}
- Хешрейт: {config.hashrate_ths} TH/s на ASIC
- Мощность: {config.power_consumption_w} Вт на ASIC
- Количество: {config.quantity} шт
- Цена ASIC: ${config.asic_price_usd:,.0f}

ОХЛАЖДЕНИЕ:
- Тип: {config.cooling_type}
- CAPEX: ${config.cooling_capex_usd:,.0f}
- Мощность: {config.cooling_power_w} Вт

ЭЛЕКТРОЭНЕРГИЯ:
- Цена: ${config.electricity_price_kwh:.4f}/кВт·ч

ДОХОДЫ:
- BTC в день: {roi['btc_per_day']:.8f} BTC
- Доход в день: ${roi['revenue_per_day']:.2f}
- Доход в месяц: ${roi['revenue_per_month']:.2f}
- Доход в год: ${roi['revenue_per_year']:,.2f}

РАСХОДЫ:
- Электричество в день: ${roi['electricity_cost_per_day']:.2f}
- Всего в день: ${roi['total_cost_per_day']:.2f}
- Всего в месяц: ${roi['total_cost_per_month']:.2f}
- Всего в год: ${roi['total_cost_per_year']:,.2f}

ПРИБЫЛЬ:
- В день: ${roi['profit_per_day']:.2f}
- В месяц: ${roi['profit_per_month']:.2f}
- В год: ${roi['profit_per_year']:,.2f}
- Маржа: {roi['profit_margin_percent']:.1f}%

ИНВЕСТИЦИИ И ROI:
- Общие инвестиции: ${roi['total_investment']:,.0f}
- Срок окупаемости: {roi['payback_months']:.1f} месяцев
- ROI за 1 год: {roi['roi_1_year_percent']:.1f}%
- Точка безубыточности: ${roi['breakeven_electricity_price']:.4f}/кВт·ч

ЭФФЕКТИВНОСТЬ:
- Потребление: {roi['power_consumption_kw']:.2f} кВт
- Эффективность: {roi['efficiency_wth']:.1f} Вт/TH

{'✅ ПРИБЫЛЬНО' if roi['is_profitable'] else '❌ УБЫТОЧНО'}
"""

                self.roi_results_text.delete(1.0, tk.END)
                self.roi_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось рассчитать ROI: {str(e)}")

        def generate_roi_projection(self):
            """Generate 12-month ROI projection."""
            try:
                from core.roi_calculator import ROICalculator, MiningConfig

                config = MiningConfig(
                    asic_model=self.roi_model_var.get(),
                    hashrate_ths=float(self.roi_hashrate_var.get()),
                    power_consumption_w=float(self.roi_power_var.get()),
                    quantity=int(self.roi_quantity_var.get()),
                    asic_price_usd=float(self.roi_price_var.get()),
                    cooling_type=self.roi_cooling_type_var.get(),
                    cooling_capex_usd=float(self.roi_cooling_capex_var.get()),
                    cooling_power_w=float(self.roi_cooling_power_var.get()),
                    electricity_price_kwh=float(self.roi_elec_price_var.get())
                )

                calc = ROICalculator(config)
                projections = calc.generate_projection(12)

                results = "ПРОГНОЗ ROI НА 12 МЕСЯЦЕВ (сложность +3%/мес)\n\n"
                results += "Месяц | Прибыль | Накопительно | ROI\n"
                results += "-------|--------|--------------|-----\n"

                for proj in projections:
                    results += f"{proj['month']:6d} | ${proj['monthly_profit']:6.0f} | ${proj['cumulative_profit']:9.0f} | {proj['roi_to_date_percent']:5.1f}%\n"

                self.roi_results_text.delete(1.0, tk.END)
                self.roi_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать прогноз: {str(e)}")

        def predict_failure_gui(self):
            """Predict equipment failure using ML."""
            try:
                from ml import PredictiveMaintenanceModel, SensorData
                from datetime import datetime

                sensor_data = SensorData(
                    timestamp=datetime.now(),
                    chip_temp=float(self.ml_chip_temp_var.get()),
                    coolant_temp=float(self.ml_coolant_temp_var.get()),
                    ambient_temp=25.0,
                    flow_rate=float(self.ml_flow_rate_var.get()),
                    pressure=1.5,
                    fan_rpm=3000,
                    power_draw=3250,
                    hashrate=float(self.ml_hashrate_var.get()),
                    equipment_id=self.ml_equipment_id_var.get()
                )

                model = PredictiveMaintenanceModel()
                prediction = model.predict_failure(sensor_data)

                results = f"""ПРЕДСКАЗАНИЕ ОТКАЗА ОБОРУДОВАНИЯ

ОБОРУДОВАНИЕ: {prediction.equipment_id}

ДАННЫЕ ДАТЧИКОВ:
- Температура чипа: {sensor_data.chip_temp}°C
- Температура жидкости: {sensor_data.coolant_temp}°C
- Расход: {sensor_data.flow_rate} л/мин
- Хешрейт: {sensor_data.hashrate} TH/s

ПРЕДСКАЗАНИЕ:
- Вероятность отказа: {prediction.failure_probability:.1%}
- Время до отказа: {prediction.predicted_failure_hours:.0f} часов ({prediction.predicted_failure_hours/24:.1f} дней)

УРОВЕНЬ РИСКА: {prediction.risk_level.upper()}

ОСНОВНЫЕ ФАКТОРЫ РИСКА:
1. {prediction.contributing_factors[0]}
2. {prediction.contributing_factors[1]}
3. {prediction.contributing_factors[2]}

РЕКОМЕНДАЦИИ:
{prediction.recommended_action}
"""

                self.ml_results_text.delete(1.0, tk.END)
                self.ml_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось выполнить предсказание: {str(e)}")

        def optimize_cooling_gui(self):
            """Optimize cooling parameters."""
            try:
                from ml import CoolingOptimizer

                optimizer = CoolingOptimizer()
                chip_temp = float(self.ml_chip_temp_var.get())

                # Assume hydro cooling for now
                optimization = optimizer.optimize_flow_rate(
                    chip_temp=chip_temp,
                    ambient_temp=25.0,
                    tdp=3250,
                    target_temp=65.0
                )

                results = f"""ОПТИМИЗАЦИЯ СИСТЕМЫ ОХЛАЖДЕНИЯ

ТЕКУЩИЕ ПАРАМЕТРЫ:
- Температура чипа: {chip_temp}°C

РЕКОМЕНДАЦИИ:
- Расход охлаждающей жидкости: {optimization['recommended_flow_rate_lpm']:.1f} л/мин
- Базовый расход: {optimization['baseline_flow_rate_lpm']:.1f} л/мин
- Экономия энергии: {optimization['estimated_power_savings_w']:.0f} Вт
- Ожидаемая температура: {optimization['estimated_chip_temp_c']:.1f}°C

ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
- Доверительность расчёта: {optimization['confidence']:.1%}

Рекомендуется увеличить расход охлаждающей жидкости для снижения температуры чипа.
"""

                self.ml_results_text.delete(1.0, tk.END)
                self.ml_results_text.insert(tk.END, results)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось оптимизировать охлаждение: {str(e)}")

        def run_emergency_simulation(self):
            """Run emergency scenario simulation."""
            try:
                from simulation import EmergencySimulator

                sim_type = self.sim_type_var.get()
                duration = int(self.sim_duration_var.get())
                failure_time = float(self.sim_failure_time_var.get())

                simulator = EmergencySimulator()

                if sim_type == "pump_failure":
                    states, analysis = simulator.simulate_pump_failure(
                        duration_seconds=duration, failure_time=failure_time)
                    scenario_name = "Отказ насоса охлаждения"
                elif sim_type == "fan_failure":
                    states, analysis = simulator.simulate_fan_failure(
                        duration_seconds=duration, failure_time=failure_time)
                    scenario_name = "Отказ вентилятора"
                elif sim_type == "coolant_leak":
                    states, analysis = simulator.simulate_coolant_leak(
                        duration_seconds=duration, leak_start=failure_time)
                    scenario_name = "Утечка охлаждающей жидкости"

                results = f"""СИМУЛЯЦИЯ АВАРИЙНОГО СЦЕНАРИЯ

СЦЕНАРИЙ: {scenario_name}
ДЛИТЕЛЬНОСТЬ: {duration} сек
ВРЕМЯ ОТКАЗА: {failure_time} сек

РЕЗУЛЬТАТЫ АНАЛИЗА:
- Максимальная температура: {analysis['max_temp']:.1f}°C
- Конечная температура: {analysis['final_temp']:.1f}°C

ВРЕМЕННЫЕ МЕТРИКИ:
"""

                if 'time_to_warning' in analysis and analysis['time_to_warning']:
                    results += f"- До предупреждения: {analysis['time_to_warning']:.0f} сек\n"
                if 'time_to_critical' in analysis and analysis['time_to_critical']:
                    results += f"- До критической температуры: {analysis['time_to_critical']:.0f} сек\n"
                if 'time_to_shutdown' in analysis and analysis['time_to_shutdown']:
                    results += f"- До аварийного отключения: {analysis['time_to_shutdown']:.0f} сек\n"

                results += f"""
ВЫВОДЫ:
- Оборудование {'выжило' if analysis.get('equipment_survived', True) else 'повреждено'}
- Критическая ситуация наступила через {analysis.get('time_to_critical', 'N/A')} сек после отказа

ГРАФИК СОХРАНЁН: simulation_plot.png
"""

                self.sim_results_text.delete(1.0, tk.END)
                self.sim_results_text.insert(tk.END, results)

                # Create and save plot
                fig = simulator.plot_simulation(states, analysis, 'simulation_plot.png')
                print("График симуляции сохранён: simulation_plot.png")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось выполнить симуляцию: {str(e)}")

        def save_simulation_plot(self):
            """Save current simulation plot."""
            messagebox.showinfo("Информация", "График автоматически сохранён как simulation_plot.png")

        def start_api_server(self):
            """Start the mobile API server."""
            try:
                import subprocess
                import os

                # Start API server in background
                api_script = os.path.join(os.path.dirname(__file__), 'mobile_api', 'api_server.py')
                subprocess.Popen(['python', api_script], creationflags=subprocess.CREATE_NO_WINDOW)

                self.api_status_label.config(text="Сервер запущен на http://0.0.0.0:5000")
                messagebox.showinfo("Успех", "API сервер запущен! Откройте http://localhost:5000 в браузере")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось запустить API сервер: {str(e)}")

        def open_api_docs(self):
            """Open API documentation."""
            try:
                import webbrowser
                docs_path = os.path.join(os.path.dirname(__file__), 'mobile_api', 'README_MOBILE.md')
                if os.path.exists(docs_path):
                    webbrowser.open(f'file://{docs_path}')
                else:
                    messagebox.showinfo("Документация", "Документация API доступна в папке mobile_api/README_MOBILE.md")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть документацию: {str(e)}")


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
