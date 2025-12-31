# file_utils.py
"""
File I/O utilities for the translation tool.
"""

import logging
import os
from typing import Dict, List, Tuple

import chardet
import pandas as pd

logger = logging.getLogger(__name__)


def load_text_file(file_path: str, progress_callback=None) -> str:
    """
    Load a text file with automatic encoding detection.
    
    Args:
        file_path: Path to the text file
        progress_callback: Optional callback for progress updates
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    def report(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)
    
    report(f"正在读取文本文件: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文本文件 '{file_path}' 不存在。")
    
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
            confidence = result.get('confidence', 0)
            report(f"检测到文件编码为: {encoding} (置信度: {confidence:.0%})")
            return raw_data.decode(encoding, errors='replace')
    except Exception as e:
        raise IOError(f"读取文件时发生错误: {e}")


def save_text_file(file_path: str, content: str, encoding: str = 'utf-8', progress_callback=None):
    """
    Save content to a text file.
    
    Args:
        file_path: Path to save the file
        content: Content to write
        encoding: File encoding (default: utf-8)
        progress_callback: Optional callback for progress updates
    """
    def report(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)
    
    report(f"正在保存文件: {file_path}")
    
    # Ensure directory exists
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        report(f"文件保存成功: {file_path}")
    except Exception as e:
        raise IOError(f"保存文件时发生错误: {e}")


def export_to_excel(
    data: List[Tuple[str, str]], 
    file_path: str, 
    columns: Tuple[str, str] = ('原文', '译文'),
    progress_callback=None
):
    """
    Export data to an Excel file.
    
    Args:
        data: List of (source, target) tuples
        file_path: Path to save the Excel file
        columns: Column names tuple (default: ('原文', '译文'))
        progress_callback: Optional callback for progress updates
    """
    def report(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)
    
    report(f"正在导出 Excel 文件: {file_path}")
    
    # Ensure directory exists
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    try:
        df = pd.DataFrame(data, columns=list(columns))
        df.to_excel(file_path, index=False)
        report(f"Excel 文件导出成功: {file_path}")
    except Exception as e:
        raise IOError(f"导出 Excel 文件时发生错误: {e}")


def export_extraction_results(
    found_terms: Dict[str, str], 
    output_prefix: str,
    progress_callback=None
) -> Tuple[str, str]:
    """
    Export extraction results to both TXT and Excel formats.
    
    Args:
        found_terms: Dictionary of original -> translation mappings
        output_prefix: Prefix for output file names
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (txt_path, excel_path)
    """
    def report(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)
    
    if not found_terms:
        report("未找到任何匹配的术语，不生成输出文件。")
        return None, None
    
    # Sort by term length (longest first)
    sorted_terms = sorted(found_terms.items(), key=lambda item: len(item[0]), reverse=True)
    
    # Save TXT
    txt_path = f"{output_prefix}_results.txt"
    report(f"正在保存 TXT 结果: {txt_path}")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("提取到的术语列表 (原名 -> 译名):\n" + "=" * 40 + "\n")
        for original, translation in sorted_terms:
            f.write(f"{original}    {translation}\n")
    
    # Save Excel
    excel_path = f"{output_prefix}_results.xlsx"
    export_to_excel(sorted_terms, excel_path, progress_callback=progress_callback)
    
    report(f"结果文件已成功保存。共 {len(found_terms)} 个术语。")
    return txt_path, excel_path
