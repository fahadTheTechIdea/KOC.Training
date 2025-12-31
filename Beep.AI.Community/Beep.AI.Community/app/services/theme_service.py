"""
Theme Service - Dynamic theme management
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional, List


class ThemeService:
    """Service for managing dynamic themes"""
    
    DEFAULT_THEME = {
        'name': 'Default',
        'primary_color': '#4a90e2',
        'secondary_color': '#7b68ee',
        'accent_color': '#50c878',
        'background_color': '#ffffff',
        'text_color': '#333333',
        'header_background': '#4a90e2',
        'header_text': '#ffffff',
        'card_background': '#ffffff',
        'card_border': '#e0e0e0',
        'button_primary': '#4a90e2',
        'button_primary_text': '#ffffff',
        'button_secondary': '#7b68ee',
        'success_color': '#50c878',
        'warning_color': '#ffa500',
        'error_color': '#e74c3c',
        'info_color': '#3498db',
        'border_radius': '8px',
        'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }
    
    THEMES = {
        'default': DEFAULT_THEME,
        'dark': {
            'name': 'Dark',
            'primary_color': '#6c8fff',
            'secondary_color': '#9b59b6',
            'accent_color': '#52c41a',
            'background_color': '#1a1a1a',
            'text_color': '#F5F5F5',  # Improved contrast - brighter text
            'header_background': '#2d2d2d',
            'header_text': '#ffffff',
            'card_background': '#2d2d2d',
            'card_border': '#404040',
            'button_primary': '#6c8fff',
            'button_primary_text': '#ffffff',
            'button_secondary': '#9b59b6',
            'success_color': '#52c41a',
            'warning_color': '#faad14',
            'error_color': '#ff4d4f',
            'info_color': '#1890ff',
            'border_radius': '8px',
            'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        },
        'light': {
            'name': 'Light',
            'primary_color': '#1890ff',
            'secondary_color': '#722ed1',
            'accent_color': '#52c41a',
            'background_color': '#f5f5f5',
            'text_color': '#262626',
            'header_background': '#001529',
            'header_text': '#ffffff',
            'card_background': '#ffffff',
            'card_border': '#d9d9d9',
            'button_primary': '#1890ff',
            'button_primary_text': '#ffffff',
            'button_secondary': '#722ed1',
            'success_color': '#52c41a',
            'warning_color': '#faad14',
            'error_color': '#ff4d4f',
            'info_color': '#1890ff',
            'border_radius': '6px',
            'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        },
        'blue': {
            'name': 'Ocean Blue',
            'primary_color': '#0066cc',
            'secondary_color': '#0099ff',
            'accent_color': '#00cc99',
            'background_color': '#f0f8ff',
            'text_color': '#1a1a1a',
            'header_background': '#0066cc',
            'header_text': '#ffffff',
            'card_background': '#ffffff',
            'card_border': '#cce6ff',
            'button_primary': '#0066cc',
            'button_primary_text': '#ffffff',
            'button_secondary': '#0099ff',
            'success_color': '#00cc99',
            'warning_color': '#ff9900',
            'error_color': '#cc0000',
            'info_color': '#0066cc',
            'border_radius': '10px',
            'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }
    }
    
    @staticmethod
    def get_theme(theme_name: str = 'default') -> Dict:
        """Get theme configuration"""
        theme_name = theme_name.lower()
        return ThemeService.THEMES.get(theme_name, ThemeService.DEFAULT_THEME)
    
    @staticmethod
    def get_all_themes() -> Dict[str, Dict]:
        """Get all available themes"""
        return ThemeService.THEMES
    
    @staticmethod
    def generate_css_variables(theme: Dict) -> str:
        """Generate CSS custom properties from theme"""
        css = ":root {\n"
        for key, value in theme.items():
            css_var = f"--{key.replace('_', '-')}"
            css += f"  {css_var}: {value};\n"
        css += "}\n"
        return css
    
    @staticmethod
    def generate_theme_css(theme_name: str = 'default') -> str:
        """Generate complete theme CSS"""
        theme = ThemeService.get_theme(theme_name)
        css = ThemeService.generate_css_variables(theme)
        
        css += """
body {
  background-color: var(--background-color);
  color: var(--text-color);
  font-family: var(--font-family);
}

.card {
  background-color: var(--card-background);
  border: 1px solid var(--card-border);
  border-radius: var(--border-radius);
}

.btn-primary {
  background-color: var(--button-primary);
  color: var(--button-primary-text);
  border-radius: var(--border-radius);
}

.btn-primary:hover {
  opacity: 0.9;
}

.header {
  background-color: var(--header-background);
  color: var(--header-text);
}

.text-success {
  color: var(--success-color);
}

.text-warning {
  color: var(--warning-color);
}

.text-error {
  color: var(--error-color);
}

.text-info {
  color: var(--info-color);
}
"""
        return css
    
    @staticmethod
    def save_user_theme(user_id: int, theme_name: str):
        """Save user's theme preference"""
        themes_file = Path('instance') / 'user_themes.json'
        themes_file.parent.mkdir(exist_ok=True)
        
        if themes_file.exists():
            with open(themes_file, 'r') as f:
                themes = json.load(f)
        else:
            themes = {}
        
        themes[str(user_id)] = theme_name.lower()
        
        with open(themes_file, 'w') as f:
            json.dump(themes, f, indent=2)
    
    @staticmethod
    def get_user_theme(user_id: Optional[int]) -> str:
        """Get user's preferred theme"""
        if not user_id:
            return 'default'
        
        themes_file = Path('instance') / 'user_themes.json'
        if themes_file.exists():
            try:
                with open(themes_file, 'r') as f:
                    themes = json.load(f)
                    return themes.get(str(user_id), 'default')
            except:
                return 'default'
        return 'default'
