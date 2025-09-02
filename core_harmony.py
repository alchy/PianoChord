# core_harmony.py
"""
core_harmony.py - Analýza harmonie a progresí.
Tento modul analyzuje akordy a hledá je v jazzových progresích.
"""

from typing import Dict, Any, Tuple
import logging

from core_constants import ChordLibrary
from core_music_theory import parse_chord_name  # Import z centrálního modulu
from utils_config import MusicalConstants
from core_database import JazzStandardsDatabase

logger = logging.getLogger(__name__)


class HarmonyAnalyzer:
    """Analyzátor harmonie s využitím databáze reálných progresí."""

    @classmethod
    def analyze(cls, base_note: str, chord_type: str) -> Dict[str, Any]:
        """
        Hlavní metoda pro analýzu akordu.
        Zaměřuje se na vlastnosti akordu a jeho výskyt v reálných progresích.

        Args:
            base_note: Základní nota akordu (např. "C", "F#")
            chord_type: Typ akordu (např. "maj7", "m7")

        Returns:
            Dict[str, Any]: Slovník s výsledky analýzy obsahující:
                - chord_name: Celý název akordu
                - base_note: Základní nota
                - chord_type: Typ akordu
                - chord_notes: Seznam not v akordu
                - real_progressions: Seznam nalezených progresí
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
        DEPRECATED: Použijte parse_chord_name z core_music_theory modulu.
        Zachováno pro zpětnou kompatibilitu - deleguje na centrální funkci.

        Args:
            chord_full_name: Celý název akordu

        Returns:
            Tuple[str, str]: (základní_nota, typ_akordu)
        """
        logger.warning("HarmonyAnalyzer.parse_chord_name je deprecated. Použijte core_music_theory.parse_chord_name")
        return parse_chord_name(chord_full_name)
