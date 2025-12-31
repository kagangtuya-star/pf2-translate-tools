# extractor_tab.py
"""
Term Extractor tab - extracts matching terms from text and exports results.
"""

import os
from typing import Dict, Optional

import customtkinter as ctk

from core.translation_engine import TranslationEngine
from core.file_utils import load_text_file, export_extraction_results
from .base_tab import BaseTab


class ExtractorTab(BaseTab):
    """
    Tab for extracting translation terms from text.
    
    Workflow:
    1. Select a text file to analyze
    2. Select an Excel translation table
    3. Click "Preview" to see found terms
    4. Review results in preview area
    5. Set output prefix and click "Export" to save results
    """
    
    tab_name = "译名提取"
    
    def __init__(self, parent: ctk.CTkFrame, config_manager=None):
        self.text_path_var: Optional[ctk.StringVar] = None
        self.excel_path_var: Optional[ctk.StringVar] = None
        self.output_prefix_var: Optional[ctk.StringVar] = None
        self.preview_btn: Optional[ctk.CTkButton] = None
        self.export_btn: Optional[ctk.CTkButton] = None
        self.progress: Optional[ctk.CTkProgressBar] = None
        self.log_box: Optional[ctk.CTkTextbox] = None
        self.preview_box: Optional[ctk.CTkTextbox] = None
        self.result_label: Optional[ctk.CTkLabel] = None
        self.engine = TranslationEngine()
        self._found_terms: Dict[str, str] = {}  # Store found terms for export
        
        super().__init__(parent, config_manager)
    
    def create_widgets(self):
        """Create the extractor tab widgets."""
        row = 0
        
        # Title
        title = ctk.CTkLabel(
            self.parent,
            text="📖 译名提取工具",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=row, column=0, padx=20, pady=(20, 5), sticky="w")
        row += 1
        
        # Description
        desc = ctk.CTkLabel(
            self.parent,
            text="从文本中提取匹配译名表的术语，预览后导出为 TXT 和 Excel 格式。",
            text_color="gray"
        )
        desc.grid(row=row, column=0, padx=20, pady=(0, 15), sticky="w")
        row += 1
        
        # Text file selector
        initial_text = ""
        if self.config_manager:
            initial_text = self.config_manager.get_last_text_file()
        
        _, self.text_path_var = self.create_file_selector(
            row=row,
            label_text="文本文件:",
            file_types=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initial_value=initial_text,
            on_change=self._on_text_file_change
        )
        row += 1
        
        # Excel file selector
        initial_excel = ""
        if self.config_manager:
            initial_excel = self.config_manager.get_last_excel_file()
        
        _, self.excel_path_var = self.create_file_selector(
            row=row,
            label_text="译名表:",
            file_types=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")],
            initial_value=initial_excel,
            on_change=self._on_excel_file_change
        )
        row += 1
        
        # Button frame for Preview and Export
        btn_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        btn_frame.grid(row=row, column=0, padx=20, pady=15, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Preview button
        self.preview_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 预览提取结果",
            command=self._start_preview,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.preview_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # Export button (initially disabled)
        self.export_btn = ctk.CTkButton(
            btn_frame,
            text="💾 导出结果",
            command=self._export_results,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            fg_color="green"
        )
        self.export_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        row += 1
        
        # Progress bar
        self.progress = self.create_progress_bar(row)
        row += 1
        
        # Result count label
        self.result_label = ctk.CTkLabel(
            self.parent,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.result_label.grid(row=row, column=0, padx=20, pady=(10, 5), sticky="w")
        row += 1
        
        # Preview area
        preview_label = ctk.CTkLabel(self.parent, text="提取预览:", anchor="w")
        preview_label.grid(row=row, column=0, padx=20, pady=(5, 5), sticky="w")
        row += 1
        
        self.preview_box = ctk.CTkTextbox(
            self.parent,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled"
        )
        self.preview_box.grid(row=row, column=0, padx=20, pady=(0, 10), sticky="nsew")
        row += 1
        
        # Output prefix selector (shown after preview)
        initial_output = ""
        if self.config_manager:
            initial_output = self.config_manager.get_last_output_dir()
        
        _, self.output_prefix_var = self.create_output_prefix_selector(row, initial_output)
        row += 1
        
        # Log area
        self.log_box = self.create_log_area(row)
        row += 2  # log_area uses 2 rows
        
        # Configure row weight for preview box to expand
        self.parent.grid_rowconfigure(row - 5, weight=1)
    
    def create_output_prefix_selector(self, row: int, initial_value: str = "") -> tuple:
        """Create output prefix input with directory browse."""
        frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=20, pady=(10, 5), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        # Label
        label = ctk.CTkLabel(frame, text="输出前缀:", width=100, anchor="w")
        label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Entry
        entry_var = ctk.StringVar(value=initial_value)
        entry = ctk.CTkEntry(
            frame, 
            textvariable=entry_var, 
            placeholder_text="输出文件名前缀 (如: output/result)"
        )
        entry.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        
        # Browse button (for directory, then append prefix)
        def browse():
            path = ctk.filedialog.askdirectory(title="选择输出目录")
            if path:
                # Append a default prefix
                entry_var.set(os.path.join(path, "extraction"))
                if self.config_manager:
                    self.config_manager.set_last_output_dir(path)
        
        browse_btn = ctk.CTkButton(frame, text="浏览...", width=80, command=browse)
        browse_btn.grid(row=0, column=2, sticky="e")
        
        return frame, entry_var
    
    def _on_text_file_change(self, path: str):
        """Handle text file selection change."""
        if self.config_manager and path:
            self.config_manager.set_last_text_file(path)
        # Clear previous results when file changes
        self._clear_preview()
    
    def _on_excel_file_change(self, path: str):
        """Handle Excel file selection change."""
        if self.config_manager and path:
            self.config_manager.set_last_excel_file(path)
        # Clear previous results when file changes
        self._clear_preview()
    
    def _clear_preview(self):
        """Clear the preview area and disable export."""
        self._found_terms = {}
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.configure(state="disabled")
        self.result_label.configure(text="")
        self.export_btn.configure(state="disabled")
    
    def _update_preview(self, terms: Dict[str, str]):
        """Update the preview area with found terms."""
        self._found_terms = terms
        sorted_terms = sorted(terms.items(), key=lambda x: len(x[0]), reverse=True)
        
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        
        if sorted_terms:
            for original, translation in sorted_terms:
                self.preview_box.insert("end", f"{original}    →    {translation}\n")
            self.result_label.configure(
                text=f"✅ 共找到 {len(terms)} 个术语",
                text_color="green"
            )
            self.export_btn.configure(state="normal")
        else:
            self.preview_box.insert("end", "未找到任何匹配的术语。")
            self.result_label.configure(
                text="⚠️ 未找到匹配术语",
                text_color="orange"
            )
            self.export_btn.configure(state="disabled")
        
        self.preview_box.configure(state="disabled")
    
    def _start_preview(self):
        """Start the preview process in a background thread."""
        # Validate inputs
        text_path = self.text_path_var.get().strip()
        excel_path = self.excel_path_var.get().strip()
        
        if not text_path:
            self.log_message(self.log_box, "❌ 错误: 请选择文本文件")
            return
        if not excel_path:
            self.log_message(self.log_box, "❌ 错误: 请选择译名表文件")
            return
        
        # Clear log and start
        self.clear_log(self.log_box)
        self._clear_preview()
        self.set_processing(True, self.preview_btn)
        self.progress.set(0)
        
        # Run in background thread
        self.run_in_thread(self._do_preview, text_path, excel_path)
    
    def _do_preview(self, text_path: str, excel_path: str):
        """Perform the preview extraction (runs in background thread)."""
        try:
            def log(msg: str):
                self.parent.after(0, lambda: self.log_message(self.log_box, msg))
            
            def set_progress(val: float):
                self.parent.after(0, lambda: self.progress.set(val))
            
            # Step 1: Load translation table
            log("📚 正在加载译名表...")
            set_progress(0.1)
            self.engine.load_translation_table(excel_path, progress_callback=log)
            set_progress(0.3)
            
            # Step 2: Build search indexes
            log("🔧 正在构建搜索索引...")
            self.engine.build_search_indexes(progress_callback=log)
            set_progress(0.5)
            
            # Step 3: Load and search text
            log("📄 正在读取并搜索文本...")
            text_content = load_text_file(text_path, progress_callback=log)
            found_terms = self.engine.find_terms_in_text(text_content)
            set_progress(1.0)
            
            log(f"✅ 预览完成，共找到 {len(found_terms)} 个独特术语。")
            log('📋 请在上方预览区查看结果，确认无误后点击"导出结果"。')
            
            # Update preview in main thread
            self.parent.after(0, lambda: self._update_preview(found_terms))
            
        except FileNotFoundError as e:
            self.parent.after(0, lambda: self.log_message(self.log_box, f"❌ 文件未找到: {e}"))
        except ValueError as e:
            self.parent.after(0, lambda: self.log_message(self.log_box, f"❌ 数据错误: {e}"))
        except Exception as e:
            self.parent.after(0, lambda: self.log_message(self.log_box, f"❌ 发生错误: {e}"))
        finally:
            self.parent.after(0, lambda: self.set_processing(False, self.preview_btn))
    
    def _export_results(self):
        """Export the previewed results to files."""
        if not self._found_terms:
            self.log_message(self.log_box, "❌ 没有可导出的结果，请先进行预览。")
            return
        
        text_path = self.text_path_var.get().strip()
        output_prefix = self.output_prefix_var.get().strip()
        
        if not output_prefix:
            # Default to text file directory
            output_prefix = os.path.splitext(text_path)[0]
        
        self.set_processing(True, self.export_btn)
        self.run_in_thread(self._do_export, output_prefix)
    
    def _do_export(self, output_prefix: str):
        """Perform the export (runs in background thread)."""
        try:
            def log(msg: str):
                self.parent.after(0, lambda: self.log_message(self.log_box, msg))
            
            log("💾 正在导出结果...")
            txt_path, excel_out_path = export_extraction_results(
                self._found_terms, output_prefix, progress_callback=log
            )
            
            log(f"📁 结果已保存:")
            log(f"   TXT: {txt_path}")
            log(f"   Excel: {excel_out_path}")
            log("🎉 导出完成！")
            
        except Exception as e:
            self.parent.after(0, lambda: self.log_message(self.log_box, f"❌ 导出错误: {e}"))
        finally:
            self.parent.after(0, lambda: self.set_processing(False, self.export_btn))
