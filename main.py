#!/usr/bin/env python3
# main.py
"""
Entry point for the PF2 Translation Tool Suite.

A GUI application for Pathfinder 2e translation tasks including:
- Term Extraction: Extract matching terms from text
- Term Attachment: Attach translations to original terms
"""

import sys
import os

# Add project root to path for module imports
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from ui.app import TranslationToolApp


def main():
    """Launch the translation tool application."""
    app = TranslationToolApp()
    app.mainloop()


if __name__ == "__main__":
    main()
