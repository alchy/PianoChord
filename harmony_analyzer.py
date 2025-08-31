# harmony_analyzer.py
"""
harmony_analyzer.py - Analýza harmonie a progresí.
Tento modul analyzuje akordy a hledá je v jazzových progresích.
OPRAVA: Aktualizované importy pro novou architekturu.
"""

from typing import Dict, Any, Tuple
import logging

from constants import ChordLibrary
from config import MusicalConstants  # OPRAVA: Import z config místo constants
from jazz_database import JazzStandardsDatabase

logger = logging.getLogger(__name__)


class HarmonyAnalyzer:
    """Analyzátor harmonie s využitím databáze reálných progresí."""

    @classmethod
    def analyze(cls, base_note: str, chord_type: str) -> Dict[str, Any]:
        """
        Hlavní metoda pro analýzu akordu.
        Zaměřuje se na vlastnosti akordu a jeho výskyt v reálných progresích.
        """
        chord_full_name = f"{base_note}{chord_type or ''}".strip()

        # Pokud je chord_type prázdný, považujeme za dur
        if not chord_type:
            chord_type = "maj"

        # Analýza samotného akordu
        try:
            chord_notes_raw = ChordLibrary.get_root_voicing(base_note, chord_type)
            chord_notes = [MusicalConstants.PIANO_KEYS[note % 12] for note in chord_notes_raw]
        except (ValueError, IndexError) as e:
            logger.error(f"Chyba při získávání voicingu pro {chord_full_name}: {e}")
            chord_notes = []

        # Hledání v databázi jazzových standardů
        try:
            real_progressions = JazzStandardsDatabase.find_progressions_by_chord(base_note, chord_type)
        except Exception as e:
            logger.error(f"Chyba při hledání progresí pro {chord_full_name}: {e}")
            real_progressions = []

        logger.debug(f"Analyzován akord {chord_full_name}: {len(real_progressions)} progresí nalezeno")

        return {
            "chord_name": chord_full_name,
            "base_note": base_note,
            "chord_type": chord_type,
            "chord_notes": chord_notes,
            "real_progressions": real_progressions,
        }

    @classmethod
    def parse_chord_name(cls, chord_full_name: str) -> Tuple[str, str]:
        """
        Rozparsuje celý název akordu na základní notu a typ.
        Optimalizováno pro složité typy jako '7#11' nebo '13b9'.
        """
        chord = chord_full_name.strip()
        if not chord:
            raise ValueError("Prázdný název akordu")

        # Zpracování názvu noty (např. C, C#, Db)
        if len(chord) > 1 and chord[1] in {'#', 'b'}:
            base_note = chord[:2]
            chord_type = chord[2:]
        else:
            base_note = chord[0]
            chord_type = chord[1:]

        # Normalizace enharmonických názvů (např. Db -> C#)
        base_note = MusicalConstants.ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())

        if base_note not in MusicalConstants.PIANO_KEYS:
            raise ValueError(f"Neplatná základní nota akordu: {base_note}")

        # Speciální případ pro akordy bez typu (např. "C") - fallback na maj
        if not chord_type and base_note in chord_full_name:
            chord_type = "maj"

        # Validace typu akordu s fallback logikou
        if chord_type not in ChordLibrary.CHORD_VOICINGS:
            original_type = chord_type

            # Fallback logika pro neznámé typy
            if not original_type:  # Prázdný typ - fallback na maj
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

            logger.warning(
                f"Neplatný typ akordu '{original_type}', použit fallback '{chord_type}' pro {chord_full_name}")

        return base_note, chord_type
