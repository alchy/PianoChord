# harmony_analyzer.py
"""
harmony_analyzer.py - Analyza harmonie a progresi.
"""
from typing import Dict, Any, Tuple
from constants import MusicalConstants, ChordLibrary
from jazz_database import JazzStandardsDatabase

# --- DEBUG ---
DEBUG = True


class HarmonyAnalyzer:
    """Analyzator harmonie s vyuzitim databaze realnych progresi."""

    @classmethod
    def analyze(cls, base_note: str, chord_type: str) -> Dict[str, Any]:
        """
        Hlavni metoda pro analyzu akordu.
        Zaměřuje se na vlastnosti akordu a jeho výskyt v reálných progresích.
        """
        chord_full_name = f"{base_note}{chord_type or ''}".strip()

        # Pokud je chord_type prazdny, povazujeme za dur.
        if not chord_type:
            chord_type = "maj"

        # Analyza samotneho akordu
        chord_notes_raw = ChordLibrary.get_root_voicing(base_note, chord_type)
        chord_notes = [MusicalConstants.PIANO_KEYS[note % 12] for note in chord_notes_raw]

        # Hledani v databazi jazzovych standardu
        real_progressions = JazzStandardsDatabase.find_progressions_by_chord(base_note, chord_type)

        return {
            "chord_name": chord_full_name,
            "base_note": base_note,
            "chord_type": chord_type,
            "chord_notes": chord_notes,
            "real_progressions": real_progressions,
        }

    @classmethod
    def parse_chord_name(cls, chord_full_name: str) -> Tuple[str, str]:
        """Rozparsuje cely nazev akordu na zakladni notu a typ."""
        chord = chord_full_name.strip()
        if not chord:
            raise ValueError("Prázdný název akordu")

        # Zpracovani nazvu noty (napr. C, C#, Db)
        if len(chord) > 1 and chord[1] in ['#', 'b']:
            base_note = chord[:2]
            chord_type = chord[2:]
        else:
            base_note = chord[0]
            chord_type = chord[1:]

        # Normalizace enharmonickych nazvu (napr. Db -> C#)
        base_note = MusicalConstants.ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())

        if base_note not in MusicalConstants.PIANO_KEYS:
            raise ValueError(f"Neplatná základní nota akordu: {base_note}")

        # Specialni pripad pro akordy bez typu (napr. "C")
        if not chord_type and base_note in chord_full_name:
            chord_type = "maj"

        return base_note, chord_type
