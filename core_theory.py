# core_theory.py
"""
core_theory.py - Modul pro pokročilejší hudební teorii.
"""
import logging
from core_music_theory import get_tritone_substitution  # Import z centrálního modulu

logger = logging.getLogger(__name__)


class MusicTheory:
    """Třída pro rozšířené funkce hudební teorie."""

    @classmethod
    def get_tritone_substitution(cls, dominant_chord: str) -> str:
        """
        DEPRECATED: Použijte get_tritone_substitution z core_music_theory modulu.
        Zachováno pro zpětnou kompatibilitu - deleguje na centrální funkci.

        Args:
            dominant_chord: Dominantní akord (např. "G7")

        Returns:
            str: Tritonová substituce (např. "Db7")
        """
        logger.warning("MusicTheory.get_tritone_substitution je deprecated. Použijte core_music_theory.get_tritone_substitution")
        return get_tritone_substitution(dominant_chord)
