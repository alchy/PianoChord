# midi/__init__.py
"""
midi/__init__.py - Inicializace MIDI modulu pro Piano Chord Analyzer.
Poskytuje nezávislý MIDI přehrávač s threading podporou.
"""

import logging

logger = logging.getLogger(__name__)
logger.info("MIDI modul inicializován")

# Import hlavní třídy
from .player import MidiPlayer, test_midi_availability

# Verze MIDI modulu
__version__ = "2.0.0"

# Seznam exportovaných objektů
__all__ = [
    "MidiPlayer",
    "test_midi_availability"
]


# Rychlá kontrola MIDI dostupnosti při importu
def check_midi_system():
    """
    Rychle zkontroluje dostupnost MIDI systému.

    Returns:
        dict: Informace o MIDI dostupnosti
    """
    try:
        import mido
        available_ports = mido.get_output_names()

        return {
            "available": True,
            "ports_count": len(available_ports),
            "ports": available_ports
        }
    except ImportError:
        return {
            "available": False,
            "error": "mido library not available"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


# Informace o MIDI při importu
_midi_info = check_midi_system()
if _midi_info["available"]:
    logger.info(f"MIDI dostupné: {_midi_info['ports_count']} portů")
else:
    logger.warning(f"MIDI nedostupné: {_midi_info['error']}")

# Export informací o MIDI
MIDI_AVAILABLE = _midi_info["available"]
AVAILABLE_PORTS = _midi_info.get("ports", [])
