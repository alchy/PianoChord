# config.py
"""
Kompletní konfigurace pro Piano Chord Analyzer.
Obsahuje všechny konstanty pro GUI, MIDI, hudební teorii a analýzu.
"""

# ============================================================================
# ZÁKLADNÍ NASTAVENÍ APLIKACE
# ============================================================================
APP_TITLE = "Piano Chord Analyzer - Jazz Training Edition"
APP_VERSION = "2.1"
APP_GEOMETRY = "1200x800"
APP_MINSIZE = (1000, 700)

# ============================================================================
# MIDI NASTAVENÍ
# ============================================================================
DEFAULT_MIDI_ENABLED = True
DEFAULT_MIDI_VELOCITY = 64
CHORD_PLAY_DURATION = 1.0  # Délka přehrání akordu v sekundách
DEFAULT_OCTAVE = 4  # Výchozí oktáva pro generování MIDI not

# ============================================================================
# HUDEBNÍ TEORIE - ZÁKLADNÍ DEFINICE
# ============================================================================

# Definice klavírních kláves (chromatická stupnice)
PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Mapa enharmonických ekvivalentů (přepis b na #)
ENHARMONIC_MAP = {
    "DB": "C#",
    "EB": "D#",
    "GB": "F#",
    "AB": "G#",
    "BB": "A#"
}

# Množina černých kláves
BLACK_KEYS = {"C#", "D#", "F#", "G#", "A#"}

# ============================================================================
# DEFINICE AKORDOVÝCH TYPŮ
# ============================================================================
# Každý typ akordu je definován intervaly v půltónech od základního tónu
CHORD_TYPES = {
    # Základní durové akordy
    "": [0, 4, 7],              # Major triad (implicitní)
    "maj": [0, 4, 7],           # Major triad (explicitní)
    "maj7": [0, 4, 7, 11],      # Major 7th
    "maj9": [0, 4, 7, 11, 14],  # Major 9th
    "maj13": [0, 4, 7, 11, 14, 21],  # Major 13th
    "6": [0, 4, 7, 9],          # Major 6th

    # Mollové akordy
    "m": [0, 3, 7],             # Minor triad
    "m7": [0, 3, 7, 10],        # Minor 7th
    "m9": [0, 3, 7, 10, 14],    # Minor 9th
    "m11": [0, 3, 7, 10, 14, 17],  # Minor 11th
    "m6": [0, 3, 7, 9],         # Minor 6th
    "m(maj7)": [0, 3, 7, 11],   # Minor major 7th

    # Dominantní akordy
    "7": [0, 4, 7, 10],         # Dominant 7th
    "9": [0, 4, 7, 10, 14],     # Dominant 9th
    "11": [0, 4, 7, 10, 14, 17],  # Dominant 11th
    "13": [0, 4, 7, 10, 14, 21],  # Dominant 13th

    # Alterované dominanty
    "7b9": [0, 4, 7, 10, 13],   # Dominant 7 flat 9
    "7#9": [0, 4, 7, 10, 15],   # Dominant 7 sharp 9
    "7b5": [0, 4, 6, 10],       # Dominant 7 flat 5
    "7#5": [0, 4, 8, 10],       # Dominant 7 sharp 5 (augmented 7th)
    "7b9#11": [0, 4, 7, 10, 13, 18],  # Dominant 7 flat 9 sharp 11
    "7alt": [0, 4, 6, 10, 13],  # Altered dominant (simplified)

    # Zmenšené a zvětšené
    "dim": [0, 3, 6],           # Diminished triad
    "dim7": [0, 3, 6, 9],       # Diminished 7th
    "m7b5": [0, 3, 6, 10],      # Half-diminished (minor 7 flat 5)
    "aug": [0, 4, 8],           # Augmented triad

    # Suspended akordy
    "sus2": [0, 2, 7],          # Suspended 2nd
    "sus4": [0, 5, 7],          # Suspended 4th
    "7sus4": [0, 5, 7, 10],     # Dominant 7 suspended 4th
}

# ============================================================================
# STUPNICE A MODY
# ============================================================================

# Intervaly durové stupnice (C dur: C D E F G A B)
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]

# Intervaly mollové stupnice (přirozený moll)
MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Mody
MODES = {
    "Ionian": [0, 2, 4, 5, 7, 9, 11],      # Dur
    "Dorian": [0, 2, 3, 5, 7, 9, 10],      # Mollový s velkou sextou
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],    # Mollový s malou sekundou
    "Lydian": [0, 2, 4, 6, 7, 9, 11],      # Durový se zvýšenou kvartou
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],  # Durový s malou septimou
    "Aeolian": [0, 2, 3, 5, 7, 8, 10],     # Přirozený moll
    "Locrian": [0, 1, 3, 5, 6, 8, 10],     # Zmenšený
}

# Alterovaná stupnice (pro alterované dominanty)
ALTERED_SCALE = [0, 1, 3, 4, 6, 8, 10]

# Whole tone stupnice (pro zvětšené akordy)
WHOLE_TONE_SCALE = [0, 2, 4, 6, 8, 10]

# Diminished scale (symetrická)
DIMINISHED_SCALE = [0, 2, 3, 5, 6, 8, 9, 11]

# ============================================================================
# ŘÍMSKÉ ČÍSLICE PRO STUPNĚ
# ============================================================================

# Mapa stupňů na římské číslice v durové tónině
MAJOR_ROMAN_MAP = {
    0: "I",    # Tónika
    1: "bII",  # Neapolská sexta
    2: "II",   # Supertonická
    3: "bIII", # Mollová medianta
    4: "III",  # Medianta
    5: "IV",   # Subdominanta
    6: "bV",   # Tritónová substituce
    7: "V",    # Dominanta
    8: "bVI",  # Mollová submedianta
    9: "VI",   # Submedianta
    10: "bVII",# Mollová subtónika
    11: "VII", # Citlivý tón
}

