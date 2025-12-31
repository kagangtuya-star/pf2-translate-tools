# base_tab.py
"""
Base class for all feature tabs in the translation tool.
"""

import os
import threading
from abc import ABC, abstractmethod
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk


class BaseTab(ABC):
    """
    Abstract base class for feature tabs.
    
    Provides common UI components and utilities for file selection,
    progress reporting, and logging.
    """
    
    # Subclasses must override this
    tab_name: str = "Base Tab"
    
    def __init__(self, parent: ctk.CTkFrame, config_manager=None):
        """
        Initialize the base tab.
        
        Args:
            parent: Parent CTkFrame (from CTkTabview)
            config_manager: Optional ConfigManager instance
        """
        self.parent = parent
        self.config_manager = config_manager
        self._is_processing = False
        
        # Configure grid
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(100, weight=1)  # Log area expands
        
        self.create_widgets()
    
    @abstractmethod
    def create_widgets(self):
        """Create tab-specific widgets. Must be implemented by subclasses."""
        pass
    
    # -------------------------------------------------------------------------
    # Common UI Components
    # -------------------------------------------------------------------------
    
    def create_file_selector(
        self,
        row: int,
        label_text: str,
        file_types: list,
        initial_value: str = "",
        on_change: Optional[Callable[[str], None]] = None
    ) -> tuple:
        """
        Create a labeled file selector with browse button.
        
        Args:
            row: Grid row number
            label_text: Label text for the selector
            file_types: List of (description, pattern) tuples for file dialog
            initial_value: Initial path value
            on_change: Callback when path changes
            
        Returns:
            Tuple of (frame, entry_var)
        """
        frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=20, pady=(10, 5), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        # Label
        label = ctk.CTkLabel(frame, text=label_text, width=100, anchor="w")
        label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Entry
        entry_var = ctk.StringVar(value=initial_value)
        entry = ctk.CTkEntry(frame, textvariable=entry_var, placeholder_text="点击浏览选择文件...")
        entry.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        
        # Browse button
        def browse():
            initial_dir = os.path.dirname(entry_var.get()) if entry_var.get() else None
            path = filedialog.askopenfilename(
                initialdir=initial_dir,
                filetypes=file_types,
                title=f"选择{label_text}"
            )
            if path:
                entry_var.set(path)
                if on_change:
                    on_change(path)
        
        browse_btn = ctk.CTkButton(frame, text="浏览...", width=80, command=browse)
        browse_btn.grid(row=0, column=2, sticky="e")
        
        return frame, entry_var
    
    def create_dir_selector(
        self,
        row: int,
        label_text: str,
        initial_value: str = "",
        on_change: Optional[Callable[[str], None]] = None
    ) -> tuple:
        """
        Create a labeled directory selector with browse button.
        
        Args:
            row: Grid row number
            label_text: Label text for the selector
            initial_value: Initial path value
            on_change: Callback when path changes
            
        Returns:
            Tuple of (frame, entry_var)
        """
        frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=20, pady=(10, 5), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        # Label
        label = ctk.CTkLabel(frame, text=label_text, width=100, anchor="w")
        label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Entry
        entry_var = ctk.StringVar(value=initial_value)
        entry = ctk.CTkEntry(frame, textvariable=entry_var, placeholder_text="点击浏览选择目录...")
        entry.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        
        # Browse button
        def browse():
            initial_dir = entry_var.get() if entry_var.get() else None
            path = filedialog.askdirectory(
                initialdir=initial_dir,
                title=f"选择{label_text}"
            )
            if path:
                entry_var.set(path)
                if on_change:
                    on_change(path)
        
        browse_btn = ctk.CTkButton(frame, text="浏览...", width=80, command=browse)
        browse_btn.grid(row=0, column=2, sticky="e")
        
        return frame, entry_var
    
    def create_action_button(
        self,
        row: int,
        text: str,
        command: Callable,
        fg_color: Optional[str] = None
    ) -> ctk.CTkButton:
        """
        Create a centered action button.
        
        Args:
            row: Grid row number
            text: Button text
            command: Button command
            fg_color: Optional foreground color
            
        Returns:
            The created button
        """
        btn = ctk.CTkButton(
            self.parent,
            text=text,
            command=command,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=fg_color
        )
        btn.grid(row=row, column=0, padx=20, pady=15)
        return btn
    
    def create_progress_bar(self, row: int) -> ctk.CTkProgressBar:
        """
        Create a progress bar.
        
        Args:
            row: Grid row number
            
        Returns:
            The created progress bar
        """
        progress = ctk.CTkProgressBar(self.parent)
        progress.grid(row=row, column=0, padx=20, pady=(5, 10), sticky="ew")
        progress.set(0)
        return progress
    
    def create_log_area(self, row: int) -> ctk.CTkTextbox:
        """
        Create a scrollable log/output text area.
        
        Args:
            row: Grid row number
            
        Returns:
            The created textbox
        """
        # Label
        label = ctk.CTkLabel(self.parent, text="日志输出:", anchor="w")
        label.grid(row=row, column=0, padx=20, pady=(10, 5), sticky="w")
        
        # Textbox
        log_box = ctk.CTkTextbox(
            self.parent,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled"
        )
        log_box.grid(row=row + 1, column=0, padx=20, pady=(0, 15), sticky="nsew")
        
        return log_box
    
    # -------------------------------------------------------------------------
    # Logging Utilities
    # -------------------------------------------------------------------------
    
    def log_message(self, log_box: ctk.CTkTextbox, message: str):
        """
        Append a message to the log box.
        
        Args:
            log_box: The textbox to append to
            message: Message to append
        """
        log_box.configure(state="normal")
        log_box.insert("end", message + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")
    
    def clear_log(self, log_box: ctk.CTkTextbox):
        """
        Clear all content from the log box.
        
        Args:
            log_box: The textbox to clear
        """
        log_box.configure(state="normal")
        log_box.delete("1.0", "end")
        log_box.configure(state="disabled")
    
    # -------------------------------------------------------------------------
    # Threading Utilities
    # -------------------------------------------------------------------------
    
    def run_in_thread(self, target: Callable, *args, **kwargs):
        """
        Run a function in a background thread.
        
        Args:
            target: Function to run
            *args, **kwargs: Arguments to pass to the function
        """
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        thread.start()
    
    def set_processing(self, is_processing: bool, button: Optional[ctk.CTkButton] = None):
        """
        Set the processing state and optionally disable/enable a button.
        
        Args:
            is_processing: Whether processing is in progress
            button: Optional button to disable/enable
        """
        self._is_processing = is_processing
        if button:
            button.configure(state="disabled" if is_processing else "normal")
