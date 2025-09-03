# transposition_engine.py
"""
Transposition logic for Piano Chord Analyzer.
Handles transposing chords, progressions, and keys by semitones.
"""

import logging
from typing import List, Dict, Tuple
from chord_analysis import ChordAnalyzer, PIANO_KEYS
from errors import TranspositionError, handle_error

logger = logging.getLogger(__name__)


class TranspositionEngine:
    """
    Handles all transposition operations for chords and progressions.
    """

    def __init__(self, chord_analyzer: ChordAnalyzer):
        """
        Initialize transposition engine.

        Args:
            chord_analyzer: ChordAnalyzer instance for chord parsing
        """
        self.chord_analyzer = chord_analyzer
        logger.info("TranspositionEngine initialized")

    @handle_error
    def transpose_note(self, note: str, semitones: int) -> str:
        """
        Transpose a single note by the given number of semitones.

        Args:
            note: Note to transpose (e.g., "C", "F#")
            semitones: Number of semitones to transpose (positive = up, negative = down)

        Returns:
            Transposed note name

        Raises:
            TranspositionError: If transposition fails
        """
        try:
            # Parse note to separate base note from any chord suffix
            if len(note) > 1 and note[1] in {'#', 'b'}:
                base_note = note[:2]
                suffix = note[2:]
            else:
                base_note = note[0]
                suffix = note[1:]

            # Validate and get base note index
            base_note, _ = self.chord_analyzer.parse_chord_name(base_note)
            base_index = PIANO_KEYS.index(base_note)

            # Calculate new index with wraparound
            new_index = (base_index + semitones) % 12
            new_note = PIANO_KEYS[new_index] + suffix

            return new_note

        except Exception as e:
            raise TranspositionError(f"Cannot transpose note '{note}' by {semitones} semitones: {e}")

    @handle_error
    def transpose_chord(self, chord_name: str, semitones: int) -> str:
        """
        Transpose a chord by the given number of semitones.

        Args:
            chord_name: Chord to transpose (e.g., "Dm7", "C#maj9")
            semitones: Number of semitones to transpose

        Returns:
            Transposed chord name

        Raises:
            TranspositionError: If transposition fails
        """
        try:
            base_note, chord_type = self.chord_analyzer.parse_chord_name(chord_name)
            transposed_base = self.transpose_note(base_note, semitones)

            # Rebuild chord with transposed base note
            return f"{transposed_base}{chord_type}"

        except Exception as e:
            raise TranspositionError(f"Cannot transpose chord '{chord_name}' by {semitones} semitones: {e}")

    @handle_error
    def transpose_progression(self, chords: List[str], semitones: int) -> List[str]:
        """
        Transpose an entire chord progression.

        Args:
            chords: List of chord names to transpose
            semitones: Number of semitones to transpose

        Returns:
            List of transposed chord names

        Raises:
            TranspositionError: If any chord fails to transpose
        """
        if not chords:
            return []

        transposed_chords = []
        failed_chords = []

        for i, chord in enumerate(chords):
            try:
                transposed_chord = self.transpose_chord(chord, semitones)
                transposed_chords.append(transposed_chord)
            except TranspositionError as e:
                failed_chords.append((i, chord, str(e)))
                logger.warning(f"Failed to transpose chord {i}: {chord} - {e}")
                # Keep original chord as fallback
                transposed_chords.append(chord)

        if failed_chords:
            logger.warning(f"Some chords failed to transpose: {failed_chords}")

        return transposed_chords

    @handle_error
    def transpose_song_data(self, song_data: Dict, semitones: int) -> Dict:
        """
        Transpose all progressions in a song data structure.

        Args:
            song_data: Dictionary containing song information and progressions
            semitones: Number of semitones to transpose

        Returns:
            Transposed song data with updated key and progressions

        Raises:
            TranspositionError: If transposition fails
        """
        try:
            # Create copy to avoid modifying original
            transposed_data = song_data.copy()

            # Transpose key signature
            original_key = song_data.get("key", "C")
            transposed_key = self.transpose_note(original_key, semitones)
            transposed_data["key"] = transposed_key

            # Transpose all progressions
            transposed_progressions = []
            for progression in song_data.get("progressions", []):
                transposed_prog = progression.copy()

                # Transpose chords in this progression
                original_chords = progression.get("chords", [])
                transposed_chords = self.transpose_progression(original_chords, semitones)
                transposed_prog["chords"] = transposed_chords

                transposed_progressions.append(transposed_prog)

            transposed_data["progressions"] = transposed_progressions
            transposed_data["original_key"] = original_key
            transposed_data["transposed_by"] = semitones

            return transposed_data

        except Exception as e:
            raise TranspositionError(f"Cannot transpose song data by {semitones} semitones: {e}")

    def generate_all_transpositions(self, song_data: Dict) -> Dict[str, Dict]:
        """
        Generate all 11 transpositions of a song (1-11 semitones up).

        Args:
            song_data: Original song data to transpose

        Returns:
            Dictionary mapping transposition keys to transposed song data
        """
        transpositions = {}
        original_name = song_data.get("title", "Unknown")

        for semitones in range(1, 12):
            try:
                transposed_data = self.transpose_song_data(song_data, semitones)
                key = f"{original_name}_trans_{semitones}"
                transpositions[key] = transposed_data

            except TranspositionError as e:
                logger.warning(f"Failed to transpose {original_name} by {semitones} semitones: {e}")
                continue

        logger.info(f"Generated {len(transpositions)} transpositions for {original_name}")
        return transpositions

    @handle_error
    def find_best_transposition_for_chord(self, chord_name: str, song_data: Dict) -> Tuple[int, str]:
        """
        Find the best transposition of a song that contains the given chord.

        Args:
            chord_name: Target chord to find
            song_data: Song data to search in

        Returns:
            Tuple of (semitones_transposed, transposed_key) or (0, original_key) if not found
        """
        # Check if chord exists in original
        for progression in song_data.get("progressions", []):
            if chord_name in progression.get("chords", []):
                return 0, song_data.get("key", "C")

        # Try all transpositions
        for semitones in range(1, 12):
            try:
                transposed_data = self.transpose_song_data(song_data, semitones)

                # Check if chord exists in transposed version
                for progression in transposed_data.get("progressions", []):
                    if chord_name in progression.get("chords", []):
                        return semitones, transposed_data["key"]

            except TranspositionError:
                continue

        # Chord not found in any transposition
        return 0, song_data.get("key", "C")

    def get_interval_name(self, semitones: int) -> str:
        """
        Get the musical interval name for a number of semitones.

        Args:
            semitones: Number of semitones (0-11)

        Returns:
            Interval name (e.g., "Perfect 5th", "Major 3rd")
        """
        interval_names = {
            0: "Unison",
            1: "Minor 2nd",
            2: "Major 2nd",
            3: "Minor 3rd",
            4: "Major 3rd",
            5: "Perfect 4th",
            6: "Tritone",
            7: "Perfect 5th",
            8: "Minor 6th",
            9: "Major 6th",
            10: "Minor 7th",
            11: "Major 7th"
        }

        # Normalize to 0-11 range
        normalized = semitones % 12
        return interval_names.get(normalized, f"{normalized} semitones")

    @handle_error
    def calculate_transposition_distance(self, from_key: str, to_key: str) -> int:
        """
        Calculate the number of semitones needed to transpose from one key to another.

        Args:
            from_key: Starting key
            to_key: Target key

        Returns:
            Number of semitones (0-11)

        Raises:
            TranspositionError: If keys are invalid
        """
        try:
            from_note, _ = self.chord_analyzer.parse_chord_name(from_key)
            to_note, _ = self.chord_analyzer.parse_chord_name(to_key)

            from_index = PIANO_KEYS.index(from_note)
            to_index = PIANO_KEYS.index(to_note)

            # Calculate shortest distance (ascending)
            distance = (to_index - from_index) % 12
            return distance

        except Exception as e:
            raise TranspositionError(f"Cannot calculate transposition from {from_key} to {to_key}: {e}")
