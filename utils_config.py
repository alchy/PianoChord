# config.py
# utils_config.py
"""
utils_config.py - Centralizovaná konfigurace aplikace.
"""
import logging
from typing import Dict, List

# Globální debug flag pro celou aplikaci
DEBUG = True


class AppConfig:
    """Centralizované nastavení aplikace."""

    # GUI nastavení
    WINDOW_TITLE = "Piano Chord Analyzer"
    WINDOW_SIZE = "1000x750"

    # Klávesové zkratky
    KEY_ANALYZE = '<Return>'
    KEY_PREV_CHORD = '<Left>'
    KEY_NEXT_CHORD = '<Right>'

    # MIDI výchozí hodnoty
    DEFAULT_MIDI_VELOCITY = 64
    DEFAULT_CHORD_DURATION = 1.0
    MIDI_ALL_NOTES_OFF_CC = 123

    # Log nastavení
    LOG_FORMAT = '[{timestamp}] {message}'
    LOG_FILE = 'app.log' if DEBUG else None


class MusicalConstants:
    """Hudební konstanty používané v aplikaci."""

    PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    ENHARMONIC_MAP = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}
    BLACK_KEYS = {"C#", "D#", "F#", "G#", "A#"}

    # Rozměry pro kreslení klaviatury (nezasahujeme do renderingu)
    WHITE_KEY_WIDTH = 18
    WHITE_KEY_HEIGHT = 80
    BLACK_KEY_WIDTH = 12
    BLACK_KEY_HEIGHT = 50

    ARCHETYPE_SIZE = 88
    MIDI_BASE_OCTAVE = 4


def setup_logging():
    """Nastaví centralizované logování pro celou aplikaci s podporou UTF-8."""
    if DEBUG:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Console handler s UTF-8 enkódováním pro Windows
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # File handler s UTF-8 enkódováním
    handlers = [console_handler]
    if AppConfig.LOG_FILE:
        try:
            file_handler = logging.FileHandler(AppConfig.LOG_FILE, encoding='utf-8')
            file_handler.setLevel(level)
            handlers.append(file_handler)
        except Exception:
            # Pokud selže file handler, pokračuj jen s console
            pass

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=handlers,
        force=True  # Přepiše existující konfiguraci
    )


# Inicializace loggingu při importu modulu
setup_logging()
logger = logging.getLogger(__name__)