# Mapa stupňů na římské číslice v mollové tónině
MINOR_ROMAN_MAP = {
    0: "i",    # Tónika
    1: "bII",  # Neapolská sexta
    2: "ii",   # Supertonická
    3: "III",  # Medianta (relativní dur)
    4: "bIV",  # Subdominanta
    5: "iv",   # Mollová subdominanta
    6: "bV",   # Tritónová substituce
    7: "V",    # Dominanta (obvykle durová v harmonickém mollu)
    8: "VI",   # Submedianta (relativní dur)
    9: "bVI",  # Mollová submedianta
    10: "VII", # Subtónika
    11: "vii", # Citlivý tón (zmenšený)
}

# ============================================================================
# TYPY DOMINANTNÍCH AKORDŮ
# ============================================================================

# Rozšířený seznam dominantních typů pro detekci sekundárních dominant
EXTENDED_DOMINANT_TYPES = {
    "7", "9", "11", "13",
    "7b9", "7#9", "7b5", "7#5",
    "7b9#11", "7alt", "7sus4",
    "dim7"  # Zmenšený septakord může fungovat jako dominanta
}

# ============================================================================
# HARMONICKÉ FUNKCE
# ============================================================================

# Mapa akordových typů na harmonické funkce
HARMONIC_FUNCTIONS = {
    "Tonic": ["maj", "maj7", "maj9", "6", "m", "m7", "m9", "m6"],
    "Subdominant": ["maj", "maj7", "m", "m7", "m9"],
    "Dominant": ["7", "9", "11", "13", "7b9", "7#9", "7b5", "7#5", "7alt", "dim7"],
    "Diminished": ["dim", "dim7", "m7b5"],
}

# ============================================================================
# CHORD-SCALE RELATIONSHIPS
# ============================================================================

# Mapa akordových typů na doporučené stupnice pro improvizaci
CHORD_SCALE_MAP = {
    "maj": "Ionian",
    "maj7": "Ionian",
    "maj9": "Ionian",
    "6": "Ionian",

    "m": "Dorian",
    "m7": "Dorian",
    "m9": "Dorian",
    "m6": "Dorian",

    "7": "Mixolydian",
    "9": "Mixolydian",
    "13": "Mixolydian",

    "7b9": "Altered",
    "7#9": "Altered",
    "7alt": "Altered",
    "7b5": "Whole Tone",
    "7#5": "Whole Tone",

    "m7b5": "Locrian",
    "dim7": "Diminished",

    "sus4": "Mixolydian",
    "7sus4": "Mixolydian",
}

# ============================================================================
# GUI - KLAVIATURA
# ============================================================================

# Rozměry bílých kláves
WHITE_KEY_WIDTH = 18
WHITE_KEY_HEIGHT = 80

# Rozměry černých kláves
BLACK_KEY_WIDTH = 12
BLACK_KEY_HEIGHT = 50

# Barvy kláves
WHITE_KEY_FILL = "white"
BLACK_KEY_FILL = "black"
KEY_OUTLINE_COLOR = "black"

# Šířky obrysu kláves
DEFAULT_KEY_WIDTH = 1
DEFAULT_HIGHLIGHT_WIDTH = 2

# Rozměry klaviatury
KEYBOARD_WIDTH = 52 * WHITE_KEY_WIDTH  # 52 bílých kláves pro 88 kláves
KEYBOARD_HEIGHT = 100
KEYBOARD_BG_COLOR = "lightgray"

# Barvy pro různé typy voicingu
VOICING_COLORS = {
    "root": "red",
    "smooth": "green",
    "drop2": "blue",
}

# ============================================================================
# GUI - VOICING TYPY
# ============================================================================

DEFAULT_VOICING_TYPE = "root"

# ============================================================================
# GUI - TREEVIEW SLOUPCE
# ============================================================================

TREEVIEW_COLUMN_WIDTHS = {
    "analysis": 200,
    "progression_index": 50,
    "progression_chord": 150,
}

# ============================================================================
# GUI - FONTY A TEXTY
# ============================================================================

CURRENT_CHORD_FONT = ("Arial", 14, "bold")
CURRENT_CHORD_DEFAULT_TEXT = "- no chord -"

# ============================================================================
# JAZZ THEORY - COMMON PROGRESSIONS
# ============================================================================

# Časté jazzové progrese pro generátor
COMMON_JAZZ_PROGRESSIONS = [
    ["ii", "V", "I"],           # ii-V-I
    ["I", "VI", "ii", "V"],     # I-VI-ii-V (rhythm changes)
    ["I", "III", "VI", "II", "V"],  # Circle of fifths
    ["I", "bIII", "bVI", "bII", "I"],  # Coltrane changes (simplified)
]

# ============================================================================
# PRACTICE MODE SETTINGS
# ============================================================================

# Obtížnosti pro cvičení
DIFFICULTY_LEVELS = ["Easy", "Medium", "Medium-Advanced", "Advanced", "Very Advanced"]

# Typy cvičení
PRACTICE_MODES = {
    "ear_training": "Ear Training",
    "sight_reading": "Sight Reading",
    "improvisation": "Improvisation Practice",
    "voice_leading": "Voice Leading",
}

# ============================================================================
# EXPORT SETTINGS
# ============================================================================

# Podporované exportní formáty
EXPORT_FORMATS = ["PDF", "MIDI", "JSON", "TXT"]

# ============================================================================
# LOGOVÁNÍ
# ============================================================================

LOG_FILE = "piano_analyzer.log"
LOG_LEVEL = "INFO"
