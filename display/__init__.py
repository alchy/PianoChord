# display/__init__.py
"""
display/__init__.py - Inicializace display modulu pro Piano Chord Analyzer.
Poskytuje komponenty pro vizuální zobrazení s automatickým MIDI.
"""

import logging

logger = logging.getLogger(__name__)
logger.info("Display modul inicializován")

# Import hlavních tříd
from .keyboard_display import KeyboardDisplay, PianoKey

# Verze display modulu
__version__ = "2.0.0"

# Seznam exportovaných objektů
__all__ = [
    "KeyboardDisplay",
    "PianoKey"
]


# Kontrola tkinter dostupnosti
def check_display_requirements():
    """
    Zkontroluje dostupnost display požadavků (tkinter).

    Returns:
        dict: Informace o dostupnosti
    """
    try:
        import tkinter as tk

        # Test vytvoření základního Canvas
        root = tk.Tk()
        root.withdraw()  # Skryje okno
        canvas = tk.Canvas(root, width=100, height=100)
        root.destroy()

        return {
            "available": True,
            "tkinter_version": tk.TkVersion
        }
    except ImportError:
        return {
            "available": False,
            "error": "tkinter not available"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


# Informace o display při importu
_display_info = check_display_requirements()
if _display_info["available"]:
    logger.info(f"Display dostupný: tkinter {_display_info['tkinter_version']}")
else:
    logger.error(f"Display nedostupný: {_display_info['error']}")

# Export informací
DISPLAY_AVAILABLE = _display_info["available"]
