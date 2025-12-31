# app.py
"""
Main application window for the PF2 Translation Tool Suite.
"""

import logging
import sys
from typing import Dict, Type

import customtkinter as ctk

from core.config_manager import ConfigManager
from .base_tab import BaseTab
from .extractor_tab import ExtractorTab
from .attacher_tab import AttacherTab


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)


class TranslationToolApp(ctk.CTk):
    """
    Main application window with tabbed interface.
    
    Features:
    - Tab-based navigation for different tools
    - Extensible architecture for adding new tabs
    - Persistent configuration
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        
        # Configure appearance
        ctk.set_appearance_mode(self.config_manager.get_appearance_mode())
        ctk.set_default_color_theme(self.config_manager.get_color_theme())
        
        # Window setup
        self.title("PF2 翻译工具组")
        width, height = self.config_manager.get_window_size()
        self.geometry(f"{width}x{height}")
        self.minsize(700, 500)
        
        # Track window resize for saving
        self.bind("<Configure>", self._on_configure)
        self._last_saved_size = (width, height)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Registered tabs
        self._tabs: Dict[str, BaseTab] = {}
        
        # Create UI
        self._create_header()
        self._create_tabview()
        self._register_default_tabs()
    
    def _create_header(self):
        """Create the header with title and theme toggle."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            header,
            text="🎲 Pathfinder 2e 翻译工具组",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Theme toggle
        theme_frame = ctk.CTkFrame(header, fg_color="transparent")
        theme_frame.grid(row=0, column=1, sticky="e")
        
        theme_label = ctk.CTkLabel(theme_frame, text="主题:")
        theme_label.grid(row=0, column=0, padx=(0, 5))
        
        current_mode = ctk.get_appearance_mode()
        theme_var = ctk.StringVar(value=current_mode)
        
        def on_theme_change(choice):
            mode = choice.lower()
            ctk.set_appearance_mode(mode)
            self.config_manager.set_appearance_mode(mode)
        
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=theme_var,
            values=["Light", "Dark", "System"],
            command=on_theme_change,
            width=100
        )
        theme_menu.grid(row=0, column=1)
    
    def _create_tabview(self):
        """Create the main tabview container."""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
    
    def _register_default_tabs(self):
        """Register the default feature tabs."""
        self.register_tab(ExtractorTab)
        self.register_tab(AttacherTab)
    
    def register_tab(self, tab_class: Type[BaseTab]):
        """
        Register and create a new feature tab.
        
        Args:
            tab_class: A subclass of BaseTab to instantiate
        """
        tab_name = tab_class.tab_name
        
        # Add tab to tabview
        self.tabview.add(tab_name)
        tab_frame = self.tabview.tab(tab_name)
        
        # Configure tab frame
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(100, weight=1)
        
        # Create tab instance
        tab_instance = tab_class(tab_frame, self.config_manager)
        self._tabs[tab_name] = tab_instance
        
        logging.info(f"已注册功能标签: {tab_name}")
    
    def get_tab(self, tab_name: str) -> BaseTab:
        """
        Get a registered tab by name.
        
        Args:
            tab_name: Name of the tab to retrieve
            
        Returns:
            The tab instance, or None if not found
        """
        return self._tabs.get(tab_name)
    
    def _on_configure(self, event):
        """Handle window configuration changes (resize)."""
        # Only respond to window resize, not internal widget events
        if event.widget != self:
            return
        
        new_size = (event.width, event.height)
        if new_size != self._last_saved_size:
            self._last_saved_size = new_size
            # Debounce: only save after resize is done
            self.after_cancel(getattr(self, '_resize_after_id', None) or 0)
            self._resize_after_id = self.after(500, self._save_window_size)
    
    def _save_window_size(self):
        """Save current window size to config."""
        width, height = self._last_saved_size
        self.config_manager.set_window_size(width, height)
