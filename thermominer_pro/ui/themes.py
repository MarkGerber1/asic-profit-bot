"""
Theme Manager for ThermoMiner Pro
Light and Dark theme support with persistence
"""

import json
from pathlib import Path
from typing import Dict


class ThemeManager:
    """Manages application themes and user preferences."""
    
    LIGHT_THEME = {
        'name': 'light',
        'background': '#FFFFFF',
        'foreground': '#000000',
        'secondary_bg': '#F0F0F0',
        'secondary_fg': '#333333',
        'accent': '#0078D7',
        'accent_hover': '#005A9E',
        'border': '#CCCCCC',
        'success': '#28A745',
        'warning': '#FFC107',
        'error': '#DC3545',
        'info': '#17A2B8',
        
        # Text colors
        'text_primary': '#000000',
        'text_secondary': '#666666',
        'text_disabled': '#999999',
        
        # Widget colors
        'button_bg': '#E1E1E1',
        'button_fg': '#000000',
        'button_hover': '#D1D1D1',
        'input_bg': '#FFFFFF',
        'input_fg': '#000000',
        'input_border': '#CCCCCC',
        
        # Chart colors
        'chart_bg': '#FFFFFF',
        'chart_grid': '#E0E0E0',
        'chart_text': '#000000'
    }
    
    DARK_THEME = {
        'name': 'dark',
        'background': '#1E1E1E',
        'foreground': '#FFFFFF',
        'secondary_bg': '#2D2D2D',
        'secondary_fg': '#CCCCCC',
        'accent': '#0E639C',
        'accent_hover': '#1177BB',
        'border': '#3F3F3F',
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336',
        'info': '#2196F3',
        
        # Text colors
        'text_primary': '#FFFFFF',
        'text_secondary': '#AAAAAA',
        'text_disabled': '#666666',
        
        # Widget colors
        'button_bg': '#3F3F3F',
        'button_fg': '#FFFFFF',
        'button_hover': '#4F4F4F',
        'input_bg': '#2D2D2D',
        'input_fg': '#FFFFFF',
        'input_border': '#555555',
        
        # Chart colors
        'chart_bg': '#1E1E1E',
        'chart_grid': '#3F3F3F',
        'chart_text': '#FFFFFF'
    }
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path.home() / '.thermominer_pro' / 'theme_config.json'
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.current_theme = self.load_preference()
    
    def load_preference(self) -> Dict:
        """Load saved theme preference."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme_name = config.get('theme', 'light')
                    return self.DARK_THEME if theme_name == 'dark' else self.LIGHT_THEME
            except Exception as e:
                print(f"Ошибка загрузки темы: {e}")
        
        return self.LIGHT_THEME
    
    def save_preference(self, theme_name: str):
        """Save theme preference to disk."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({'theme': theme_name}, f)
        except Exception as e:
            print(f"Ошибка сохранения темы: {e}")
    
    def get_theme(self) -> Dict:
        """Get current theme."""
        return self.current_theme
    
    def set_theme(self, theme_name: str) -> Dict:
        """Set theme by name ('light' or 'dark')."""
        if theme_name == 'dark':
            self.current_theme = self.DARK_THEME
        else:
            self.current_theme = self.LIGHT_THEME
        
        self.save_preference(theme_name)
        return self.current_theme
    
    def toggle_theme(self) -> Dict:
        """Toggle between light and dark theme."""
        current_name = self.current_theme['name']
        new_name = 'dark' if current_name == 'light' else 'light'
        return self.set_theme(new_name)
    
    def get_tkinter_style(self) -> Dict:
        """Get Tkinter-compatible style dictionary."""
        theme = self.current_theme
        return {
            'bg': theme['background'],
            'fg': theme['foreground'],
            'activebackground': theme['accent'],
            'activeforeground': theme['foreground'],
            'selectbackground': theme['accent'],
            'selectforeground': theme['foreground'],
            'insertbackground': theme['foreground'],
            'highlightbackground': theme['border'],
            'highlightcolor': theme['accent'],
            'disabledforeground': theme['text_disabled']
        }
    
    def get_matplotlib_style(self) -> Dict:
        """Get matplotlib-compatible style dictionary."""
        theme = self.current_theme
        return {
            'figure.facecolor': theme['chart_bg'],
            'axes.facecolor': theme['chart_bg'],
            'axes.edgecolor': theme['chart_grid'],
            'axes.labelcolor': theme['chart_text'],
            'text.color': theme['chart_text'],
            'xtick.color': theme['chart_text'],
            'ytick.color': theme['chart_text'],
            'grid.color': theme['chart_grid'],
            'legend.facecolor': theme['secondary_bg'],
            'legend.edgecolor': theme['border']
        }
    
    def get_plotly_template(self) -> str:
        """Get Plotly template name."""
        return 'plotly_dark' if self.current_theme['name'] == 'dark' else 'plotly'
    
    def apply_to_tkinter_widget(self, widget, widget_type='default'):
        """Apply theme to a Tkinter widget."""
        theme = self.current_theme
        
        try:
            if widget_type == 'text':
                widget.config(
                    bg=theme['input_bg'],
                    fg=theme['input_fg'],
                    insertbackground=theme['foreground'],
                    selectbackground=theme['accent'],
                    selectforeground=theme['foreground']
                )
            elif widget_type == 'button':
                widget.config(
                    bg=theme['button_bg'],
                    fg=theme['button_fg'],
                    activebackground=theme['button_hover'],
                    activeforeground=theme['button_fg']
                )
            elif widget_type == 'entry':
                widget.config(
                    bg=theme['input_bg'],
                    fg=theme['input_fg'],
                    insertbackground=theme['foreground'],
                    selectbackground=theme['accent']
                )
            elif widget_type == 'label':
                widget.config(
                    bg=theme['background'],
                    fg=theme['text_primary']
                )
            elif widget_type == 'frame':
                widget.config(
                    bg=theme['background']
                )
            else:
                # Default styling
                widget.config(
                    bg=theme['background'],
                    fg=theme['foreground']
                )
        except Exception as e:
            print(f"Не удалось применить тему к виджету: {e}")
    
    def get_ttk_style_config(self) -> Dict:
        """Get ttk Style configuration."""
        theme = self.current_theme
        
        return {
            'TFrame': {
                'configure': {'background': theme['background']}
            },
            'TLabel': {
                'configure': {
                    'background': theme['background'],
                    'foreground': theme['text_primary']
                }
            },
            'TButton': {
                'configure': {
                    'background': theme['button_bg'],
                    'foreground': theme['button_fg'],
                    'bordercolor': theme['border'],
                    'lightcolor': theme['button_hover'],
                    'darkcolor': theme['button_bg']
                },
                'map': {
                    'background': [('active', theme['button_hover'])],
                    'foreground': [('active', theme['button_fg'])]
                }
            },
            'TEntry': {
                'configure': {
                    'fieldbackground': theme['input_bg'],
                    'foreground': theme['input_fg'],
                    'bordercolor': theme['input_border']
                }
            },
            'TCombobox': {
                'configure': {
                    'fieldbackground': theme['input_bg'],
                    'background': theme['button_bg'],
                    'foreground': theme['input_fg'],
                    'arrowcolor': theme['text_primary']
                }
            },
            'TNotebook': {
                'configure': {
                    'background': theme['background'],
                    'bordercolor': theme['border']
                }
            },
            'TNotebook.Tab': {
                'configure': {
                    'background': theme['secondary_bg'],
                    'foreground': theme['text_primary']
                },
                'map': {
                    'background': [('selected', theme['accent'])],
                    'foreground': [('selected', theme['foreground'])]
                }
            },
            'TLabelframe': {
                'configure': {
                    'background': theme['background'],
                    'foreground': theme['text_primary'],
                    'bordercolor': theme['border']
                }
            },
            'TLabelframe.Label': {
                'configure': {
                    'background': theme['background'],
                    'foreground': theme['text_primary']
                }
            }
        }


