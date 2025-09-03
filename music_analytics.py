# music_analytics.py
"""
Module for music analysis logic, including chord parsing, voicing, progression management, and secondary dominant detection.
"""

import json
import logging
from typing import List, Dict, Tuple, Set

import config

logger = logging.getLogger(__name__)


class MusicAnalytics:
    """
    Handles music logic: chord analysis, progressions, voicings, and secondary dominants.
    """

    def __init__(self):
        # Input: None
        # Description: Initializes the music analytics with default values, loads database, creates transposed versions, and builds genres cache.
        # Output: None
        # Called by: PianoChordAnalyzer in gui.py
        self.voicing_type = config.DEFAULT_VOICING_TYPE
        self.previous_chord_midi = []

        self.current_progression = []
        self.current_index = 0
        self.current_annotations = []
        self.progression_source = ""

        self.database = self._load_database()
        self.transposed_database = self._create_transposed_database()
        self.genres_cache = self._build_genres_cache()

        logger.info("MusicAnalytics initialized")

    def _load_database(self) -> Dict:
        # Input: None
        # Description: Loads the chord progressions database from a JSON file or returns a fallback if loading fails.
        # Output: Dictionary of song data with progressions.
        # Called by: __init__
        try:
            with open('database.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return self._get_fallback_database()

    def _get_fallback_database(self) -> Dict:
        # Input: None
        # Description: Provides a default fallback database if the main one fails to load.
        # Output: Dictionary with a sample progression.
        # Called by: _load_database
        return {
            "ii-V-I Major": {
                "genre": "jazz-progressions",
                "key": "C",
                "progressions": [{"chords": ["Dm7", "G7", "Cmaj7"], "description": "Basic ii-V-I"}]
            }
        }

    def _create_transposed_database(self) -> Dict:
        # Input: None
        # Description: Creates transposed versions of all songs in the database for more chord options.
        # Output: Dictionary of transposed song data.
        # Called by: __init__
        transposed = {}

        for song_name, song_data in self.database.items():
            original_key = song_data.get("key", "C")

            for semitones in range(1, 12):
                try:
                    transposed_key = self._transpose_note(original_key, semitones)

                    transposed_progressions = []
                    for prog in song_data.get("progressions", []):
                        transposed_chords = [self._transpose_chord(chord, semitones) for chord in
                                             prog.get("chords", [])]
                        transposed_prog = prog.copy()
                        transposed_prog["chords"] = transposed_chords
                        transposed_progressions.append(transposed_prog)

                    transposed_song = song_data.copy()
                    transposed_song["key"] = transposed_key
                    transposed_song["progressions"] = transposed_progressions
                    transposed_song["original_key"] = original_key
                    transposed_song["transposed_by"] = semitones

                    transposed_name = f"{song_name}_trans_{semitones}"
                    transposed[transposed_name] = transposed_song

                except Exception as e:
                    logger.warning(f"Error transposing {song_name} by {semitones}: {e}")
                    continue

        logger.info(f"Created {len(transposed)} transposed songs")
        return transposed

    def _transpose_note(self, note: str, semitones: int) -> str:
        # Input: note (str) - The note to transpose, semitones (int) - Number of semitones to transpose by.
        # Description: Transposes a note by the given number of semitones.
        # Output: Transposed note string.
        # Called by: _create_transposed_database, _transpose_chord
        if len(note) > 1 and note[1] in {'#', 'b'}:
            base_note = note[:2]
            chord_part = note[2:]
        else:
            base_note = note[0]
            chord_part = note[1:]

        base_note = config.ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())
        index = config.PIANO_KEYS.index(base_note)
        new_index = (index + semitones) % 12
        return config.PIANO_KEYS[new_index] + chord_part

    def _transpose_chord(self, chord: str, semitones: int) -> str:
        # Input: chord (str) - The chord to transpose, semitones (int) - Number of semitones.
        # Description: Transposes an entire chord by the given semitones.
        # Output: Transposed chord string.
        # Called by: _create_transposed_database
        try:
            base_note, chord_type = self.parse_chord(chord)
            new_base_note = self._transpose_note(base_note, semitones)
            return f"{new_base_note}{chord_type}"
        except Exception as e:
            logger.warning(f"Error transposing chord {chord}: {e}")
            return chord

    def _build_genres_cache(self) -> Dict[str, List[str]]:
        # Input: None
        # Description: Builds a cache of genres for faster access.
        # Output: Dictionary mapping genres to list of song names.
        # Called by: __init__
        genres = {}
        for song_name, song_data in self.database.items():
            genre = song_data.get("genre", "unknown")
            if genre not in genres:
                genres[genre] = []
            genres[genre].append(song_name)
        return genres

    def parse_chord(self, chord_name: str) -> Tuple[str, str]:
        # Input: chord_name (str) - The chord name to parse.
        # Description: Splits the chord name into base note and chord type.
        # Output: Tuple (base_note, chord_type)
        # Called by: get_chord_midi, get_voicing, _transpose_chord, analyze_chord, find_progressions, get_scale_notes, detect_secondary_dominants, get_roman_numeral, generate_secondary_dominant
        chord = chord_name.strip()
        if len(chord) > 1 and chord[1] in {'#', 'b'}:
            base_note = chord[:2]
            chord_type = chord[2:]
        else:
            base_note = chord[0]
            chord_type = chord[1:]

        base_note = config.ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())
        if base_note not in config.PIANO_KEYS:
            raise ValueError(f"Invalid note: {base_note}")

        return base_note, chord_type

    def get_chord_midi(self, base_note: str, chord_type: str, octave: int = config.DEFAULT_OCTAVE) -> List[int]:
        # Input: base_note (str), chord_type (str), octave (int, optional)
        # Description: Returns MIDI notes for the given chord.
        # Output: List of MIDI note integers.
        # Called by: get_voicing, detect_secondary_dominants (indirectly)
        intervals = config.CHORD_TYPES.get(chord_type, config.CHORD_TYPES["maj"])
        base_idx = config.PIANO_KEYS.index(base_note)
        base_midi = 12 * octave + base_idx
        return [base_midi + interval for interval in intervals]

    def get_voicing(self, chord_name: str) -> List[int]:
        # Input: chord_name (str)
        # Description: Returns MIDI notes for the chord based on the selected voicing type.
        # Output: List of MIDI notes.
        # Called by: draw_chord in gui.py (via KeyboardDisplay), play_secondary_dominant (indirectly)
        try:
            base_note, chord_type = self.parse_chord(chord_name)
            root_midi = self.get_chord_midi(base_note, chord_type)

            if self.voicing_type == "smooth" and self.previous_chord_midi:
                return self._get_smooth_voicing(root_midi)
            elif self.voicing_type == "drop2":
                return self._get_drop2_voicing(root_midi)
            else:
                return root_midi
        except Exception as e:
            logger.error(f"Error getting voicing: {e}")
            return []

    def _get_smooth_voicing(self, root_voicing: List[int]) -> List[int]:
        # Input: root_voicing (List[int]) - Basic MIDI notes.
        # Description: Returns smooth voicing to minimize movement between chords.
        # Output: List of adjusted MIDI notes.
        # Called by: get_voicing
        best_voicing = root_voicing
        min_distance = float('inf')
        avg_prev = sum(self.previous_chord_midi) / len(self.previous_chord_midi)

        for octave_shift in range(-2, 3):
            for inversion in range(len(root_voicing)):
                inverted_notes = root_voicing[inversion:] + [note + 12 for note in root_voicing[:inversion]]
                current_voicing = [note + octave_shift * 12 for note in inverted_notes]
                avg_current = sum(current_voicing) / len(current_voicing)
                distance = abs(avg_current - avg_prev)

                if distance < min_distance:
                    min_distance = distance
                    best_voicing = current_voicing

        return best_voicing

    def _get_drop2_voicing(self, root_voicing: List[int]) -> List[int]:
        # Input: root_voicing (List[int])
        # Description: Returns drop-2 voicing for the chord.
        # Output: List of adjusted MIDI notes.
        # Called by: get_voicing
        if len(root_voicing) < 4:
            return root_voicing

        drop2_voicing = root_voicing.copy()
        sorted_notes = sorted(drop2_voicing)
        second_highest = sorted_notes[-2]
        second_highest_index = drop2_voicing.index(second_highest)
        drop2_voicing[second_highest_index] = second_highest - 12
        return sorted(drop2_voicing)

    def analyze_chord(self, chord_name: str) -> Dict:
        # Input: chord_name (str)
        # Description: Performs complete analysis of the given chord, including finding progressions.
        # Output: Dictionary with analysis results.
        # Called by: analyze_chord in gui.py
        try:
            base_note, chord_type = self.parse_chord(chord_name)
            progressions = self.find_progressions(chord_name)

            return {
                'chord_name': chord_name,
                'base_note': base_note,
                'chord_type': chord_type,
                'progressions': progressions,
                'success': True
            }
        except Exception as e:
            return {'chord_name': chord_name, 'error': str(e), 'success': False}

    def find_progressions(self, chord_name: str) -> List[Dict]:
        # Input: chord_name (str)
        # Description: Finds progressions containing the given chord in the database and transposed versions, including annotations for secondary dominants.
        # Output: List of progression dictionaries with annotations.
        # Called by: analyze_chord
        results = []

        for song_name, song_data in self.database.items():
            for prog in song_data.get("progressions", []):
                chords = prog.get("chords", [])
                if chord_name in chords:
                    annotations = self.detect_secondary_dominants(chords, song_data.get("key", "C"))
                    results.append({
                        'song': song_name,
                        'chords': chords,
                        'annotations': annotations,
                        'description': prog.get('description', ''),
                        'genre': song_data.get('genre', 'unknown'),
                        'transposed_by': 0,
                        'original_key': song_data.get('key', 'Unknown')
                    })

        for song_name, song_data in self.transposed_database.items():
            for prog in song_data.get("progressions", []):
                chords = prog.get("chords", [])
                if chord_name in chords:
                    original_name = song_name.split("_trans_")[0]
                    annotations = self.detect_secondary_dominants(chords, song_data.get("key", "C"))
                    results.append({
                        'song': original_name,
                        'chords': chords,
                        'annotations': annotations,
                        'description': prog.get('description', ''),
                        'genre': song_data.get('genre', 'unknown'),
                        'transposed_by': song_data.get('transposed_by', 0),
                        'original_key': song_data.get('original_key', 'Unknown')
                    })

        return results

    def is_minor_key(self, key: str) -> bool:
        # Input: key (str)
        # Description: Checks if the key is minor (based on 'm' suffix or db info).
        # Output: Boolean
        # Called by: get_roman_numeral, get_scale_notes
        return key.lower().endswith('m')  # Simple check; extend if db has mode

    def get_scale_notes(self, key: str) -> Set[int]:
        # Input: key (str) - The key (e.g., "C")
        # Description: Returns MIDI pitches (mod 12) for the diatonic scale of the key (assuming major).
        # Output: Set of pitch classes.
        # Called by: detect_secondary_dominants
        try:
            intervals = config.MINOR_SCALE_INTERVALS if self.is_minor_key(key) else config.MAJOR_SCALE_INTERVALS
            base_note, _ = self.parse_chord(key)
            base_idx = config.PIANO_KEYS.index(base_note)
            return {(base_idx + interval) % 12 for interval in intervals}
        except Exception as e:
            logger.warning(f"Error generating scale for {key}: {e}")
            return set()

    def is_dominant_type(self, chord_type: str) -> bool:
        # Input: chord_type (str)
        # Description: Checks if the chord type is dominant.
        # Output: Boolean
        # Called by: detect_secondary_dominants
        return chord_type in config.EXTENDED_DOMINANT_TYPES

    def has_chromatic_notes(self, midi_notes: List[int], scale_notes: Set[int]) -> bool:
        # Input: midi_notes (List[int]), scale_notes (Set[int])
        # Description: Checks if the chord contains notes outside the scale.
        # Output: Boolean
        # Called by: detect_secondary_dominants
        chord_pitches = {note % 12 for note in midi_notes}
        return any(pitch not in scale_notes for pitch in chord_pitches)

    def detect_secondary_dominants(self, progression: List[str], key: str) -> List[str]:
        # Input: progression (List[str]) - List of chord names, key (str) - The key of the progression.
        # Description: Detects secondary dominants in the progression.
        # Output: List of annotations (e.g., ["", "V7/ii", ""]).
        # Called by: find_progressions, on_progression_double_click in gui.py
        annotations = [""] * len(progression)
        scale_notes = self.get_scale_notes(key)

        for i in range(len(progression) - 1):
            chord1 = progression[i]
            chord2 = progression[i + 1]

            try:
                base1, type1 = self.parse_chord(chord1)
                base2, _ = self.parse_chord(chord2)
                root1_idx = config.PIANO_KEYS.index(base1)
                root2_idx = config.PIANO_KEYS.index(base2)

                # Check if root1 is V to root2: root2 = (root1 + 5) % 12
                if (root1_idx + 5) % 12 != root2_idx:
                    continue

                if not self.is_dominant_type(type1):
                    continue

                midi_notes1 = self.get_chord_midi(base1, type1)
                if not self.has_chromatic_notes(midi_notes1, scale_notes):
                    continue

                target_roman = self.get_roman_numeral(base2, key)
                if type1 == "dim7":
                    annotations[i] = f"vii°/{target_roman}"
                else:
                    annotations[i] = f"V{type1 if type1 else ''}/{target_roman}"

            except Exception as e:
                logger.warning(f"Error detecting secondary dominant for {chord1} -> {chord2}: {e}")

        return annotations

    def get_roman_numeral(self, base_note: str, key: str) -> str:
        # Input: base_note (str), key (str)
        # Description: Converts base_note to Roman numeral in the given key (for major).
        # Output: Roman numeral string (e.g., "ii").
        # Called by: detect_secondary_dominants
        key_root_idx = config.PIANO_KEYS.index(self.parse_chord(key)[0])
        note_idx = config.PIANO_KEYS.index(base_note)
        degree = (note_idx - key_root_idx) % 12
        roman_map = config.MINOR_ROMAN_MAP if self.is_minor_key(key) else config.MAJOR_ROMAN_MAP
        return roman_map.get(degree, f"[{degree}]")  # Fallback to degree if unknown (no more "?")

    def generate_secondary_dominant(self, target_chord: str) -> str:
        # Input: target_chord (str) - e.g., "Dm"
        # Description: Generates the secondary dominant chord name (V7/target).
        # Output: Chord name string, e.g., "A7"
        # Called by: play_secondary_dominant in gui.py
        base_note, chord_type = self.parse_chord(target_chord)
        target_idx = config.PIANO_KEYS.index(base_note)
        dom_idx = (target_idx + 7) % 12  # Up P5 for dom root
        dom_note = config.PIANO_KEYS[dom_idx]
        return f"{dom_note}7"  # Simple dom7; could extend to voicing
