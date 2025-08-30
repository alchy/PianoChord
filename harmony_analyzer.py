# harmony_analyzer.py
"""
harmony_analyzer.py - Analyza harmonie a progresi.
Tento modul analyzuje akordy a hledá je v jazzových progresech.
"""

from typing import Dict, Any, Tuple
from constants import MusicalConstants, ChordLibrary, DEBUG  # Opravil import DEBUG
from jazz_database import JazzStandardsDatabase
import logging  # NOVÉ: Import pro logování varování (optimalizace místo print)

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
        """Rozparsuje cely nazev akordu na zakladni notu a typ. Optimalizováno pro složité typy jako '7#11' nebo '13b9'."""
        chord = chord_full_name.strip()
        if not chord:
            raise ValueError("Prázdný název akordu")

        # Zpracovani nazvu noty (napr. C, C#, Db)
        if len(chord) > 1 and chord[1] in {'#', 'b'}:
            base_note = chord[:2]
            chord_type = chord[2:]
        else:
            base_note = chord[0]
            chord_type = chord[1:]

        # Normalizace enharmonickych nazvu (napr. Db -> C#)
        base_note = MusicalConstants.ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())

        if base_note not in MusicalConstants.PIANO_KEYS:
            raise ValueError(f"Neplatná základní nota akordu: {base_note}")

        # Specialni pripad pro akordy bez typu (napr. "C") – fallback na maj
        if not chord_type and base_note in chord_full_name:
            chord_type = "maj"

        # NOVÉ: Optimalizace pro složité typy s příponami (např. "7#11" zůstane jako "7#11", pokud je v knihovně)
        if chord_type not in ChordLibrary.CHORD_VOICINGS:
            original_type = chord_type
            # Fallback logika: Zjednodušit na základní typ (pro odstraněné warningů)
            if not original_type:  # Prázdný typ – fallback na maj (optimalizace pro klíče jako "Ab")
                chord_type = "maj"
            elif original_type.startswith('m'):
                chord_type = 'm7'  # Fallback pro minor varianty
            elif 'maj' in original_type:
                chord_type = 'maj7'  # Fallback pro major
            elif 'sus' in original_type:
                chord_type = 'sus4'  # Fallback pro suspended
            elif 'dim' in original_type:
                chord_type = 'dim7'  # Fallback pro diminished
            else:
                chord_type = '7'  # Default fallback pro dominantní typy
            # NOVÉ: Logování jen pokud DEBUG (optimalizace – méně spamu)
            if DEBUG:
                logging.warning(f"Neplatný typ akordu '{original_type}', použit fallback '{chord_type}' pro {chord_full_name}.")

        return base_note, chord_type