def apply_theme_to_matplotlib(theme_manager: ThemeManager):
    """Apply theme to matplotlib globally."""
    import matplotlib.pyplot as plt
    style_dict = theme_manager.get_matplotlib_style()
    plt.rcParams.update(style_dict)


def create_theme_toggle_button(parent, theme_manager: ThemeManager, on_toggle_callback=None):
    """Create a theme toggle button for Tkinter.
    
    Args:
        parent: Parent Tkinter widget
        theme_manager: ThemeManager instance
        on_toggle_callback: Function to call after theme toggle (receives new theme dict)
    
    Returns:
        Button widget
    """
    import tkinter as tk
    from tkinter import ttk
    
    def toggle():
        new_theme = theme_manager.toggle_theme()
        btn.config(text='🌙 Тёмная' if new_theme['name'] == 'light' else '☀️ Светлая')
        if on_toggle_callback:
            on_toggle_callback(new_theme)
    
    current_theme = theme_manager.get_theme()
    btn = ttk.Button(
        parent,
        text='🌙 Тёмная' if current_theme['name'] == 'light' else '☀️ Светлая',
        command=toggle
    )
    
    return btn


if __name__ == "__main__":
    # Demo
    manager = ThemeManager()
    
    print("Текущая тема:", manager.get_theme()['name'])
    print("\nЦвета темы:")
    for key, value in manager.get_theme().items():
        if key != 'name':
            print(f"  {key}: {value}")
    
    print("\n" + "="*50)
    print("Переключение темы...")
    manager.toggle_theme()
    
    print("Новая тема:", manager.get_theme()['name'])
    print("\nЦвета темы:")
    for key, value in manager.get_theme().items():
        if key != 'name':
            print(f"  {key}: {value}")

