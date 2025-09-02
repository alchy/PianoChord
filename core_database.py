# core_database.py
"""
core_database.py - Databáze jazzových standardů a jejich progresí.
"""

import logging
from typing import List, Dict, Optional, Any
from functools import lru_cache
import json

logger = logging.getLogger(__name__)


class JazzStandardsDatabase:
    """Databáze jazzových standardů a jejich progresí."""

    # Načtení databáze z JSON souboru
    with open('database.json', 'r', encoding='utf-8') as f:
        JAZZ_STANDARDS = json.load(f)

    # Slovník pro transponované verze (vytvoří se při inicializaci)
    TRANSPOSED_STANDARDS = {}

    @classmethod
    def _initialize_transposed_standards(cls):
        """
        Vytvoří transponované verze standardů pro všech 11 transpozic.
        OPRAVENO: Používá centrální core_music_theory.py místo lokálních importů.
        """
        if cls.TRANSPOSED_STANDARDS:  # Už inicializováno
            return

        # OPRAVA: Import z centrálního modulu
        try:
            from core_music_theory import transpose_note, transpose_chord
        except ImportError as e:
            logger.error(f"Chyba importu transpose funkcí z core_music_theory: {e}")
            return

        transposed_count = 0
        for song_name, song_data in cls.JAZZ_STANDARDS.items():
            original_key = song_data["key"]

            for semitones in range(1, 12):  # 1 až 11
                try:
                    # OPRAVA: Rozlišení mezi jednoduchou notou a akordem
                    if len(original_key) == 1 or (len(original_key) == 2 and original_key[1] in ['#', 'b']):
                        # Jednoduchá nota
                        transposed_key = transpose_note(original_key, semitones)
                    else:
                        # Složený akord
                        transposed_key = transpose_chord(original_key, semitones)

                    transposed_progressions = []

                    for prog in song_data["progressions"]:
                        transposed_chords = [transpose_chord(chord, semitones) for chord in prog["chords"]]
                        transposed_prog = prog.copy()
                        transposed_prog["chords"] = transposed_chords
                        transposed_progressions.append(transposed_prog)

                    transposed_song = song_data.copy()
                    transposed_song["key"] = transposed_key
                    transposed_song["transposed_by"] = semitones
                    transposed_song["original_key"] = original_key
                    transposed_song["progressions"] = transposed_progressions

                    transposed_name = f"{song_name}_trans_{semitones}"
                    cls.TRANSPOSED_STANDARDS[transposed_name] = transposed_song
                    transposed_count += 1

                except Exception as e:
                    logger.warning(f"Chyba při transpozici {song_name} o {semitones} půltónů: {e}")

        logger.info(f"Inicializováno {transposed_count} transponovaných standardů")

    @classmethod
    def get_song_info(cls, song_name: str) -> Optional[Dict]:
        """
        Získá kompletní informace o písni.

        Args:
            song_name: Název písně

        Returns:
            Optional[Dict]: Informace o písni nebo None pokud není nalezena
        """
        cls._initialize_transposed_standards()  # Zajištění inicializace
        return cls.JAZZ_STANDARDS.get(song_name) or cls.TRANSPOSED_STANDARDS.get(song_name)

    @classmethod
    def get_all_songs(cls) -> List[str]:
        """
        Vrátí seznam všech písní v databázi.

        Returns:
            List[str]: Seřazený seznam názvů písní
        """
        cls._initialize_transposed_standards()
        return sorted(list(cls.JAZZ_STANDARDS.keys()) + list(cls.TRANSPOSED_STANDARDS.keys()))

    @classmethod
    @lru_cache(maxsize=128)
    def find_progressions_by_chord(cls, base_note: str, chord_type: str) -> List[Dict[str, Any]]:
        """
        Hledá progrese, které obsahují daný akord, včetně transponovaných verzí.
        OPRAVENO: Přidáno debugging pro sledování problémů.

        Args:
            base_note: Základní nota akordu
            chord_type: Typ akordu

        Returns:
            List[Dict[str, Any]]: Seznam nalezených progresí s metadaty
        """
        cls._initialize_transposed_standards()
        target_chord = f"{base_note}{chord_type}"
        results = []

        logger.debug(f"Hledám progrese pro akord: {target_chord}")

        # Nejdřív prohledat originály
        for song_name, song_data in cls.JAZZ_STANDARDS.items():
            for prog in song_data["progressions"]:
                if any(c.upper() == target_chord.upper() for c in prog["chords"]):
                    prog_copy = prog.copy()
                    prog_copy['song'] = song_name
                    prog_copy['transposed_by'] = 0  # Označení jako originál
                    prog_copy['transposed_key'] = None
                    prog_copy['original_key'] = song_data["key"]
                    results.append(prog_copy)
                    logger.debug(f"Nalezena originální progrese v {song_name}: {prog['chords']}")

        # Pak transponované
        for song_name, song_data in cls.TRANSPOSED_STANDARDS.items():
            for prog in song_data["progressions"]:
                if any(c.upper() == target_chord.upper() for c in prog["chords"]):
                    prog_copy = prog.copy()
                    prog_copy['song'] = song_name.split("_trans_")[0]  # Původní název písně
                    prog_copy['transposed_by'] = song_data["transposed_by"]
                    prog_copy['transposed_key'] = song_data["key"]
                    prog_copy['original_key'] = song_data["original_key"]
                    results.append(prog_copy)
                    logger.debug(
                        f"Nalezena transponovaná progrese v {song_name}: {prog['chords']} (transpozice +{song_data['transposed_by']})")

        logger.info(f"Nalezeno {len(results)} progresí pro akord {target_chord} (včetně transpozic)")
        return results
