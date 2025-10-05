"""
3D Visualization Module for ThermoMiner Pro
Thermal mapping and airflow visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import plotly.graph_objects as go
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class AsicPosition:
    """Position of ASIC in 3D space."""
    x: float  # meters
    y: float  # meters
    z: float  # meters
    tdp: float  # watts
    model: str = "ASIC"


@dataclass
class RoomConfig:
    """Room configuration for 3D visualization."""
    length: float  # meters (X)
    width: float  # meters (Y)
    height: float  # meters (Z)
    inlet_temp: float = 25.0  # °C
    outlet_temp: float = 35.0  # °C


class ThermalMapper3D:
    """3D thermal mapping and visualization engine."""
    
    def __init__(self, room: RoomConfig):
        self.room = room
        self.asics: List[AsicPosition] = []
        self.grid_resolution = 20  # points per dimension
        
    def add_asic(self, x: float, y: float, z: float, tdp: float, model: str = "ASIC"):
        """Add ASIC to the room."""
        self.asics.append(AsicPosition(x, y, z, tdp, model))
        
    def add_asic_rack(self, start_x: float, start_y: float, start_z: float,
                     count: int, tdp_per_unit: float, spacing: float = 0.5,
                     model: str = "ASIC"):
        """Add a rack of ASICs in a row."""
        for i in range(count):
            self.add_asic(
                start_x + i * spacing,
                start_y,
                start_z,
                tdp_per_unit,
                f"{model} #{i+1}"
            )
    
    def calculate_temperature_field(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Calculate 3D temperature field using simplified heat diffusion model.
        
        Returns:
            X, Y, Z, T - 3D meshgrid coordinates and temperature field
        """
        # Create 3D grid
        x = np.linspace(0, self.room.length, self.grid_resolution)
        y = np.linspace(0, self.room.width, self.grid_resolution)
        z = np.linspace(0, self.room.height, self.grid_resolution)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Initialize temperature field with inlet temperature
        T = np.full_like(X, self.room.inlet_temp)
        
        # Add heat sources from each ASIC
        for asic in self.asics:
            # Distance from each grid point to ASIC
            dx = X - asic.x
            dy = Y - asic.y
            dz = Z - asic.z
            distance = np.sqrt(dx**2 + dy**2 + dz**2)
            
            # Avoid division by zero
            distance = np.maximum(distance, 0.1)
            
            # Heat diffusion model: T increases with 1/r^2 decay
            # Scaling factor based on TDP
            heat_intensity = asic.tdp / 100.0  # Normalize by 100W
            temperature_rise = heat_intensity * 10.0 / (distance**1.5)
            
            T += temperature_rise
        
        # Apply vertical temperature gradient (hot air rises)
        vertical_gradient = (Z / self.room.height) * 5.0  # 5°C rise from floor to ceiling
        T += vertical_gradient
        
        # Clamp to reasonable values
        T = np.clip(T, self.room.inlet_temp, self.room.outlet_temp + 20)
        
        return X, Y, Z, T
    
    def create_matplotlib_figure(self) -> Figure:
        """Create matplotlib 3D figure with thermal visualization."""
        fig = Figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Calculate temperature field
        X, Y, Z, T = self.calculate_temperature_field()
        
        # Create isosurface slices at different temperatures
        temp_levels = [30, 35, 40, 45, 50]
        colors = ['blue', 'cyan', 'yellow', 'orange', 'red']
        
        # Plot horizontal slices at different heights
        for i, z_level in enumerate([0.5, 1.0, 1.5, 2.0, 2.5]):
            if z_level < self.room.height:
                z_idx = int((z_level / self.room.height) * (self.grid_resolution - 1))
                temp_slice = T[:, :, z_idx]
                
                x = np.linspace(0, self.room.length, self.grid_resolution)
                y = np.linspace(0, self.room.width, self.grid_resolution)
                X_slice, Y_slice = np.meshgrid(x, y, indexing='ij')
                
                surf = ax.plot_surface(X_slice, Y_slice, 
                                      np.full_like(X_slice, z_level),
                                      facecolors=plt.cm.hot((temp_slice - T.min()) / (T.max() - T.min())),
                                      alpha=0.3, shade=False)
        
        # Plot ASIC positions
        for asic in self.asics:
            ax.scatter([asic.x], [asic.y], [asic.z], 
                      c='black', marker='s', s=100, 
                      label=f'{asic.model}: {asic.tdp}W')
        
        # Room boundaries
        ax.set_xlim(0, self.room.length)
        ax.set_ylim(0, self.room.width)
        ax.set_zlim(0, self.room.height)
        
        ax.set_xlabel('Длина (м)')
        ax.set_ylabel('Ширина (м)')
        ax.set_zlabel('Высота (м)')
        ax.set_title('3D Тепловая Карта Помещения')
        
        # Add colorbar
        mappable = plt.cm.ScalarMappable(cmap='hot')
        mappable.set_array(T)
        mappable.set_clim(T.min(), T.max())
        fig.colorbar(mappable, ax=ax, label='Температура (°C)', shrink=0.5)
        
        return fig
    
    def create_plotly_figure(self) -> go.Figure:
        """Create interactive Plotly 3D figure with thermal visualization."""
        X, Y, Z, T = self.calculate_temperature_field()
        
        # Create volume rendering
        fig = go.Figure()
        
        # Add volume plot for temperature field
        # Sample the field for performance
        step = 2
        fig.add_trace(go.Volume(
            x=X[::step, ::step, ::step].flatten(),
            y=Y[::step, ::step, ::step].flatten(),
            z=Z[::step, ::step, ::step].flatten(),
            value=T[::step, ::step, ::step].flatten(),
            isomin=self.room.inlet_temp + 5,
            isomax=T.max(),
            opacity=0.1,
            surface_count=15,
            colorscale='Hot',
            colorbar=dict(title="Температура (°C)"),
            name='Температурное поле'
        ))
        
        # Add ASIC markers
        asic_x = [asic.x for asic in self.asics]
        asic_y = [asic.y for asic in self.asics]
        asic_z = [asic.z for asic in self.asics]
        asic_text = [f"{asic.model}<br>{asic.tdp}W" for asic in self.asics]
        
        fig.add_trace(go.Scatter3d(
            x=asic_x, y=asic_y, z=asic_z,
            mode='markers+text',
            marker=dict(size=10, color='black', symbol='square'),
            text=asic_text,
            textposition='top center',
            name='ASIC майнеры'
        ))
        
        # Add room boundaries
        room_edges = self._get_room_edges()
        for edge in room_edges:
            fig.add_trace(go.Scatter3d(
                x=edge[0], y=edge[1], z=edge[2],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False
            ))
        
        fig.update_layout(
            title='3D Тепловая Карта Майнинг-Фермы',
            scene=dict(
                xaxis_title='Длина (м)',
                yaxis_title='Ширина (м)',
                zaxis_title='Высота (м)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                )
            ),
            width=1000,
            height=800
        )
        
        return fig
    
    def _get_room_edges(self) -> List[Tuple[List, List, List]]:
        """Get room boundary edges for visualization."""
        l, w, h = self.room.length, self.room.width, self.room.height
        
        edges = [
            # Bottom rectangle
            ([0, l], [0, 0], [0, 0]),
            ([l, l], [0, w], [0, 0]),
            ([l, 0], [w, w], [0, 0]),
            ([0, 0], [w, 0], [0, 0]),
            # Top rectangle
            ([0, l], [0, 0], [h, h]),
            ([l, l], [0, w], [h, h]),
            ([l, 0], [w, w], [h, h]),
            ([0, 0], [w, 0], [h, h]),
            # Vertical edges
            ([0, 0], [0, 0], [0, h]),
            ([l, l], [0, 0], [0, h]),
            ([l, l], [w, w], [0, h]),
            ([0, 0], [w, w], [0, h]),
        ]
        
        return edges
    
    def get_hotspot_analysis(self) -> Dict:
        """Analyze hotspots in the room."""
        X, Y, Z, T = self.calculate_temperature_field()
        
        # Find maximum temperature and its location
        max_temp = T.max()
        max_idx = np.unravel_index(T.argmax(), T.shape)
        max_location = (
            X[max_idx],
            Y[max_idx],
            Z[max_idx]
        )
        
        # Find average temperature
        avg_temp = T.mean()
        
        # Count critical zones (>45°C)
        critical_volume = np.sum(T > 45) / T.size * 100  # percentage
        
        # Temperature distribution
        temp_std = T.std()
        
        return {
            'max_temp': float(max_temp),
            'max_location': max_location,
            'avg_temp': float(avg_temp),
            'temp_std': float(temp_std),
            'critical_volume_percent': float(critical_volume),
            'hotspot_warning': max_temp > 50.0
        }
    
    def generate_airflow_vectors(self, inlet_position: str = 'bottom') -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Generate airflow velocity vectors for visualization.
        
        Args:
            inlet_position: 'bottom', 'side', or 'top'
            
        Returns:
            X, Y, Z, U, V, W - position and velocity components
        """
        # Coarser grid for vectors
        res = 8
        x = np.linspace(0, self.room.length, res)
        y = np.linspace(0, self.room.width, res)
        z = np.linspace(0, self.room.height, res)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Initialize velocity field
        U = np.zeros_like(X)
        V = np.zeros_like(Y)
        W = np.zeros_like(Z)
        
        if inlet_position == 'bottom':
            # Air flows upward
            W = np.ones_like(Z) * 0.5
            # Add horizontal component near ASICs
            for asic in self.asics:
                dx = X - asic.x
                dy = Y - asic.y
                distance = np.sqrt(dx**2 + dy**2 + 0.1)
                U += dx / distance * 0.2
                V += dy / distance * 0.2
        elif inlet_position == 'side':
            # Air flows horizontally
            U = np.ones_like(X) * 0.5
            W = Z / self.room.height * 0.2  # Slight upward component
        
        return X, Y, Z, U, V, W


def create_thermal_visualization_widget(room: RoomConfig, asics: List[AsicPosition]):
    """Create a Qt widget with thermal visualization."""
    mapper = ThermalMapper3D(room)
    for asic in asics:
        mapper.add_asic(asic.x, asic.y, asic.z, asic.tdp, asic.model)
    
    fig = mapper.create_matplotlib_figure()
    return fig


if __name__ == "__main__":
    # Demo
    room = RoomConfig(length=10, width=6, height=3, inlet_temp=25, outlet_temp=35)
    mapper = ThermalMapper3D(room)
    
    # Add rack of ASICs
    mapper.add_asic_rack(2, 2, 1, count=10, tdp_per_unit=3250, spacing=0.8, model="Antminer S19")
    
    # Hotspot analysis
    analysis = mapper.get_hotspot_analysis()
    print("=== Анализ Тепловых Зон ===")
    print(f"Максимальная температура: {analysis['max_temp']:.1f}°C")
    print(f"Средняя температура: {analysis['avg_temp']:.1f}°C")
    print(f"Критический объём (>45°C): {analysis['critical_volume_percent']:.1f}%")
    print(f"⚠️ Предупреждение о перегреве: {analysis['hotspot_warning']}")
    
    # Create interactive plot
    fig = mapper.create_plotly_figure()
    fig.write_html("thermal_map_3d.html")
    print("\n✅ 3D визуализация сохранена в thermal_map_3d.html")

