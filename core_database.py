# core_database.py
"""
core_database.py - Databáze jazzových standardů a jejich progresí.
VYLEPŠENO: Bezpečné načítání s try-catch a podporou více JSON souborů.
"""

import logging
import json
import os
from typing import List, Dict, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class JazzStandardsDatabase:
    """
    Databáze jazzových standardů a jejich progresí.
    VYLEPŠENO: Bezpečné načítání s možností mergování více JSON souborů.
    """

    # Konfigurace databázových souborů - lze upravit podle potřeby
    DATABASE_FILES = [
        'database.json',  # Hlavní databáze
        'database_classics.json',  # Klasické standardy (volitelný)
        'database_modern.json',  # Moderní jazz (volitelný)
        'database_exercises.json'  # Cvičení a progrese (volitelný)
    ]

    # Inicializace prázdné databáze
    JAZZ_STANDARDS = {}
    TRANSPOSED_STANDARDS = {}

    # Flag pro sledování stavu inicializace
    _database_loaded = False
    _load_errors = []

    @classmethod
    def _load_database_safely(cls) -> Dict[str, Any]:
        """
        Bezpečné načtení databáze z jednoho nebo více JSON souborů.

        Returns:
            Dict[str, Any]: Sloučená databáze ze všech dostupných souborů
        """
        merged_database = {}
        loaded_files = []
        errors = []

        logger.info(f"Načítám databázi ze souborů: {cls.DATABASE_FILES}")

        for filename in cls.DATABASE_FILES:
            try:
                if not os.path.exists(filename):
                    logger.debug(f"Soubor {filename} neexistuje, přeskakuję")
                    continue

                logger.debug(f"Pokus o načtení souboru: {filename}")

                with open(filename, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                # Validace že se jedná o slovník
                if not isinstance(file_data, dict):
                    raise ValueError(f"Soubor {filename} neobsahuje slovník na root úrovni")

                # Kontrola kolizí názvů písní
                collisions = set(merged_database.keys()) & set(file_data.keys())
                if collisions:
                    logger.warning(f"Kolize názvů písní v {filename}: {collisions} - přepíšu původní")

                # Merge do hlavní databáze
                merged_database.update(file_data)
                loaded_files.append(filename)

                logger.info(f"✅ Načten {filename}: {len(file_data)} písní")

            except FileNotFoundError:
                logger.debug(f"Soubor {filename} nenalezen")

            except json.JSONDecodeError as e:
                error_msg = f"Chyba JSON formátu v {filename}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

            except ValueError as e:
                error_msg = f"Chyba struktury dat v {filename}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

            except Exception as e:
                error_msg = f"Neočekávaná chyba při načítání {filename}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Výsledek načítání
        total_songs = len(merged_database)
        if total_songs > 0:
            logger.info(f"🎵 Databáze úspěšně načtena: {total_songs} písní ze souborů: {loaded_files}")
        else:
            logger.warning("⚠️ Žádná databáze nebyla načtena - použiji fallback")
            merged_database = cls._get_fallback_database()

        if errors:
            logger.warning(f"Chyby při načítání: {len(errors)} problémů")
            cls._load_errors = errors

        return merged_database

    @classmethod
    def _get_fallback_database(cls) -> Dict[str, Any]:
        """
        Základní fallback databáze pro případ selhání načítání.
        Obsahuje minimální sadu progresí pro testování.

        Returns:
            Dict[str, Any]: Minimální databáze s několika základními progresemi
        """
        logger.info("Používám fallback databázi")

        return {
            "ii-V-I Dur základní": {
                "key": "C",
                "difficulty": "Easy",
                "progressions": [
                    {
                        "chords": ["Dm7", "G7", "Cmaj7"],
                        "description": "Základní ii-V-I v C dur"
                    }
                ]
            },
            "ii-V-I Moll základní": {
                "key": "Cm",
                "difficulty": "Easy",
                "progressions": [
                    {
                        "chords": ["Dm7b5", "G7", "Cm7"],
                        "description": "Základní iiØ-V-i v C moll"
                    }
                ]
            },
            "Blues C": {
                "key": "C",
                "difficulty": "Easy",
                "progressions": [
                    {
                        "chords": ["C7", "F7", "C7", "G7", "F7", "C7"],
                        "description": "Základní bluesová progrese"
                    }
                ]
            }
        }

    @classmethod
    def _ensure_database_loaded(cls) -> None:
        """
        Zajistí, že databáze je načtená. Volá se automaticky při prvním přístupu.
        """
        if not cls._database_loaded:
            logger.debug("Inicializuji databázi...")
            cls.JAZZ_STANDARDS = cls._load_database_safely()
            cls._database_loaded = True

    @classmethod
    def _initialize_transposed_standards(cls):
        """
        Vytvoří transponované verze standardů pro všech 11 transpozic.
        OPRAVENO: Používá centrální core_music_theory.py a bezpečné načítání.
        """
        cls._ensure_database_loaded()  # Zajistí načtení databáze

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
            try:
                original_key = song_data.get("key", "C")  # Bezpečný přístup

                if not original_key:
                    logger.warning(f"Píseň {song_name} nemá definovaný key, přeskakuji transpozice")
                    continue

                for semitones in range(1, 12):  # 1 až 11
                    try:
                        # OPRAVA: Rozlišení mezi jednoduchou notou a akordem
                        if len(original_key) == 1 or (len(original_key) == 2 and original_key[1] in ['#', 'b']):
                            # Jednoduchá nota
                            transposed_key = transpose_note(original_key, semitones)
                        else:
                            # Složený akord
                            transposed_key = transpose_chord(original_key, semitones)

                        # Bezpečný přístup k progresím
                        original_progressions = song_data.get("progressions", [])
                        transposed_progressions = []

                        for prog in original_progressions:
                            if not isinstance(prog, dict) or "chords" not in prog:
                                logger.warning(f"Neplatná progrese v {song_name}, přeskakuji")
                                continue

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
                        continue

            except Exception as e:
                logger.error(f"Chyba při zpracování písně {song_name}: {e}")
                continue

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
        cls._ensure_database_loaded()
        cls._initialize_transposed_standards()  # Zajištění inicializace
        return cls.JAZZ_STANDARDS.get(song_name) or cls.TRANSPOSED_STANDARDS.get(song_name)

    @classmethod
    def get_all_songs(cls) -> List[str]:
        """
        Vrátí seznam všech písní v databázi.

        Returns:
            List[str]: Seřazený seznam názvů písní
        """
        cls._ensure_database_loaded()
        cls._initialize_transposed_standards()
        return sorted(list(cls.JAZZ_STANDARDS.keys()) + list(cls.TRANSPOSED_STANDARDS.keys()))

    @classmethod
    @lru_cache(maxsize=128)
    def find_progressions_by_chord(cls, base_note: str, chord_type: str) -> List[Dict[str, Any]]:
        """
        Hledá progrese, které obsahují daný akord, včetně transponovaných verzí.
        OPRAVENO: Přidáno debugging pro sledování problémů a bezpečné načítání.

        Args:
            base_note: Základní nota akordu
            chord_type: Typ akordu

        Returns:
            List[Dict[str, Any]]: Seznam nalezených progresí s metadaty
        """
        cls._ensure_database_loaded()
        cls._initialize_transposed_standards()
        target_chord = f"{base_note}{chord_type}"
        results = []

        logger.debug(f"Hledám progrese pro akord: {target_chord}")

        try:
            # Nejdřív prohledat originály
            for song_name, song_data in cls.JAZZ_STANDARDS.items():
                if not isinstance(song_data, dict):
                    continue

                progressions = song_data.get("progressions", [])
                for prog in progressions:
                    if not isinstance(prog, dict) or "chords" not in prog:
                        continue

                    if any(c.upper() == target_chord.upper() for c in prog["chords"]):
                        prog_copy = prog.copy()
                        prog_copy['song'] = song_name
                        prog_copy['transposed_by'] = 0  # Označení jako originál
                        prog_copy['transposed_key'] = None
                        prog_copy['original_key'] = song_data.get("key", "Unknown")
                        results.append(prog_copy)
                        logger.debug(f"Nalezena originální progrese v {song_name}: {prog['chords']}")

            # Pak transponované
            for song_name, song_data in cls.TRANSPOSED_STANDARDS.items():
                if not isinstance(song_data, dict):
                    continue

                progressions = song_data.get("progressions", [])
                for prog in progressions:
                    if not isinstance(prog, dict) or "chords" not in prog:
                        continue

                    if any(c.upper() == target_chord.upper() for c in prog["chords"]):
                        prog_copy = prog.copy()
                        prog_copy['song'] = song_name.split("_trans_")[0]  # Původní název písně
                        prog_copy['transposed_by'] = song_data.get("transposed_by", 0)
                        prog_copy['transposed_key'] = song_data.get("key", "Unknown")
                        prog_copy['original_key'] = song_data.get("original_key", "Unknown")
                        results.append(prog_copy)
                        logger.debug(
                            f"Nalezena transponovaná progrese v {song_name}: {prog['chords']} "
                            f"(transpozice +{song_data.get('transposed_by', 0)})")

        except Exception as e:
            logger.error(f"Chyba při hledání progresí pro {target_chord}: {e}")

        logger.info(f"Nalezeno {len(results)} progresí pro akord {target_chord} (včetně transpozic)")
        return results

    @classmethod
    def get_database_info(cls) -> Dict[str, Any]:
        """
        Vrátí informace o stavu databáze pro debugging a monitoring.

        Returns:
            Dict[str, Any]: Informace o databázi
        """
        cls._ensure_database_loaded()
        cls._initialize_transposed_standards()

        return {
            "database_loaded": cls._database_loaded,
            "original_songs_count": len(cls.JAZZ_STANDARDS),
            "transposed_songs_count": len(cls.TRANSPOSED_STANDARDS),
            "total_songs": len(cls.JAZZ_STANDARDS) + len(cls.TRANSPOSED_STANDARDS),
            "load_errors_count": len(cls._load_errors),
            "load_errors": cls._load_errors.copy(),
            "configured_files": cls.DATABASE_FILES.copy()
        }

    @classmethod
    def reload_database(cls) -> bool:
        """
        Znovu načte databázi ze souborů. Užitečné pro vývoj nebo aktualizace.

        Returns:
            bool: True pokud reload proběhl úspěšně
        """
        logger.info("Reload databáze...")

        try:
            # Reset stavů
            cls._database_loaded = False
            cls._load_errors.clear()
            cls.JAZZ_STANDARDS.clear()
            cls.TRANSPOSED_STANDARDS.clear()

            # Vyčisti cache
            cls.find_progressions_by_chord.cache_clear()

            # Znovu načti
            cls._ensure_database_loaded()
            cls._initialize_transposed_standards()

            logger.info("✅ Reload databáze dokončen")
            return True

        except Exception as e:
            logger.error(f"❌ Chyba při reload databáze: {e}")
            return False
