# chord_analysis.py
"""
Core chord analysis logic for Piano Chord Analyzer.
Handles chord parsing, MIDI note generation, and chord validation.
"""

import logging
from typing import List, Tuple, Dict, Set
from errors import ChordParsingError, handle_error, validate_chord_name

logger = logging.getLogger(__name__)

# Musical constants
PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ENHARMONIC_MAP = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}
BLACK_KEYS = {"C#", "D#", "F#", "G#", "A#"}

# Chord type definitions - intervals from root
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

# Scale definitions for key analysis
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Roman numeral mappings for analysis
MAJOR_ROMAN_MAP = {0: "I", 2: "ii", 4: "iii", 5: "IV", 7: "V", 9: "vi", 11: "vii°"}
MINOR_ROMAN_MAP = {0: "i", 2: "ii°", 3: "III", 5: "iv", 7: "v", 8: "VI", 10: "VII"}

# Dominant chord types for secondary dominant detection
DOMINANT_TYPES = {"7", "9", "13", "7b9", "7b5", "dim7"}


class ChordAnalyzer:
    """
    Handles chord parsing, validation, and basic analysis.
    """

    def __init__(self):
        """Initialize the chord analyzer."""
        logger.info("ChordAnalyzer initialized")

    @handle_error
    def parse_chord_name(self, chord_name: str) -> Tuple[str, str]:
        """
        Parse chord name into base note and chord type.

        Args:
            chord_name: Chord name to parse (e.g., "Dm7", "C#maj9")

        Returns:
            Tuple of (base_note, chord_type)

        Raises:
            ChordParsingError: If chord cannot be parsed
        """
        chord_name = validate_chord_name(chord_name)

        # Handle sharp/flat notes (2 characters)
        if len(chord_name) > 1 and chord_name[1] in {'#', 'b'}:
            base_note = chord_name[:2]
            chord_type = chord_name[2:]
        else:
            base_note = chord_name[0]
            chord_type = chord_name[1:]

        # Normalize enharmonic equivalents
        base_note = ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())

        # Validate base note
        if base_note not in PIANO_KEYS:
            raise ChordParsingError(f"Invalid note: {base_note}")

        # Validate chord type
        if chord_type not in CHORD_TYPES:
            available_types = list(CHORD_TYPES.keys())[:10]  # Show first 10 for brevity
            raise ChordParsingError(f"Unknown chord type: '{chord_type}'. Available types: {available_types}")

        return base_note, chord_type

    @handle_error
    def get_chord_intervals(self, chord_type: str) -> List[int]:
        """
        Get intervals for a chord type.

        Args:
            chord_type: Type of chord (e.g., "m7", "maj9")

        Returns:
            List of intervals from root note

        Raises:
            ChordParsingError: If chord type is unknown
        """
        if chord_type not in CHORD_TYPES:
            raise ChordParsingError(f"Unknown chord type: {chord_type}")

        return CHORD_TYPES[chord_type].copy()

    @handle_error
    def chord_to_midi_notes(self, chord_name: str, octave: int = 4) -> List[int]:
        """
        Convert chord name to MIDI note numbers.

        Args:
            chord_name: Name of chord to convert
            octave: Base octave for the chord (default: 4)

        Returns:
            List of MIDI note numbers

        Raises:
            ChordParsingError: If chord cannot be parsed
        """
        base_note, chord_type = self.parse_chord_name(chord_name)
        intervals = self.get_chord_intervals(chord_type)

        # Calculate base MIDI note
        base_index = PIANO_KEYS.index(base_note)
        base_midi = 12 * octave + base_index

        # Generate chord MIDI notes
        midi_notes = [base_midi + interval for interval in intervals]

        # Ensure notes are in valid MIDI range (0-127)
        midi_notes = [note for note in midi_notes if 0 <= note <= 127]

        if not midi_notes:
            raise ChordParsingError(f"Chord {chord_name} in octave {octave} produces no valid MIDI notes")

        return midi_notes

    def is_minor_key(self, key: str) -> bool:
        """
        Check if a key signature is minor.

        Args:
            key: Key signature (e.g., "Am", "C")

        Returns:
            True if key is minor, False if major
        """
        return key.lower().endswith('m')

    @handle_error
    def get_scale_notes(self, key: str) -> Set[int]:
        """
        Get pitch classes (0-11) for a diatonic scale.

        Args:
            key: Key signature (e.g., "C", "Am")

        Returns:
            Set of pitch classes in the scale

        Raises:
            ChordParsingError: If key is invalid
        """
        # Parse key to get root note
        try:
            if self.is_minor_key(key):
                # Remove 'm' suffix for minor keys
                root_key = key[:-1] if key.endswith('m') else key
                intervals = MINOR_SCALE_INTERVALS
            else:
                root_key = key
                intervals = MAJOR_SCALE_INTERVALS

            base_note, _ = self.parse_chord_name(root_key)
            base_index = PIANO_KEYS.index(base_note)

            # Generate scale pitch classes
            scale_pitches = {(base_index + interval) % 12 for interval in intervals}
            return scale_pitches

        except Exception as e:
            raise ChordParsingError(f"Cannot generate scale for key '{key}': {e}")

    def is_dominant_chord(self, chord_type: str) -> bool:
        """
        Check if chord type is a dominant chord.

        Args:
            chord_type: Type of chord to check

        Returns:
            True if chord is dominant type
        """
        return chord_type in DOMINANT_TYPES

    @handle_error
    def get_roman_numeral(self, base_note: str, key: str) -> str:
        """
        Convert base note to Roman numeral in given key.

        Args:
            base_note: Note to convert (e.g., "D")
            key: Key context (e.g., "C", "Am")

        Returns:
            Roman numeral representation (e.g., "ii", "V")

        Raises:
            ChordParsingError: If conversion fails
        """
        try:
            # Parse key root
            if self.is_minor_key(key):
                key_root = key[:-1] if key.endswith('m') else key
                roman_map = MINOR_ROMAN_MAP
            else:
                key_root = key
                roman_map = MAJOR_ROMAN_MAP

            key_root_parsed, _ = self.parse_chord_name(key_root)
            note_parsed, _ = self.parse_chord_name(base_note)

            # Calculate degree
            key_index = PIANO_KEYS.index(key_root_parsed)
            note_index = PIANO_KEYS.index(note_parsed)
            degree = (note_index - key_index) % 12

            return roman_map.get(degree, f"[{degree}]")

        except Exception as e:
            raise ChordParsingError(f"Cannot convert {base_note} to roman numeral in key {key}: {e}")

    @handle_error
    def analyze_chord_in_key(self, chord_name: str, key: str) -> Dict:
        """
        Analyze a chord within a key context.

        Args:
            chord_name: Chord to analyze
            key: Key context

        Returns:
            Dictionary with analysis results
        """
        base_note, chord_type = self.parse_chord_name(chord_name)
        roman_numeral = self.get_roman_numeral(base_note, key)
        scale_notes = self.get_scale_notes(key)
        midi_notes = self.chord_to_midi_notes(chord_name)

        # Check if chord contains non-diatonic notes
        chord_pitches = {note % 12 for note in midi_notes}
        has_chromatic_notes = bool(chord_pitches - scale_notes)

        return {
            'chord_name': chord_name,
            'base_note': base_note,
            'chord_type': chord_type,
            'roman_numeral': roman_numeral,
            'key': key,
            'midi_notes': midi_notes,
            'is_diatonic': not has_chromatic_notes,
            'is_dominant': self.is_dominant_chord(chord_type),
            'chord_pitches': sorted(chord_pitches),
            'scale_pitches': sorted(scale_notes)
        }

    def validate_chord_name(self, chord_name: str) -> bool:
        """
        Validate if a chord name can be parsed.

        Args:
            chord_name: Chord name to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            self.parse_chord_name(chord_name)
            return True
        except ChordParsingError:
            return False
