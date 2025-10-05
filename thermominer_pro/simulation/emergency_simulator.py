"""
Emergency Scenario Simulator for ThermoMiner Pro
Simulates equipment failures and thermal runaway scenarios
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


@dataclass
class EquipmentState:
    """State of mining equipment at a point in time."""
    time_seconds: float
    chip_temp: float  # °C
    coolant_temp: float  # °C
    ambient_temp: float  # °C
    flow_rate: float  # L/min
    pressure: float  # bar
    fan_rpm: int
    power_draw: float  # W
    hashrate: float  # TH/s
    is_operational: bool


@dataclass
class EmergencyScenario:
    """Definition of an emergency scenario."""
    name: str
    description: str
    failure_time_seconds: float
    failure_type: str  # 'pump', 'fan', 'power', 'coolant_leak'
    severity: str  # 'minor', 'major', 'critical'


class EmergencySimulator:
    """Simulates emergency scenarios and thermal dynamics."""
    
    def __init__(self, initial_chip_temp: float = 65.0,
                 initial_coolant_temp: float = 30.0,
                 ambient_temp: float = 25.0,
                 tdp: float = 3250.0,
                 thermal_mass: float = 5.0):  # kg (approximate ASIC mass)
        """
        Initialize simulator.
        
        Args:
            initial_chip_temp: Starting chip temperature (°C)
            initial_coolant_temp: Starting coolant temperature (°C)
            ambient_temp: Ambient air temperature (°C)
            tdp: Thermal design power (W)
            thermal_mass: Effective thermal mass of ASIC (kg)
        """
        self.initial_chip_temp = initial_chip_temp
        self.initial_coolant_temp = initial_coolant_temp
        self.ambient_temp = ambient_temp
        self.tdp = tdp
        self.thermal_mass = thermal_mass
        
        # Thermal properties (approximate for electronics)
        self.specific_heat = 880  # J/kg·K (aluminum/copper mix)
        self.thermal_capacity = thermal_mass * self.specific_heat
        
        # Critical temperatures
        self.temp_warning = 80.0  # °C
        self.temp_critical = 90.0  # °C
        self.temp_shutdown = 100.0  # °C
        self.temp_damage = 110.0  # °C
    
    def simulate_normal_operation(self, duration_seconds: float = 3600,
                                  dt: float = 1.0) -> List[EquipmentState]:
        """Simulate normal operation."""
        states = []
        time = 0.0
        chip_temp = self.initial_chip_temp
        coolant_temp = self.initial_coolant_temp
        
        while time <= duration_seconds:
            # Normal cooling: heat transfer to coolant
            # Q = h * A * (T_chip - T_coolant)
            # Simplified: dT/dt = (Q_in - Q_out) / (m * c)
            
            heat_in = self.tdp  # Watts
            heat_transfer_coeff = 50.0  # W/K (effective)
            heat_out = heat_transfer_coeff * (chip_temp - coolant_temp)
            
            # Temperature change
            dT = (heat_in - heat_out) * dt / self.thermal_capacity
            chip_temp += dT
            
            # Coolant temperature rises slightly
            coolant_temp = self.initial_coolant_temp + (time / 3600) * 0.5
            
            state = EquipmentState(
                time_seconds=time,
                chip_temp=chip_temp,
                coolant_temp=coolant_temp,
                ambient_temp=self.ambient_temp,
                flow_rate=10.0,
                pressure=1.5,
                fan_rpm=3000,
                power_draw=self.tdp,
                hashrate=110.0,
                is_operational=True
            )
            states.append(state)
            
            time += dt
        
        return states
    
    def simulate_pump_failure(self, duration_seconds: float = 600,
                             failure_time: float = 60.0,
                             dt: float = 1.0) -> Tuple[List[EquipmentState], Dict]:
        """Simulate coolant pump failure.
        
        Returns:
            (states, analysis)
        """
        states = []
        time = 0.0
        chip_temp = self.initial_chip_temp
        coolant_temp = self.initial_coolant_temp
        flow_rate = 10.0
        
        # Tracking
        warning_time = None
        critical_time = None
        shutdown_time = None
        damage_time = None
        
        while time <= duration_seconds:
            # Pump fails at failure_time
            if time >= failure_time:
                # Flow rate drops exponentially
                time_since_failure = time - failure_time
                flow_rate = 10.0 * np.exp(-time_since_failure / 10.0)
            
            # Heat transfer depends on flow rate
            if flow_rate > 0.5:
                heat_transfer_coeff = 50.0 * (flow_rate / 10.0)
            else:
                # Natural convection only
                heat_transfer_coeff = 5.0
            
            heat_in = self.tdp
            heat_out = heat_transfer_coeff * (chip_temp - self.ambient_temp)
            
            dT = (heat_in - heat_out) * dt / self.thermal_capacity
            chip_temp += dT
            
            # Coolant stagnates and heats up
            if time >= failure_time:
                coolant_temp += (chip_temp - coolant_temp) * 0.01 * dt
            
            # Check temperature thresholds
            if chip_temp >= self.temp_warning and warning_time is None:
                warning_time = time
            if chip_temp >= self.temp_critical and critical_time is None:
                critical_time = time
            if chip_temp >= self.temp_shutdown and shutdown_time is None:
                shutdown_time = time
                # ASIC shuts down to protect itself
                heat_in = 0
            if chip_temp >= self.temp_damage and damage_time is None:
                damage_time = time
            
            is_operational = chip_temp < self.temp_shutdown
            
            state = EquipmentState(
                time_seconds=time,
                chip_temp=chip_temp,
                coolant_temp=coolant_temp,
                ambient_temp=self.ambient_temp,
                flow_rate=flow_rate,
                pressure=1.5 * (flow_rate / 10.0) if flow_rate > 0 else 0,
                fan_rpm=3000,
                power_draw=heat_in,
                hashrate=110.0 * (flow_rate / 10.0) if is_operational else 0,
                is_operational=is_operational
            )
            states.append(state)
            
            time += dt
        
        analysis = {
            'scenario': 'Отказ насоса охлаждения',
            'failure_time': failure_time,
            'time_to_warning': warning_time - failure_time if warning_time else None,
            'time_to_critical': critical_time - failure_time if critical_time else None,
            'time_to_shutdown': shutdown_time - failure_time if shutdown_time else None,
            'time_to_damage': damage_time - failure_time if damage_time else None,
            'max_temp': max(s.chip_temp for s in states),
            'final_temp': states[-1].chip_temp,
            'equipment_survived': damage_time is None
        }
        
        return states, analysis
    
    def simulate_fan_failure(self, duration_seconds: float = 1800,
                            failure_time: float = 60.0,
                            dt: float = 1.0) -> Tuple[List[EquipmentState], Dict]:
        """Simulate ventilation fan failure (air cooling)."""
        states = []
        time = 0.0
        chip_temp = self.initial_chip_temp
        ambient_temp = self.ambient_temp
        fan_rpm = 3000
        
        warning_time = None
        critical_time = None
        shutdown_time = None
        
        while time <= duration_seconds:
            # Fan fails at failure_time
            if time >= failure_time:
                time_since_failure = time - failure_time
                fan_rpm = int(3000 * np.exp(-time_since_failure / 30.0))
            
            # Heat transfer depends on airflow (fan RPM)
            if fan_rpm > 500:
                heat_transfer_coeff = 30.0 * (fan_rpm / 3000.0)
            else:
                # Natural convection only
                heat_transfer_coeff = 3.0
            
            # Ambient temperature rises due to poor ventilation
            if time >= failure_time:
                ambient_temp = self.ambient_temp + (time - failure_time) / 60.0
            
            heat_in = self.tdp
            heat_out = heat_transfer_coeff * (chip_temp - ambient_temp)
            
            dT = (heat_in - heat_out) * dt / self.thermal_capacity
            chip_temp += dT
            
            if chip_temp >= self.temp_warning and warning_time is None:
                warning_time = time
            if chip_temp >= self.temp_critical and critical_time is None:
                critical_time = time
            if chip_temp >= self.temp_shutdown and shutdown_time is None:
                shutdown_time = time
                heat_in = 0
            
            is_operational = chip_temp < self.temp_shutdown
            
            state = EquipmentState(
                time_seconds=time,
                chip_temp=chip_temp,
                coolant_temp=0,  # N/A for air cooling
                ambient_temp=ambient_temp,
                flow_rate=0,  # N/A
                pressure=0,  # N/A
                fan_rpm=fan_rpm,
                power_draw=heat_in,
                hashrate=110.0 if is_operational else 0,
                is_operational=is_operational
            )
            states.append(state)
            
            time += dt
        
        analysis = {
            'scenario': 'Отказ вентилятора',
            'failure_time': failure_time,
            'time_to_warning': warning_time - failure_time if warning_time else None,
            'time_to_critical': critical_time - failure_time if critical_time else None,
            'time_to_shutdown': shutdown_time - failure_time if shutdown_time else None,
            'max_temp': max(s.chip_temp for s in states),
            'final_temp': states[-1].chip_temp,
            'equipment_survived': shutdown_time is not None
        }
        
        return states, analysis
    
    def simulate_coolant_leak(self, duration_seconds: float = 1200,
                             leak_start: float = 60.0,
                             leak_rate: float = 0.1,  # L/min loss
                             dt: float = 1.0) -> Tuple[List[EquipmentState], Dict]:
        """Simulate coolant leak."""
        states = []
        time = 0.0
        chip_temp = self.initial_chip_temp
        coolant_temp = self.initial_coolant_temp
        flow_rate = 10.0
        total_coolant = 20.0  # liters
        
        warning_time = None
        critical_time = None
        
        while time <= duration_seconds and total_coolant > 0:
            # Coolant leaks
            if time >= leak_start:
                total_coolant -= leak_rate * (dt / 60.0)
                total_coolant = max(0, total_coolant)
                
                # Flow rate decreases as coolant is lost
                flow_rate = 10.0 * (total_coolant / 20.0)
            
            # Heat transfer
            if flow_rate > 0.5:
                heat_transfer_coeff = 50.0 * (flow_rate / 10.0)
            else:
                heat_transfer_coeff = 5.0
            
            heat_in = self.tdp
            heat_out = heat_transfer_coeff * (chip_temp - self.ambient_temp)
            
            dT = (heat_in - heat_out) * dt / self.thermal_capacity
            chip_temp += dT
            
            if chip_temp >= self.temp_warning and warning_time is None:
                warning_time = time
            if chip_temp >= self.temp_critical and critical_time is None:
                critical_time = time
            
            state = EquipmentState(
                time_seconds=time,
                chip_temp=chip_temp,
                coolant_temp=coolant_temp,
                ambient_temp=self.ambient_temp,
                flow_rate=flow_rate,
                pressure=1.5 * (total_coolant / 20.0),
                fan_rpm=3000,
                power_draw=self.tdp,
                hashrate=110.0 if chip_temp < self.temp_shutdown else 0,
                is_operational=chip_temp < self.temp_shutdown
            )
            states.append(state)
            
            time += dt
        
        analysis = {
            'scenario': 'Утечка охлаждающей жидкости',
            'leak_start': leak_start,
            'leak_rate_lpm': leak_rate,
            'time_to_warning': warning_time - leak_start if warning_time else None,
            'time_to_critical': critical_time - leak_start if critical_time else None,
            'time_until_empty': (20.0 / leak_rate) * 60,  # seconds
            'max_temp': max(s.chip_temp for s in states),
            'final_coolant_level': total_coolant
        }
        
        return states, analysis
    
    def plot_simulation(self, states: List[EquipmentState], analysis: Dict,
                       save_path: str = None) -> plt.Figure:
        """Plot simulation results."""
        times = [s.time_seconds / 60 for s in states]  # Convert to minutes
        chip_temps = [s.chip_temp for s in states]
        flow_rates = [s.flow_rate for s in states]
        fan_rpms = [s.fan_rpm for s in states]
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # Temperature plot
        ax1 = axes[0]
        ax1.plot(times, chip_temps, 'r-', linewidth=2, label='Температура чипа')
        ax1.axhline(self.temp_warning, color='orange', linestyle='--', label='Предупреждение')
        ax1.axhline(self.temp_critical, color='red', linestyle='--', label='Критическая')
        ax1.axhline(self.temp_shutdown, color='darkred', linestyle='--', label='Отключение')
        ax1.set_ylabel('Температура (°C)', fontsize=12)
        ax1.set_title(f'Сценарий: {analysis["scenario"]}', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Flow rate plot
        ax2 = axes[1]
        ax2.plot(times, flow_rates, 'b-', linewidth=2, label='Расход охлаждающей жидкости')
        ax2.set_ylabel('Расход (л/мин)', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Fan RPM plot
        ax3 = axes[2]
        ax3.plot(times, fan_rpms, 'g-', linewidth=2, label='Обороты вентилятора')
        ax3.set_xlabel('Время (минуты)', fontsize=12)
        ax3.set_ylabel('RPM', fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Add failure marker
        if 'failure_time' in analysis:
            for ax in axes:
                ax.axvline(analysis['failure_time'] / 60, color='black', 
                          linestyle=':', linewidth=2, label='Момент отказа')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig


def format_analysis_report(analysis: Dict) -> str:
    """Format simulation analysis as readable report."""
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║          АНАЛИЗ АВАРИЙНОГО СЦЕНАРИЯ                          ║
╚══════════════════════════════════════════════════════════════╝

🚨 СЦЕНАРИЙ: {analysis['scenario']}

⏱️  ВРЕМЕННЫЕ МЕТРИКИ:
"""
    
    if 'failure_time' in analysis:
        report += f"   • Время отказа: {analysis['failure_time']:.0f} сек ({analysis['failure_time']/60:.1f} мин)\n"
    
    if analysis.get('time_to_warning'):
        report += f"   • До предупреждения: {analysis['time_to_warning']:.0f} сек ({analysis['time_to_warning']/60:.1f} мин)\n"
    
    if analysis.get('time_to_critical'):
        report += f"   • До критической температуры: {analysis['time_to_critical']:.0f} сек ({analysis['time_to_critical']/60:.1f} мин)\n"
    
    if analysis.get('time_to_shutdown'):
        report += f"   • До аварийного отключения: {analysis['time_to_shutdown']:.0f} сек ({analysis['time_to_shutdown']/60:.1f} мин)\n"
    
    report += f"""
🌡️  ТЕМПЕРАТУРНЫЕ ПОКАЗАТЕЛИ:
   • Максимальная температура: {analysis['max_temp']:.1f}°C
   • Конечная температура: {analysis['final_temp']:.1f}°C

"""
    
    if 'equipment_survived' in analysis:
        if analysis['equipment_survived']:
            report += "✅ ОБОРУДОВАНИЕ: Выжило (аварийное отключение сработало)\n"
        else:
            report += "❌ ОБОРУДОВАНИЕ: Повреждено (превышена температура повреждения)\n"
    
    report += f"""
💡 РЕКОМЕНДАЦИИ:
   • Установите температурные датчики с алертами
   • Время реакции оператора: {analysis.get('time_to_critical', 300)/60:.1f} минут
   • Рекомендуется резервирование критических компонентов
   • Автоматическое отключение при {90}°C
"""
    
    return report


