# gui/__init__.py
"""
gui/__init__.py - Inicializace GUI modulu pro Piano Chord Analyzer.
Poskytuje refaktorované GUI komponenty s čistou separací od logiky.
"""

import logging

logger = logging.getLogger(__name__)
logger.info("GUI modul inicializován")

# Import hlavních GUI komponent
from .main_window import MainWindow
from .analysis_view import AnalysisView
from .controls_view import ControlsView
from .progression_view import ProgressionView

# Verze GUI modulu
__version__ = "2.0.0"

# Seznam exportovaných objektů
__all__ = [
    "MainWindow",
    "AnalysisView",
    "ControlsView",
    "ProgressionView"
]


# Kontrola tkinter dostupnosti
def check_gui_requirements():
    """
    Zkontroluje dostupnost GUI požadavků.

    Returns:
        dict: Informace o dostupnosti GUI
    """
    try:
        import tkinter as tk
        from tkinter import ttk

        # Test základní funkcionality
        root = tk.Tk()
        root.withdraw()

        # Test ttk komponent
        frame = ttk.Frame(root)
        notebook = ttk.Notebook(root)

        root.destroy()

        return {
            "available": True,
            "tkinter_version": tk.TkVersion
        }
    except ImportError as e:
        return {
            "available": False,
            "error": f"tkinter import error: {e}"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


# Kontrola při importu
_gui_info = check_gui_requirements()
if _gui_info["available"]:
    logger.info(f"GUI dostupný: tkinter {_gui_info['tkinter_version']}")
else:
    logger.error(f"GUI nedostupný: {_gui_info['error']}")

# Export informací
GUI_AVAILABLE = _gui_info["available"]
