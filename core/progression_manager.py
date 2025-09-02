# core/progression_manager.py
"""
core/progression_manager.py - Správa progresí, databáze a žánrové struktury.
Nezávislý modul pro práci s databází jazzových standardů a progresí.
Podporuje dynamické vytváření žánrových kategorií a transpozice.
"""

import logging
import json
import os
from typing import List, Dict, Optional, Any
from functools import lru_cache
from core.music_theory import transpose_chord

logger = logging.getLogger(__name__)


class ProgressionManager:
    """
    Správce progresí s podporou žánrové struktury a transpozic.
    Nezávislý na GUI - může být použit v jiných aplikacích.
    """

    def __init__(self, database_files: List[str] = None):
        """
        Inicializuje ProgressionManager s možností specifikovat databázové soubory.

        Args:
            database_files: Seznam JSON souborů s databází (None = použije výchozí)
        """
        # Konfigurace databázových souborů
        self.database_files = database_files or [
            'database.json',
            'database_classics.json',
            'database_modern.json',
            'database_exercises.json'
        ]

        # Inicializace prázdných databází
        self.original_database: Dict[str, Dict] = {}
        self.transposed_database: Dict[str, Dict] = {}
        self.genres_cache: Dict[str, List[str]] = {}

        # Flags pro sledování stavu
        self._database_loaded = False
        self._transposed_initialized = False
        self._load_errors: List[str] = []

    def load_database(self, force_reload: bool = False) -> bool:
        """
        Načte databázi ze všech dostupných JSON souborů.

        Args:
            force_reload: Pokud True, znovu načte databázi i když už je načtena

        Returns:
            bool: True při úspěšném načtení
        """
        if self._database_loaded and not force_reload:
            return True

        logger.info("Načítám databázi progresí...")
        self.original_database.clear()
        self._load_errors.clear()

        loaded_files = []
        total_songs = 0

        for filename in self.database_files:
            try:
                if not os.path.exists(filename):
                    logger.debug(f"Soubor {filename} neexistuje, přeskakuji")
                    continue

                logger.debug(f"Načítám soubor: {filename}")

                with open(filename, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                # Validace že se jedná o slovník
                if not isinstance(file_data, dict):
                    raise ValueError(f"Soubor {filename} neobsahuje slovník na root úrovni")

                # Kontrola kolizí názvů písní
                collisions = set(self.original_database.keys()) & set(file_data.keys())
                if collisions:
                    logger.warning(f"Kolize názvů písní v {filename}: {collisions} - přepíšu původní")

                # Merge do hlavní databáze
                self.original_database.update(file_data)
                loaded_files.append(filename)
                total_songs += len(file_data)

                logger.info(f"Načten {filename}: {len(file_data)} písní")

            except FileNotFoundError:
                logger.debug(f"Soubor {filename} nenalezen")

            except json.JSONDecodeError as e:
                error_msg = f"Chyba JSON formátu v {filename}: {e}"
                logger.error(error_msg)
                self._load_errors.append(error_msg)

            except Exception as e:
                error_msg = f"Neočekávaná chyba při načítání {filename}: {e}"
                logger.error(error_msg)
                self._load_errors.append(error_msg)

        # Výsledek načítání
        if self.original_database:
            logger.info(f"Databáze úspěšně načtena: {len(self.original_database)} písní ze souborů: {loaded_files}")
            self._database_loaded = True

            # Vyčistí cache po změně databáze
            self._clear_caches()
            return True
        else:
            logger.warning("Žádná databáze nebyla načtena - použiji fallback")
            self.original_database = self._get_fallback_database()
            self._database_loaded = True
            return False

    def _get_fallback_database(self) -> Dict[str, Dict]:
        """
        Základní fallback databáze pro případ selhání načítání.

        Returns:
            Dict[str, Dict]: Minimální databáze s několika základními progresemi
        """
        logger.info("Používám fallback databázi")

        return {
            "ii-V-I Dur základní": {
                "genre": "jazz-progressions",
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
                "genre": "jazz-progressions",
                "key": "Cm",
                "difficulty": "Easy",
                "progressions": [
                    {
                        "chords": ["Dm7b5", "G7", "Cm7"],
                        "description": "Základní iiø-V-i v C moll"
                    }
                ]
            },
            "Blues C": {
                "genre": "blues",
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

    def initialize_transpositions(self) -> None:
        """
        Vytvoří transponované verze všech písní pro všech 11 transpozic.
        Volá se automaticky při prvním přístupu k transponovaným datům.
        """
        if self._transposed_initialized:
            return

        if not self._database_loaded:
            self.load_database()

        logger.info("Inicializuji transpozice všech písní...")
        self.transposed_database.clear()

        transposed_count = 0
        for song_name, song_data in self.original_database.items():
            try:
                original_key = song_data.get("key", "C")

                if not original_key:
                    logger.warning(f"Píseň {song_name} nemá definovaný key, přeskakuji transpozice")
                    continue

                for semitones in range(1, 12):  # 1 až 11 půltónů
                    try:
                        # Transpozice klíče
                        if len(original_key) <= 2 and not any(c in original_key for c in ['maj', 'min', 'm7']):
                            # Jednoduchá nota
                            from core.music_theory import transpose_note
                            transposed_key = transpose_note(original_key, semitones)
                        else:
                            # Složený akord
                            transposed_key = transpose_chord(original_key, semitones)

                        # Transpozice progresí
                        transposed_progressions = []
                        for prog in song_data.get("progressions", []):
                            if not isinstance(prog, dict) or "chords" not in prog:
                                continue

                            transposed_chords = [transpose_chord(chord, semitones) for chord in prog["chords"]]
                            transposed_prog = prog.copy()
                            transposed_prog["chords"] = transposed_chords
                            transposed_progressions.append(transposed_prog)

                        # Vytvoření transponované písně
                        transposed_song = song_data.copy()
                        transposed_song["key"] = transposed_key
                        transposed_song["transposed_by"] = semitones
                        transposed_song["original_key"] = original_key
                        transposed_song["progressions"] = transposed_progressions

                        transposed_name = f"{song_name}_trans_{semitones}"
                        self.transposed_database[transposed_name] = transposed_song
                        transposed_count += 1

                    except Exception as e:
                        logger.warning(f"Chyba při transpozici {song_name} o {semitones} půltónů: {e}")
                        continue

            except Exception as e:
                logger.error(f"Chyba při zpracování písně {song_name}: {e}")
                continue

        self._transposed_initialized = True
        logger.info(f"Inicializováno {transposed_count} transponovaných písní")

    def get_all_songs(self) -> List[str]:
        """
        Vrátí seznam všech písní včetně transponovaných verzí.

        Returns:
            List[str]: Seřazený seznam názvů písní
        """
        if not self._database_loaded:
            self.load_database()

        if not self._transposed_initialized:
            self.initialize_transpositions()

        all_songs = list(self.original_database.keys()) + list(self.transposed_database.keys())
        return sorted(all_songs)

    def get_song_info(self, song_name: str) -> Optional[Dict]:
        """
        Získá kompletní informace o písni.

        Args:
            song_name: Název písně

        Returns:
            Optional[Dict]: Informace o písni nebo None pokud není nalezena
        """
        if not self._database_loaded:
            self.load_database()

        # Nejdřív hledá v originálech
        if song_name in self.original_database:
            return self.original_database[song_name]

        # Pak v transpozicích
        if not self._transposed_initialized:
            self.initialize_transpositions()

        return self.transposed_database.get(song_name)

    @lru_cache(maxsize=256)
    def find_progressions_by_chord(self, base_note: str, chord_type: str) -> List[Dict[str, Any]]:
        """
        Hledá progrese, které obsahují daný akord, včetně transponovaných verzí.
        Používá cache pro rychlejší opakované dotazy.

        Args:
            base_note: Základní nota akordu
            chord_type: Typ akordu

        Returns:
            List[Dict[str, Any]]: Seznam nalezených progresí s metadaty
        """
        if not self._database_loaded:
            self.load_database()

        target_chord = f"{base_note}{chord_type}".upper()
        results = []

        logger.debug(f"Hledám progrese pro akord: {target_chord}")

        # Hledání v originálních písních
        for song_name, song_data in self.original_database.items():
            results.extend(self._search_progressions_in_song(
                song_name, song_data, target_chord, is_transposed=False
            ))

        # Hledání v transponovaných verzích
        if not self._transposed_initialized:
            self.initialize_transpositions()

        for song_name, song_data in self.transposed_database.items():
            results.extend(self._search_progressions_in_song(
                song_name, song_data, target_chord, is_transposed=True
            ))

        logger.info(f"Nalezeno {len(results)} progresí pro akord {target_chord}")
        return results

    def _search_progressions_in_song(self, song_name: str, song_data: Dict,
                                     target_chord: str, is_transposed: bool) -> List[Dict[str, Any]]:
        """
        Hledá progrese obsahující cílový akord v konkrétní písni.

        Args:
            song_name: Název písně
            song_data: Data písně
            target_chord: Hledaný akord (uppercase)
            is_transposed: Zda se jedná o transponovanou verzi

        Returns:
            List[Dict[str, Any]]: Seznam nalezených progresí
        """
        results = []

        if not isinstance(song_data, dict):
            return results

        progressions = song_data.get("progressions", [])
        for prog in progressions:
            if not isinstance(prog, dict) or "chords" not in prog:
                continue

            # Hledá akord v progrese (case-insensitive)
            if any(chord.upper() == target_chord for chord in prog["chords"]):
                prog_copy = prog.copy()

                if is_transposed:
                    # Transponovaná píseň
                    original_name = song_name.split("_trans_")[0]
                    prog_copy['song'] = original_name
                    prog_copy['transposed_by'] = song_data.get("transposed_by", 0)
                    prog_copy['transposed_key'] = song_data.get("key", "Unknown")
                    prog_copy['original_key'] = song_data.get("original_key", "Unknown")
                else:
                    # Originální píseň
                    prog_copy['song'] = song_name
                    prog_copy['transposed_by'] = 0
                    prog_copy['transposed_key'] = None
                    prog_copy['original_key'] = song_data.get("key", "Unknown")

                # Přidá žánr pokud existuje
                prog_copy['genre'] = song_data.get("genre", "unknown")

                results.append(prog_copy)

                logger.debug(f"Nalezena progrese v {song_name}: {prog['chords']}")

        return results

    def get_genres(self) -> Dict[str, List[str]]:
        """
        Vrátí slovník žánrů s písněmi, které do nich patří.
        Dynamicky vytváří kategorie na základě obsahu databáze.

        Returns:
            Dict[str, List[str]]: {"žánr": ["píseň1", "píseň2", ...]}
        """
        if self.genres_cache:
            return self.genres_cache

        if not self._database_loaded:
            self.load_database()

        genres = {}

        # Projde všechny originální písně
        for song_name, song_data in self.original_database.items():
            genre = song_data.get("genre", "unknown")

            if genre not in genres:
                genres[genre] = []
            genres[genre].append(song_name)

        # Seřadí písně v každém žánru
        for genre in genres:
            genres[genre].sort()

        # Seřadí žánry podle názvu
        self.genres_cache = dict(sorted(genres.items()))

        logger.info(f"Nalezeno {len(self.genres_cache)} žánrů: {list(self.genres_cache.keys())}")
        return self.genres_cache

    def get_songs_by_genre(self, genre: str) -> List[str]:
        """
        Vrátí seznam písní konkrétního žánru.

        Args:
            genre: Název žánru

        Returns:
            List[str]: Seznam písní daného žánru
        """
        genres = self.get_genres()
        return genres.get(genre, [])

    def get_progression_by_song(self, song_name: str) -> List[str]:
        """
        Vrátí všechny akordy z všech progresí dané písně jako jeden seznam.

        Args:
            song_name: Název písně

        Returns:
            List[str]: Seznam všech akordů z písně
        """
        song_info = self.get_song_info(song_name)
        if not song_info:
            return []

        all_chords = []
        for prog in song_info.get("progressions", []):
            if isinstance(prog, dict) and "chords" in prog:
                all_chords.extend(prog["chords"])

        return all_chords

    def export_progressions_by_genre(self, genre: str) -> Dict[str, Any]:
        """
        Exportuje všechny progrese konkrétního žánru.

        Args:
            genre: Název žánru

        Returns:
            Dict[str, Any]: Strukturovaná data pro export
        """
        songs = self.get_songs_by_genre(genre)
        export_data = {
            "genre": genre,
            "songs_count": len(songs),
            "songs": {}
        }

        for song_name in songs:
            song_info = self.get_song_info(song_name)
            if song_info:
                export_data["songs"][song_name] = {
                    "key": song_info.get("key", "Unknown"),
                    "composer": song_info.get("composer", "Unknown"),
                    "year": song_info.get("year", "Unknown"),
                    "difficulty": song_info.get("difficulty", "Unknown"),
                    "progressions": song_info.get("progressions", [])
                }

        return export_data

    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Vrátí statistiky o databázi pro monitoring a debugging.

        Returns:
            Dict[str, Any]: Statistiky databáze
        """
        if not self._database_loaded:
            self.load_database()

        if not self._transposed_initialized:
            self.initialize_transpositions()

        genres = self.get_genres()

        return {
            "database_loaded": self._database_loaded,
            "transposed_initialized": self._transposed_initialized,
            "original_songs_count": len(self.original_database),
            "transposed_songs_count": len(self.transposed_database),
            "total_songs": len(self.original_database) + len(self.transposed_database),
            "genres_count": len(genres),
            "genres": list(genres.keys()),
            "songs_per_genre": {genre: len(songs) for genre, songs in genres.items()},
            "load_errors_count": len(self._load_errors),
            "load_errors": self._load_errors.copy(),
            "configured_files": self.database_files.copy()
        }

    def reload_database(self) -> bool:
        """
        Znovu načte databázi ze souborů.

        Returns:
            bool: True pokud reload proběhl úspěšně
        """
        logger.info("Reload databáze...")

        try:
            # Reset stavů
            self._database_loaded = False
            self._transposed_initialized = False
            self._load_errors.clear()
            self.original_database.clear()
            self.transposed_database.clear()

            # Vyčisti cache
            self._clear_caches()

            # Znovu načti
            success = self.load_database()
            if success:
                self.initialize_transpositions()

            logger.info("Reload databáze dokončen")
            return success

        except Exception as e:
            logger.error(f"Chyba při reload databáze: {e}")
            return False

    def _clear_caches(self) -> None:
        """Vyčistí všechny cache."""
        self.genres_cache.clear()
        self.find_progressions_by_chord.cache_clear()
        logger.debug("Cache vyčištěna")


# Utility funkce pro práci s progresemi
def analyze_progression_complexity(chords: List[str]) -> Dict[str, Any]:
    """
    Analyzuje složitost progrese na základě použitých akordů.

    Args:
        chords: Seznam akordů v progresi

    Returns:
        Dict[str, Any]: Analýza složitosti
    """
    from core.music_theory import parse_chord_name

    if not chords:
        return {"complexity": "empty", "score": 0}

    unique_chords = list(set(chords))
    chord_types = []

    try:
        for chord in unique_chords:
            _, chord_type = parse_chord_name(chord)
            chord_types.append(chord_type)
    except:
        pass

    # Jednoduché hodnocení složitosti
    complexity_score = 0
    complexity_score += len(unique_chords)  # Počet různých akordů

    # Penalizace za složité typy
    for chord_type in chord_types:
        if any(marker in chord_type for marker in ['b9', '#9', 'b13', '#11']):
            complexity_score += 3
        elif any(marker in chord_type for marker in ['9', '11', '13']):
            complexity_score += 2
        elif any(marker in chord_type for marker in ['7', 'm7', 'maj7']):
            complexity_score += 1

    if complexity_score <= 5:
        complexity = "easy"
    elif complexity_score <= 10:
        complexity = "medium"
    elif complexity_score <= 15:
        complexity = "hard"
    else:
        complexity = "expert"

    return {
        "complexity": complexity,
        "score": complexity_score,
        "unique_chords_count": len(unique_chords),
        "total_chords_count": len(chords),
        "chord_types": list(set(chord_types))
    }


if __name__ == "__main__":
    # Jednoduché testování ProgressionManager
    print("=== Test ProgressionManager ===")

    # Test inicializace
    print("\n1. Inicializace:")
    manager = ProgressionManager()
    success = manager.load_database()
    print(f"Databáze načtena: {success}")

    # Test statistik
    print("\n2. Statistiky databáze:")
    stats = manager.get_database_statistics()
    print(f"Originální písně: {stats['original_songs_count']}")
    print(f"Transponované písně: {stats['transposed_songs_count']}")
    print(f"Žánry: {stats['genres']}")

    # Test žánrů
    print("\n3. Žánry:")
    genres = manager.get_genres()
    for genre, songs in genres.items():
        print(f"{genre}: {len(songs)} písní")
        if songs:
            print(f"  Příklad: {songs[0]}")

    # Test hledání progresí
    print("\n4. Test hledání progresí:")
    progressions = manager.find_progressions_by_chord("C", "maj7")
    print(f"Progrese s Cmaj7: {len(progressions)}")
    if progressions:
        first = progressions[0]
        print(f"  Příklad: {first.get('song', 'Unknown')} - {first.get('chords', [])}")

    # Test analýzy složitosti
    print("\n5. Test analýzy složitosti:")
    test_progression = ["Cmaj7", "Am7", "Dm7", "G7"]
    analysis = analyze_progression_complexity(test_progression)
    print(f"Progrese: {test_progression}")
    print(f"Složitost: {analysis['complexity']} (score: {analysis['score']})")
