# constants.py
"""
constants.py - Definuje hudebni konstanty a knihovnu akordu.
"""
from typing import List
from functools import lru_cache

# --- DEBUG ---
DEBUG = True


class MusicalConstants:
    """Hudebni konstanty pouzivane v aplikaci."""
    PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    ENHARMONIC_MAP = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}

    BLACK_KEYS = {"C#", "D#", "F#", "G#", "A#"}

    # Rozmery pro kresleni klaviatury
    WHITE_KEY_WIDTH = 18
    WHITE_KEY_HEIGHT = 80
    BLACK_KEY_WIDTH = 12
    BLACK_KEY_HEIGHT = 50

    ARCHETYPE_SIZE = 88  # Pocet klaves
    MIDI_BASE_OCTAVE = 4  # Stredni C = C4


class ChordLibrary:
    """Knihovna akordu a jejich voicingu."""
    CHORD_VOICINGS = {
        # Major
        "maj": [0, 4, 7],
        "maj7": [0, 4, 7, 11],
        "maj9": [0, 4, 7, 11, 14],
        "6": [0, 4, 7, 9],
        # Minor
        "m": [0, 3, 7],
        "m7": [0, 3, 7, 10],
        "m9": [0, 3, 7, 10, 14],
        "m6": [0, 3, 7, 9],
        "m7b5": [0, 3, 6, 10],
        # Dominant
        "7": [0, 4, 7, 10],
        "9": [0, 4, 7, 10, 14],
        "13": [0, 4, 7, 10, 14, 21],
        # Diminished / Other
        "dim": [0, 3, 6],
        "dim7": [0, 3, 6, 9],
        "aug": [0, 4, 8],
        "sus2": [0, 2, 7],
        "sus4": [0, 5, 7],
    }

    @classmethod
    @lru_cache(maxsize=256)
    def get_root_voicing(cls, base_note: str, chord_type: str) -> List[int]:
        """Vrati MIDI noty pro akord v zakladnim tvaru."""
        if chord_type not in cls.CHORD_VOICINGS:
            # Fallback pro pripady jako G, C, atd.
            if not chord_type:
                chord_type = "maj"
            else:
                raise ValueError(f"Neznamy typ akordu: {chord_type}")

        base_note_val = MusicalConstants.PIANO_KEYS.index(base_note)
        intervals = cls.CHORD_VOICINGS[chord_type]

        # Posun na zakladni oktavu (napr. C4)
        base_midi = 12 * MusicalConstants.MIDI_BASE_OCTAVE + base_note_val

        return [base_midi + i for i in intervals]

    @classmethod
    def get_smooth_voicing(cls, base_note: str, chord_type: str, prev_chord_midi: List[int]) -> List[int]:
        """Najde nejblizsi inverzi akordu k predchozimu akordu."""
        if not prev_chord_midi:
            return cls.get_root_voicing(base_note, chord_type)

        root_voicing = cls.get_root_voicing(base_note, chord_type)
        best_voicing = root_voicing
        min_distance = float('inf')

        avg_prev = sum(prev_chord_midi) / len(prev_chord_midi)

        # Prozkouma ruzne oktavy a inverze
        for octave_shift in range(-2, 3):
            for i in range(len(root_voicing)):
                inversion = root_voicing[i:] + [note + 12 for note in root_voicing[:i]]
                current_voicing = [note + octave_shift * 12 for note in inversion]

                avg_current = sum(current_voicing) / len(current_voicing)
                distance = abs(avg_current - avg_prev)

                if distance < min_distance:
                    min_distance = distance
                    best_voicing = current_voicing

        return best_voicing

    @staticmethod
    def midi_to_key_nr(midi_note: int, base_octave_midi_start: int = 21) -> int:
        """Prevede MIDI cislo na cislo klavesy (A0 = 0)."""
        return midi_note - base_octave_midi_start  # 21 je MIDI pro A0

# NOVÉ: Funkce pro transpozici not a akordů
def transpose_note(note: str, semitones: int) -> str:
    """Transponuje základní notu o daný počet půltónů."""
    note = MusicalConstants.ENHARMONIC_MAP.get(note.upper(), note.upper())
    if note not in MusicalConstants.PIANO_KEYS:
        raise ValueError(f"Neplatná nota: {note}")
    index = MusicalConstants.PIANO_KEYS.index(note)
    new_index = (index + semitones) % 12
    return MusicalConstants.PIANO_KEYS[new_index]

def transpose_chord(chord: str, semitones: int) -> str:
    """Transponuje celý akord (base_note + type) o daný počet půltónů."""
    from harmony_analyzer import HarmonyAnalyzer  # Import zde, aby se vyhnuli cyklickému importu
    base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord)
    new_base_note = transpose_note(base_note, semitones)
    return f"{new_base_note}{chord_type}"