# music_theory.py
"""
music_theory.py - Modul pro pokrocilejsi hudebni teorii.
"""
from harmony_analyzer import HarmonyAnalyzer
from constants import MusicalConstants

# --- DEBUG ---
DEBUG = True


class MusicTheory:
    """Trida pro rozsirene funkce hudebni teorie."""

    @classmethod
    def get_tritone_substitution(cls, dominant_chord: str) -> str:
        """
        Vrati tritonovou substituci pro dominantni akord.
        Priklad: G7 -> Db7
        """
        try:
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(dominant_chord)
            if '7' not in chord_type:  # Funguje jen pro dominantni akordy
                return dominant_chord

            base_index = MusicalConstants.PIANO_KEYS.index(base_note)
            tritone_index = (base_index + 6) % 12  # Tritonus je 6 pulktonu

            sub_note = MusicalConstants.PIANO_KEYS[tritone_index]

            if DEBUG:
                print(f"Tritonová substituce pro {dominant_chord} je {sub_note}{chord_type}")

            return f"{sub_note}{chord_type}"
        except ValueError:
            return dominant_chord  # V pripade chyby vrati puvodni akord
