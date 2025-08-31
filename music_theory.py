# music_theory.py
"""
music_theory.py - Modul pro pokročilejší hudební teorii.
OPRAVA: Aktualizované importy pro novou architekturu.
"""

import logging
from harmony_analyzer import HarmonyAnalyzer
from config import MusicalConstants

logger = logging.getLogger(__name__)


class MusicTheory:
    """Třída pro rozšířené funkce hudební teorie."""

    @classmethod
    def get_tritone_substitution(cls, dominant_chord: str) -> str:
        """
        Vrátí tritonovou substituci pro dominantní akord.
        Příklad: G7 -> Db7
        """
        try:
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(dominant_chord)

            # Funguje jen pro dominantní akordy
            if '7' not in chord_type:
                logger.warning(
                    f"Tritonová substituce funguje jen pro dominantní akordy, vrácen původní: {dominant_chord}")
                return dominant_chord

            base_index = MusicalConstants.PIANO_KEYS.index(base_note)
            tritone_index = (base_index + 6) % 12  # Tritonus je 6 půltónů

            sub_note = MusicalConstants.PIANO_KEYS[tritone_index]
            substitution = f"{sub_note}{chord_type}"

            logger.debug(f"Tritonová substituce pro {dominant_chord} je {substitution}")
            return substitution

        except (ValueError, IndexError) as e:
            logger.error(f"Chyba při výpočtu tritonové substituce pro {dominant_chord}: {e}")
            return dominant_chord  # V případě chyby vrátí původní akord
