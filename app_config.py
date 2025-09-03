# app_config.py
"""
Application configuration for Piano Chord Analyzer.
Centralized configuration settings and constants.
"""

import logging
from pathlib import Path

# Application information
APP_NAME = "Piano Chord Analyzer"
APP_VERSION = "2.0.0-refactored"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# Window settings
DEFAULT_WINDOW_SIZE = "1200x800"
MIN_WINDOW_SIZE = (900, 600)

# File paths
DEFAULT_DATABASE_PATH = "database.json"
DEFAULT_LOG_FILE = "piano_analyzer.log"

# MIDI settings
DEFAULT_MIDI_VELOCITY = 64
DEFAULT_CHORD_DURATION = 1.0
DEFAULT_OCTAVE = 4

# Keyboard display settings
WHITE_KEY_WIDTH = 18
WHITE_KEY_HEIGHT = 80
BLACK_KEY_WIDTH = 12
BLACK_KEY_HEIGHT = 50
KEYBOARD_WIDTH = 52 * WHITE_KEY_WIDTH
KEYBOARD_HEIGHT = WHITE_KEY_HEIGHT + 10

# Colors
WHITE_KEY_FILL = "white"
BLACK_KEY_FILL = "black"
KEY_OUTLINE_COLOR = "gray"
KEYBOARD_BG_COLOR = "lightgray"

VOICING_COLORS = {
    'root': '#FF6B6B',  # Red
    'smooth': '#4ECDC4',  # Teal
    'drop2': '#45B7D1'  # Blue
}

# Default settings
DEFAULT_VOICING_TYPE = "root"
DEFAULT_MIDI_ENABLED = True

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# GUI layout settings
MAIN_PADDING = 10
COMPONENT_PADDING = 5

# TreeView column widths
TREEVIEW_COLUMN_WIDTHS = {
    "analysis_song": 180,
    "analysis_progression": 250,
    "analysis_description": 200,
    "analysis_genre": 120,
    "analysis_key": 50,
    "analysis_composer": 150,
    "progression_index": 50,
    "progression_chord": 120,
    "progression_function": 200
}

# Musical constants (moved from other files for centralization)
PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ENHARMONIC_MAP = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}
BLACK_KEYS = {"C#", "D#", "F#", "G#", "A#"}

# Scale intervals
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Roman numeral mappings
MAJOR_ROMAN_MAP = {0: "I", 2: "ii", 4: "iii", 5: "IV", 7: "V", 9: "vi", 11: "vii°"}
MINOR_ROMAN_MAP = {0: "i", 2: "ii°", 3: "III", 5: "iv", 7: "v", 8: "VI", 10: "VII"}

# Chord type definitions
CHORD_TYPES = {
    "": [0, 4, 7],  # Major triad
    "maj": [0, 4, 7],  # Major triad
    "maj7": [0, 4, 7, 11],  # Major 7th
    "maj9": [0, 4, 7, 11, 14],  # Major 9th
    "m": [0, 3, 7],  # Minor triad
    "m7": [0, 3, 7, 10],  # Minor 7th
    "m9": [0, 3, 7, 10, 14],  # Minor 9th
    "m6": [0, 3, 7, 9],  # Minor 6th
    "7": [0, 4, 7, 10],  # Dominant 7th
    "9": [0, 4, 7, 10, 14],  # Dominant 9th
    "13": [0, 4, 7, 10, 14, 21],  # Dominant 13th
    "dim": [0, 3, 6],  # Diminished triad
    "dim7": [0, 3, 6, 9],  # Diminished 7th
    "aug": [0, 4, 8],  # Augmented triad
    "sus2": [0, 2, 7],  # Suspended 2nd
    "sus4": [0, 5, 7],  # Suspended 4th
    "m7b5": [0, 3, 6, 10],  # Half-diminished 7th
    "6": [0, 4, 7, 9],  # Major 6th
    "7b9": [0, 4, 7, 10, 13],  # Dominant 7th flat 9
    "7b5": [0, 4, 6, 10]  # Dominant 7th flat 5
}

# Dominant chord types for analysis
DOMINANT_TYPES = {"7", "9", "13", "7b9", "7b5", "dim7"}


def setup_logging(log_file: str = None, level: int = None):
    """
    Setup application logging configuration.

    Args:
        log_file: Optional log file path
        level: Optional logging level
    """
    log_file = log_file or DEFAULT_LOG_FILE
    level = level or LOG_LEVEL

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )


def get_app_info():
    """Get application information dictionary."""
    return {
        'name': APP_NAME,
        'version': APP_VERSION,
        'title': APP_TITLE
    }


def validate_config():
    """
    Validate configuration settings.

    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []

    # Check database file
    if not Path(DEFAULT_DATABASE_PATH).exists():
        errors.append(f"Database file not found: {DEFAULT_DATABASE_PATH}")

    # Check MIDI settings
    if not (0 <= DEFAULT_MIDI_VELOCITY <= 127):
        errors.append(f"Invalid MIDI velocity: {DEFAULT_MIDI_VELOCITY} (must be 0-127)")

    if DEFAULT_CHORD_DURATION <= 0:
        errors.append(f"Invalid chord duration: {DEFAULT_CHORD_DURATION} (must be positive)")

    # Check keyboard settings
    if WHITE_KEY_WIDTH <= 0 or WHITE_KEY_HEIGHT <= 0:
        errors.append("Invalid keyboard dimensions")

    return errors
