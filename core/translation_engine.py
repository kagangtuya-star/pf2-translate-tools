# translation_engine.py
"""
Core translation engine for term matching and attachment.
Extracted and refactored from test.py for use in the GUI application.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple

import nltk
import pandas as pd
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger(__name__)

MAX_PATTERN_LEN = 20_000


class NLTKManager:
    """Manages NLTK data initialization and resources."""
    
    _initialized = False
    _lemmatizer: Optional[WordNetLemmatizer] = None
    
    @classmethod
    def get_data_dir(cls) -> str:
        """Get the local NLTK data directory path."""
        script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(script_dir, "nltk_data")
    
    @classmethod
    def initialize(cls, progress_callback=None) -> bool:
        """
        Initialize NLTK resources, downloading if necessary.
        
        Args:
            progress_callback: Optional callback function(message: str) for progress updates
            
        Returns:
            True if initialization was successful
        """
        if cls._initialized:
            return True
            
        nltk_data_dir = cls.get_data_dir()
        
        def report(msg: str):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)
        
        # Create directory if needed
        if not os.path.exists(nltk_data_dir):
            report(f"创建本地 NLTK 数据目录: {nltk_data_dir}")
            os.makedirs(nltk_data_dir)
        
        # Add to NLTK search path
        if nltk_data_dir not in nltk.data.path:
            nltk.data.path.insert(0, nltk_data_dir)
        
        # Check/download required packages
        try:
            nltk.data.find('corpora/wordnet.zip')
            nltk.data.find('corpora/omw-1.4.zip')
            report(f"成功在本地目录 'nltk_data' 找到 NLTK 数据包。")
        except LookupError:
            report("未在本地找到 NLTK 数据包，正在下载...")
            try:
                nltk.download('wordnet', download_dir=nltk_data_dir, quiet=True)
                nltk.download('omw-1.4', download_dir=nltk_data_dir, quiet=True)
                report("NLTK 数据包已成功下载到本地。")
            except Exception as e:
                logger.error(f"下载 NLTK 数据包时出错: {e}")
                return False
        
        cls._lemmatizer = WordNetLemmatizer()
        cls._initialized = True
        return True
    
    @classmethod
    def get_lemmatizer(cls) -> WordNetLemmatizer:
        """Get the WordNet lemmatizer instance."""
        if not cls._initialized:
            cls.initialize()
        return cls._lemmatizer
    
    @classmethod
    def lemmatize_word(cls, word: str) -> str:
        """Lemmatize a word using both verb and noun forms."""
        lemmatizer = cls.get_lemmatizer()
        lemma = lemmatizer.lemmatize(word, pos='v')
        return lemmatizer.lemmatize(lemma, pos='n')


class TranslationEngine:
    """
    Core engine for translation term matching and text processing.
    
    Supports two main operations:
    1. Term extraction: Find terms in text and return matches
    2. Term attachment: Replace terms with "translation original" format
    """
    
    def __init__(self):
        self.translation_dict: Dict[str, str] = {}
        self._regex: Optional[re.Pattern] = None
        self._lower_to_original: Dict[str, str] = {}
        self._lemma_map: Dict[str, str] = {}
        self._indexes_built = False
    
    def load_translation_table(self, excel_path: str, progress_callback=None) -> int:
        """
        Load translation table from Excel file.
        
        Args:
            excel_path: Path to Excel file with source and target columns
            progress_callback: Optional callback for progress updates
            
        Returns:
            Number of terms loaded
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        def report(msg: str):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)
        
        report(f"正在加载 Excel 译名表: {excel_path}")
        
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"译名表文件 '{excel_path}' 不存在。")
        
        try:
            df = pd.read_excel(excel_path, header=0)
        except Exception as e:
            raise ValueError(f"无法读取 Excel 文件: {e}")
        
        if df.shape[1] < 2:
            raise ValueError(f"Excel 文件列数少于2，需要至少包含原文和译文两列。")
        
        source_col, target_col = str(df.columns[0]), str(df.columns[1])
        report(f"使用列 '{source_col}' 作为原文，'{target_col}' 作为译文。")
        
        df_cleaned = df[[source_col, target_col]].dropna()
        self.translation_dict = {
            str(row[source_col]).strip(): str(row[target_col]).strip()
            for _, row in df_cleaned.iterrows()
            if str(row[source_col]).strip() and str(row[target_col]).strip()
        }
        
        self._indexes_built = False
        report(f"成功加载 {len(self.translation_dict)} 个有效术语。")
        return len(self.translation_dict)
    
    def _join_terms_for_regex(self, escaped_list: List[str]) -> str:
        """Join escaped terms into a regex pattern, chunking if too long."""
        if not escaped_list:
            return ''
        chunks, buf, cur_len = [], [], 0
        for term in escaped_list:
            if cur_len + len(term) + 1 > MAX_PATTERN_LEN:
                chunks.append('|'.join(buf))
                buf, cur_len = [], 0
            buf.append(term)
            cur_len += len(term) + 1
        if buf:
            chunks.append('|'.join(buf))
        return chunks[0] if len(chunks) == 1 else '(?:' + ')|(?:'.join(chunks) + ')'
    
    def build_search_indexes(self, progress_callback=None):
        """
        Build regex and lookup indexes for efficient term matching.
        Must be called after loading translation table.
        """
        def report(msg: str):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)
        
        if not self.translation_dict:
            self._regex = None
            self._lower_to_original = {}
            self._lemma_map = {}
            self._indexes_built = True
            return
        
        report("正在构建术语搜索索引...")
        
        # Initialize NLTK
        NLTKManager.initialize(progress_callback)
        
        sorted_keys = sorted(self.translation_dict.keys(), key=len, reverse=True)
        self._lower_to_original = {k.lower(): k for k in sorted_keys}
        
        # Build lemma map for single-word terms
        self._lemma_map = {}
        for key in sorted_keys:
            key_lower = key.lower()
            if ' ' not in key_lower:
                lemma = NLTKManager.lemmatize_word(key_lower)
                if lemma != key_lower and lemma not in self._lower_to_original:
                    self._lemma_map[lemma] = key
        
        # Build regex pattern
        all_forms_lower = set(self._lower_to_original.keys()) | set(self._lemma_map.keys())
        escaped_terms = [re.escape(term) for term in sorted(all_forms_lower, key=len, reverse=True)]
        
        if escaped_terms:
            pattern_str = rf'\b({self._join_terms_for_regex(escaped_terms)})\b'
            self._regex = re.compile(pattern_str, re.IGNORECASE)
        else:
            self._regex = None
        
        self._indexes_built = True
        report("术语搜索索引构建完成。")
    
    def _ensure_indexes(self):
        """Ensure search indexes are built before matching."""
        if not self._indexes_built:
            self.build_search_indexes()
    
    def find_terms_in_text(self, text: str) -> Dict[str, str]:
        """
        Find all matching terms in the given text.
        
        Args:
            text: The text to search in
            
        Returns:
            Dictionary mapping original terms to their translations
        """
        self._ensure_indexes()
        
        if not text or not self._regex:
            return {}
        
        found_terms = {}
        for match in self._regex.finditer(text):
            matched_text = match.group(0).lower()
            original_key = self._lower_to_original.get(matched_text) or self._lemma_map.get(matched_text)
            if original_key and original_key not in found_terms:
                found_terms[original_key] = self.translation_dict[original_key]
        
        return found_terms
    
    def attach_translations_to_text(
        self, 
        text: str, 
        format_template: str = "{translation} {original}"
    ) -> str:
        """
        Replace terms in text with translation-attached format.
        
        Args:
            text: The text to process
            format_template: Format string with {translation} and {original} placeholders
                           Examples: "{translation} {original}", "{original}({translation})"
                           
        Returns:
            Text with terms replaced by translated format
        """
        self._ensure_indexes()
        
        if not text or not self._regex:
            return text
        
        # Track replacements to avoid double-processing
        replacements = []
        
        for match in self._regex.finditer(text):
            matched_text = match.group(0)
            matched_lower = matched_text.lower()
            original_key = self._lower_to_original.get(matched_lower) or self._lemma_map.get(matched_lower)
            
            if original_key:
                translation = self.translation_dict[original_key]
                # Preserve original case in output
                replacement = format_template.format(
                    translation=translation,
                    original=matched_text
                )
                replacements.append((match.start(), match.end(), replacement))
        
        # Apply replacements in reverse order to preserve positions
        result = text
        for start, end, replacement in reversed(replacements):
            result = result[:start] + replacement + result[end:]
        
        return result
    
    def get_term_count(self) -> int:
        """Get the number of loaded terms."""
        return len(self.translation_dict)
