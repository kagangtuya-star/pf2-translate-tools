# attacher_tab.py
"""
Term Attacher tab - attaches translations to original terms in text.
"""

import os
from typing import Optional

import customtkinter as ctk

from core.translation_engine import TranslationEngine
from core.file_utils import load_text_file, save_text_file
from .base_tab import BaseTab


# Predefined format templates
FORMAT_TEMPLATES = [
    ("{translation} {original}", "译名 原名 (如: 火球术 fire ball)"),
    ("{original}({translation})", "原名(译名) (如: fire ball(火球术))"),
    ("{original} ({translation})", "原名 (译名) (如: fire ball (火球术))"),
    ("{translation}({original})", "译名(原名) (如: 火球术(fire ball))"),
]


class AttacherTab(BaseTab):
    """
    Tab for attaching translations to terms in text.
    
    Features:
    1. File mode: Process entire files with translation attachment
    2. Live preview mode: Type text and see instant translation attachment
    """
    
    tab_name = "译名附加"
    
    def __init__(self, parent: ctk.CTkFrame, config_manager=None):
        self.text_path_var: Optional[ctk.StringVar] = None
        self.excel_path_var: Optional[ctk.StringVar] = None
        self.output_path_var: Optional[ctk.StringVar] = None
        self.format_var: Optional[ctk.StringVar] = None
        self.attach_btn: Optional[ctk.CTkButton] = None
        self.progress: Optional[ctk.CTkProgressBar] = None
        self.log_box: Optional[ctk.CTkTextbox] = None
        self.input_preview: Optional[ctk.CTkTextbox] = None
        self.output_preview: Optional[ctk.CTkTextbox] = None
        self.engine = TranslationEngine()
        self._engine_ready = False
        self._preview_update_id = None  # For debouncing
        
        super().__init__(parent, config_manager)
    
    def create_widgets(self):
        """Create the attacher tab widgets with optimized layout."""
        # Configure parent grid
        self.parent.grid_columnconfigure(0, weight=1)
        
        row = 0
        
        # === Header Section ===
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=row, column=0, padx=20, pady=(15, 10), sticky="ew")
        
        title = ctk.CTkLabel(
            header_frame,
            text="🔗 译名附加工具",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(anchor="w")
        
        desc = ctk.CTkLabel(
            header_frame,
            text="将译名附加到原文术语上 | 支持实时预览和批量文件处理",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        desc.pack(anchor="w", pady=(2, 0))
        row += 1
        
        # === Settings Section (Excel + Format in one row) ===
        settings_frame = ctk.CTkFrame(self.parent, corner_radius=10)
        settings_frame.grid(row=row, column=0, padx=20, pady=(0, 10), sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Excel selector
        excel_label = ctk.CTkLabel(settings_frame, text="📚 译名表:", width=80, anchor="w")
        excel_label.grid(row=0, column=0, padx=(15, 5), pady=(12, 6), sticky="w")
        
        initial_excel = ""
        if self.config_manager:
            initial_excel = self.config_manager.get_last_excel_file()
        
        self.excel_path_var = ctk.StringVar(value=initial_excel)
        excel_entry = ctk.CTkEntry(
            settings_frame, 
            textvariable=self.excel_path_var,
            placeholder_text="选择 Excel 译名表文件..."
        )
        excel_entry.grid(row=0, column=1, padx=5, pady=(12, 6), sticky="ew")
        
        excel_btn = ctk.CTkButton(
            settings_frame, text="浏览", width=60,
            command=self._browse_excel
        )
        excel_btn.grid(row=0, column=2, padx=(5, 15), pady=(12, 6))
        
        # Format selector
        format_label = ctk.CTkLabel(settings_frame, text="📝 格式:", width=80, anchor="w")
        format_label.grid(row=1, column=0, padx=(15, 5), pady=(6, 12), sticky="w")
        
        saved_template = "{translation} {original}"
        if self.config_manager:
            saved_template = self.config_manager.get_format_template()
        
        display_values = [desc for _, desc in FORMAT_TEMPLATES]
        initial_index = 0
        for i, (template, _) in enumerate(FORMAT_TEMPLATES):
            if template == saved_template:
                initial_index = i
                break
        
        self.format_var = ctk.StringVar(value=display_values[initial_index])
        format_dropdown = ctk.CTkOptionMenu(
            settings_frame,
            variable=self.format_var,
            values=display_values,
            command=self._on_format_change,
            width=400
        )
        format_dropdown.grid(row=1, column=1, columnspan=2, padx=(5, 15), pady=(6, 12), sticky="w")
        row += 1
        
        # === Live Preview Section ===
        preview_header = ctk.CTkLabel(
            self.parent,
            text="⚡ 实时预览",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        preview_header.grid(row=row, column=0, padx=20, pady=(10, 5), sticky="w")
        row += 1
        
        # Preview container
        preview_frame = ctk.CTkFrame(self.parent, corner_radius=10, height=180)
        preview_frame.grid(row=row, column=0, padx=20, pady=(0, 10), sticky="ew")
        preview_frame.grid_propagate(False)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(1, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)
        
        # Input side
        input_label = ctk.CTkLabel(preview_frame, text="📝 输入原文", anchor="w")
        input_label.grid(row=0, column=0, padx=(15, 5), pady=(10, 3), sticky="w")
        
        self.input_preview = ctk.CTkTextbox(
            preview_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        self.input_preview.grid(row=1, column=0, padx=(15, 5), pady=(0, 10), sticky="nsew")
        self.input_preview.bind("<KeyRelease>", lambda e: self._schedule_preview_update())
        
        # Output side
        output_label = ctk.CTkLabel(preview_frame, text="✨ 附加结果", anchor="w")
        output_label.grid(row=0, column=1, padx=(5, 15), pady=(10, 3), sticky="w")
        
        self.output_preview = ctk.CTkTextbox(
            preview_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled"
        )
        self.output_preview.grid(row=1, column=1, padx=(5, 15), pady=(0, 10), sticky="nsew")
        row += 1
        
        # === File Processing Section ===
        file_header = ctk.CTkLabel(
            self.parent,
            text="📁 批量文件处理",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        file_header.grid(row=row, column=0, padx=20, pady=(15, 5), sticky="w")
        row += 1
        
        # File processing container
        file_frame = ctk.CTkFrame(self.parent, corner_radius=10)
        file_frame.grid(row=row, column=0, padx=20, pady=(0, 10), sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)
        
        # Text file selector
        text_label = ctk.CTkLabel(file_frame, text="输入文件:", width=80, anchor="w")
        text_label.grid(row=0, column=0, padx=(15, 5), pady=(12, 6), sticky="w")
        
        initial_text = ""
        if self.config_manager:
            initial_text = self.config_manager.get_last_text_file()
        
        self.text_path_var = ctk.StringVar(value=initial_text)
        text_entry = ctk.CTkEntry(
            file_frame,
            textvariable=self.text_path_var,
            placeholder_text="选择要处理的文本文件..."
        )
        text_entry.grid(row=0, column=1, padx=5, pady=(12, 6), sticky="ew")
        
        text_btn = ctk.CTkButton(
            file_frame, text="浏览", width=60,
            command=self._browse_text_file
        )
        text_btn.grid(row=0, column=2, padx=(5, 15), pady=(12, 6))
        
        # Output file selector
        output_label = ctk.CTkLabel(file_frame, text="输出文件:", width=80, anchor="w")
        output_label.grid(row=1, column=0, padx=(15, 5), pady=(6, 12), sticky="w")
        
        self.output_path_var = ctk.StringVar(value="")
        output_entry = ctk.CTkEntry(
            file_frame,
            textvariable=self.output_path_var,
            placeholder_text="输出路径 (留空自动生成)"
        )
        output_entry.grid(row=1, column=1, padx=5, pady=(6, 12), sticky="ew")
        
        output_btn = ctk.CTkButton(
            file_frame, text="浏览", width=60,
            command=self._browse_output_file
        )
        output_btn.grid(row=1, column=2, padx=(5, 15), pady=(6, 12))
        row += 1
        
        # Action button and progress
        action_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        action_frame.grid(row=row, column=0, padx=20, pady=(5, 5), sticky="ew")
        action_frame.grid_columnconfigure(1, weight=1)
        
        self.attach_btn = ctk.CTkButton(
            action_frame,
            text="🚀 开始处理",
            command=self._start_attaching,
            height=36,
            width=120,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.attach_btn.grid(row=0, column=0, padx=(0, 15), sticky="w")
        
        self.progress = ctk.CTkProgressBar(action_frame)
        self.progress.grid(row=0, column=1, sticky="ew")
        self.progress.set(0)
        row += 1
        
        # Log area
        log_label = ctk.CTkLabel(self.parent, text="📋 日志", anchor="w")
        log_label.grid(row=row, column=0, padx=20, pady=(10, 3), sticky="w")
        row += 1
        
        self.log_box = ctk.CTkTextbox(
            self.parent,
            height=100,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled"
        )
        self.log_box.grid(row=row, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Load engine if Excel was previously set
        if initial_excel:
            self.run_in_thread(self._load_engine_for_preview, initial_excel)
    
    def _browse_excel(self):
        """Browse for Excel file."""
        path = ctk.filedialog.askopenfilename(
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")],
            title="选择译名表"
        )
        if path:
            self.excel_path_var.set(path)
            self._on_excel_file_change(path)
    
    def _browse_text_file(self):
        """Browse for text file."""
        path = ctk.filedialog.askopenfilename(
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="选择文本文件"
        )
        if path:
            self.text_path_var.set(path)
            self._on_text_file_change(path)
    
    def _browse_output_file(self):
        """Browse for output file."""
        initial_dir = None
        if self.text_path_var.get():
            initial_dir = os.path.dirname(self.text_path_var.get())
        
        path = ctk.filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="保存输出文件"
        )
        if path:
            self.output_path_var.set(path)
    
    def _get_selected_template(self) -> str:
        """Get the currently selected format template string."""
        current_display = self.format_var.get()
        for template, desc in FORMAT_TEMPLATES:
            if desc == current_display:
                return template
        return FORMAT_TEMPLATES[0][0]
    
    def _on_format_change(self, choice: str):
        """Handle format selection change."""
        template = self._get_selected_template()
        if self.config_manager:
            self.config_manager.set_format_template(template)
        self._update_live_preview()
    
    def _on_text_file_change(self, path: str):
        """Handle text file selection change."""
        if self.config_manager and path:
            self.config_manager.set_last_text_file(path)
        if path and not self.output_path_var.get():
            base, ext = os.path.splitext(path)
            self.output_path_var.set(f"{base}_translated{ext}")
    
    def _on_excel_file_change(self, path: str):
        """Handle Excel file selection change."""
        if self.config_manager and path:
            self.config_manager.set_last_excel_file(path)
        if path:
            self.run_in_thread(self._load_engine_for_preview, path)
    
    def _load_engine_for_preview(self, excel_path: str):
        """Load translation engine in background for live preview."""
        try:
            self.engine.load_translation_table(excel_path)
            self.engine.build_search_indexes()
            self._engine_ready = True
            self.parent.after(0, self._update_live_preview)
        except Exception as e:
            self._engine_ready = False
    
    def _schedule_preview_update(self):
        """Schedule a preview update with debouncing."""
        if self._preview_update_id:
            self.parent.after_cancel(self._preview_update_id)
        self._preview_update_id = self.parent.after(300, self._update_live_preview)
    
    def _update_live_preview(self):
        """Update the output preview with translated text."""
        if not self._engine_ready:
            self.output_preview.configure(state="normal")
            self.output_preview.delete("1.0", "end")
            self.output_preview.insert("1.0", "⏳ 请先选择译名表...")
            self.output_preview.configure(state="disabled")
            return
        
        input_text = self.input_preview.get("1.0", "end-1c")
        
        if not input_text.strip():
            self.output_preview.configure(state="normal")
            self.output_preview.delete("1.0", "end")
            self.output_preview.configure(state="disabled")
            return
        
        try:
            format_template = self._get_selected_template()
            result_text = self.engine.attach_translations_to_text(
                input_text,
                format_template=format_template
            )
            
            self.output_preview.configure(state="normal")
            self.output_preview.delete("1.0", "end")
            self.output_preview.insert("1.0", result_text)
            self.output_preview.configure(state="disabled")
        except Exception as e:
            self.output_preview.configure(state="normal")
            self.output_preview.delete("1.0", "end")
            self.output_preview.insert("1.0", f"❌ 错误: {e}")
            self.output_preview.configure(state="disabled")
    
    def _start_attaching(self):
        """Start the attaching process for file mode."""
        text_path = self.text_path_var.get().strip()
        excel_path = self.excel_path_var.get().strip()
        output_path = self.output_path_var.get().strip()
        
        if not text_path:
            self.log_message(self.log_box, "❌ 错误: 请选择输入文件")
            return
        if not excel_path:
            self.log_message(self.log_box, "❌ 错误: 请选择译名表")
            return
        if not output_path:
            base, ext = os.path.splitext(text_path)
            output_path = f"{base}_translated{ext}"
            self.output_path_var.set(output_path)
        
        format_template = self._get_selected_template()
        
        self.clear_log(self.log_box)
        self.set_processing(True, self.attach_btn)
        self.progress.set(0)
        
        self.run_in_thread(
            self._do_attaching,
            text_path,
            excel_path,
            output_path,
            format_template
        )
    
    def _do_attaching(
        self,
        text_path: str,
        excel_path: str,
        output_path: str,
        format_template: str
    ):
        """Perform the attaching (runs in background thread)."""
        try:
            def log(msg: str):
                self.parent.after(0, lambda: self.log_message(self.log_box, msg))
            
            def set_progress(val: float):
                self.parent.after(0, lambda: self.progress.set(val))
            
            log("📚 加载译名表...")
            set_progress(0.15)
            self.engine.load_translation_table(excel_path, progress_callback=log)
            set_progress(0.35)
            
            log("🔧 构建索引...")
            self.engine.build_search_indexes(progress_callback=log)
            set_progress(0.5)
            
            log("📄 读取原文...")
            original_text = load_text_file(text_path, progress_callback=log)
            set_progress(0.6)
            
            log(f"🔗 附加译名...")
            result_text = self.engine.attach_translations_to_text(
                original_text,
                format_template=format_template
            )
            set_progress(0.85)
            
            log(f"💾 保存: {os.path.basename(output_path)}")
            save_text_file(output_path, result_text, progress_callback=log)
            set_progress(1.0)
            
            log(f"✅ 完成! {len(original_text)} → {len(result_text)} 字符")
            
        except Exception as e:
            self.parent.after(0, lambda: self.log_message(self.log_box, f"❌ 错误: {e}"))
        finally:
            self.parent.after(0, lambda: self.set_processing(False, self.attach_btn))
