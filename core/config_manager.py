# config_manager.py
"""
Configuration management for the translation tool.
"""

import configparser
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages application configuration using INI files.
    
    Handles loading/saving of user preferences such as:
    - Recently used file paths
    - Window dimensions
    - UI preferences
    """
    
    DEFAULT_CONFIG = {
        'Paths': {
            'last_text_file': '',
            'last_excel_file': '',
            'last_output_dir': '',
        },
        'UI': {
            'window_width': '950',
            'window_height': '800',
            'appearance_mode': 'dark',
            'color_theme': 'blue',
        },
        'Attacher': {
            'format_template': '{translation} {original}',
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            config_path = os.path.join(script_dir, "config.ini")
        
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing config or create with defaults."""
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path, encoding='utf-8')
                logger.info(f"已加载配置文件: {self.config_path}")
            except Exception as e:
                logger.warning(f"读取配置文件失败: {e}，将使用默认配置")
                self._apply_defaults()
        else:
            logger.info("配置文件不存在，创建默认配置")
            self._apply_defaults()
            self.save()
    
    def _apply_defaults(self):
        """Apply default configuration values."""
        for section, values in self.DEFAULT_CONFIG.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in values.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
    
    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.debug(f"配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    # Path getters/setters
    def get_last_text_file(self) -> str:
        return self.config.get('Paths', 'last_text_file', fallback='')
    
    def set_last_text_file(self, path: str):
        self.config.set('Paths', 'last_text_file', path)
        self.save()
    
    def get_last_excel_file(self) -> str:
        return self.config.get('Paths', 'last_excel_file', fallback='')
    
    def set_last_excel_file(self, path: str):
        self.config.set('Paths', 'last_excel_file', path)
        self.save()
    
    def get_last_output_dir(self) -> str:
        return self.config.get('Paths', 'last_output_dir', fallback='')
    
    def set_last_output_dir(self, path: str):
        self.config.set('Paths', 'last_output_dir', path)
        self.save()
    
    # UI getters/setters
    def get_window_size(self) -> tuple:
        width = self.config.getint('UI', 'window_width', fallback=900)
        height = self.config.getint('UI', 'window_height', fallback=650)
        return width, height
    
    def set_window_size(self, width: int, height: int):
        self.config.set('UI', 'window_width', str(width))
        self.config.set('UI', 'window_height', str(height))
        self.save()
    
    def get_appearance_mode(self) -> str:
        return self.config.get('UI', 'appearance_mode', fallback='dark')
    
    def set_appearance_mode(self, mode: str):
        self.config.set('UI', 'appearance_mode', mode)
        self.save()
    
    def get_color_theme(self) -> str:
        return self.config.get('UI', 'color_theme', fallback='blue')
    
    # Attacher settings
    def get_format_template(self) -> str:
        return self.config.get('Attacher', 'format_template', fallback='{translation} {original}')
    
    def set_format_template(self, template: str):
        self.config.set('Attacher', 'format_template', template)
        self.save()