if __name__ == "__main__":
    print("=== ThermoMiner Pro: Emergency Scenario Simulator ===\n")
    
    simulator = EmergencySimulator(
        initial_chip_temp=65.0,
        initial_coolant_temp=30.0,
        ambient_temp=25.0,
        tdp=3250.0
    )
    
    # Scenario 1: Pump failure
    print("1. СИМУЛЯЦИЯ ОТКАЗА НАСОСА\n")
    states, analysis = simulator.simulate_pump_failure(duration_seconds=600, failure_time=60)
    print(format_analysis_report(analysis))
    
    fig = simulator.plot_simulation(states, analysis, 'pump_failure_simulation.png')
    print("📊 График сохранён: pump_failure_simulation.png\n")
    
    print("="*70 + "\n")
    
    # Scenario 2: Fan failure
    print("2. СИМУЛЯЦИЯ ОТКАЗА ВЕНТИЛЯТОРА\n")
    states, analysis = simulator.simulate_fan_failure(duration_seconds=1800, failure_time=60)
    print(format_analysis_report(analysis))
    
    fig = simulator.plot_simulation(states, analysis, 'fan_failure_simulation.png')
    print("📊 График сохранён: fan_failure_simulation.png\n")
    
    print("="*70 + "\n")
    
    # Scenario 3: Coolant leak
    print("3. СИМУЛЯЦИЯ УТЕЧКИ ОХЛАЖДАЮЩЕЙ ЖИДКОСТИ\n")
    states, analysis = simulator.simulate_coolant_leak(duration_seconds=1200, leak_start=60, leak_rate=0.2)
    print(format_analysis_report(analysis))
    
    fig = simulator.plot_simulation(states, analysis, 'coolant_leak_simulation.png')
    print("📊 График сохранён: coolant_leak_simulation.png")

