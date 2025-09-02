# core_database.py
"""
core_database.py - Databáze jazzových standardů a jejich progresí.
OPRAVENO: Používá centrální core_music_theory.py pro transpozice.
"""

import logging
from typing import List, Dict, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class JazzStandardsDatabase:
    """Databáze jazzových standardů a jejich progresí."""

    JAZZ_STANDARDS = {
        # --- Classic Easy / Medium ---
        "Fly Me to the Moon": {
            "key": "C", "composer": "Bart Howard", "year": 1954, "difficulty": "Easy - Medium",
            "progressions": [
                {"chords": ["Am7", "Dm7", "G7", "Cmaj7"], "description": "vi-ii-V-I hlavní progrese"},
                {"chords": ["Fmaj7", "Bm7b5", "E7", "Am7"], "description": "IV-viiØ-III7-vi modulace do vi"}
            ]
        },
        "Autumn Leaves": {
            "key": "Gm", "composer": "Joseph Kosma", "year": 1945, "difficulty": "Easy-Medium",
            "progressions": [
                {"chords": ["Cm7", "F7", "Bbmaj7", "Ebmaj7"], "description": "ii-V-I-IV v Bb dur"},
                {"chords": ["Am7b5", "D7", "Gm"], "description": "iiØ-V-i v G moll"}
            ]
        },
        "Summertime": {
            "key": "Am", "composer": "George Gershwin", "year": 1935, "difficulty": "Easy",
            "progressions": [
                {"chords": ["Am", "E7", "Am", "E7"], "description": "i-V-i"},
                {"chords": ["Dm7", "G7", "C", "F"], "description": "iv-VII7-III-VI in relative major"}
            ]
        },
        "Georgia (Original)": {
            "key": "F", "composer": "Hoagy Carmichael", "year": 1930, "difficulty": "Medium",
            "progressions": [
                {"chords": ["F", "Am7", "Dm7", "G7", "C7", "F"], "description": "Hlavní progrese s vi-ii-V-I modulací"},
                {"chords": ["Bbmaj7", "Bdim7", "C7", "F"], "description": "IV-#iio7-V-I turnaround"}
            ]
        },

        "Georgia (Ray Charles Piano Cover)": {
            "key": "G", "composer": "Hoagy Carmichael", "year": 1930, "difficulty": "Medium",
            "progressions": [
                {"chords": ["G", "C7", "C", "Cm6", "Em", "A7", "D7", "D", "G", "B7", "Em", "G7", "C#m"],
                 "description": "Dle Chordify"},
                {"chords": ["G", "Bm7", "Em7", "A7", "D7", "G"], "description": "Hlavní progrese s vi-ii-V-I modulací"},
                {"chords": ["C", "C#dim7", "D7", "G"], "description": "IV-#ivo7-V-I turnaround"}
            ]
        },

        # --- Medium / Bebop ---
        "All The Things You Are": {
            "key": "Ab", "composer": "Jerome Kern", "year": 1939, "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["Fm7", "Bbm7", "Eb7", "Abmaj7"], "description": "vi-ii-V-I v Ab dur"},
                {"chords": ["Dbmaj7", "G7", "Cmaj7"], "description": "IV-VII7-III modulace do C dur"},
                {"chords": ["Am7", "D7", "Gmaj7"], "description": "ii-V-I v G dur (bridge)"}
            ]
        },
        "Blue Bossa": {
            "key": "Cm", "composer": "Kenny Dorham", "year": 1963, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Cm7", "Fm7", "Dm7b5", "G7", "Cm7"], "description": "i-iv-iiØ-V-i v C moll"},
                {"chords": ["Ebm7", "Ab7", "Dbmaj7"], "description": "ii-V-I v Db dur"}
            ]
        },
        "Take The A Train": {
            "key": "C", "composer": "Billy Strayhorn", "year": 1939, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Cmaj7", "Cmaj7", "D7", "D7"], "description": "Bridge modulace"},
                {"chords": ["Dm7", "G7", "Cmaj7", "A7"], "description": "ii-V-I-VI7 turnaround"}
            ]
        },
        "Satin Doll": {
            "key": "C", "composer": "Duke Ellington", "year": 1953, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Dm7", "G7", "Dm7", "G7"], "description": "Opakující se ii-V"},
                {"chords": ["Em7", "A7", "Dm7", "G7"], "description": "iii-VI7-ii-V prodloužení"}
            ]
        },

        # --- Advanced / Modern Jazz ---
        "Giant Steps": {
            "key": "B", "composer": "John Coltrane", "year": 1959, "difficulty": "Very Advanced",
            "progressions": [
                {"chords": ["Bmaj7", "D7", "Gmaj7", "Bb7", "Ebmaj7"],
                 "description": "Coltrane changes - terciové vztahy"},
                {"chords": ["Am7", "D7", "Gmaj7"], "description": "ii-V-I v G dur"},
                {"chords": ["C#m7", "F#7", "Bmaj7"], "description": "ii-V-I v B dur"}
            ]
        },
        "Stella by Starlight": {
            "key": "Bb", "composer": "Victor Young", "year": 1944, "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["Em7b5", "A7b9", "Cm7", "F7"], "description": "Unresolved iiØ-V leading to ii-V"},
                {"chords": ["Bbmaj7", "Bdim7", "Cm7", "F7"], "description": "I - #io7 - ii-V turnaround"},
                {"chords": ["Dm7", "G7", "Cm7", "F7"], "description": "ii-V-ii-V cycle"}
            ]
        },
        "My Funny Valentine": {
            "key": "Cm", "composer": "Richard Rodgers", "year": 1937, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Cm", "Cm(maj7)", "Cm7", "Cm6"], "description": "Descending bass line in minor i chord"},
                {"chords": ["Abmaj7", "Fm7", "Dm7b5", "G7"], "description": "VI-ii-vØ-V progression"},
                {"chords": ["Cm", "Eb7", "Abmaj7", "D7b9"], "description": "i-III-VI-II7 turnaround"}
            ]
        },

        # --- Bill Evans ---
        "Waltz for Debby": {
            "key": "Bb", "composer": "Bill Evans", "year": 1961, "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["Bbmaj7", "Gm7", "C7", "Fmaj7"], "description": "Lyrická progrese s ii-V-I"},
                {"chords": ["Ebmaj7", "Am7b5", "D7", "Gm7"], "description": "Modulační část s chromatickou přechodovou"}
            ]
        },
        "Peace Piece": {
            "key": "C", "composer": "Bill Evans", "year": 1958, "difficulty": "Advanced",
            "progressions": [
                {"chords": ["Cmaj7", "G9sus4", "Am7", "Fmaj7"], "description": "Volná improvizační sekvence"},
                {"chords": ["Dm7", "G13", "Cmaj7"], "description": "ii-V-I loop"}
            ]
        },
        "Blue in Green": {
            "key": "Db", "composer": "Bill Evans", "year": 1959, "difficulty": "Advanced",
            "progressions": [
                {"chords": ["Dbmaj7", "Em7b5", "A7b9", "Dbmaj7"], "description": "Modulační chromatika"},
                {"chords": ["Gm7", "C7", "Fmaj7"], "description": "ii-V-I loop"}
            ]
        },

        # --- Michel Petrucciani ---
        "Looking Up": {
            "key": "C", "composer": "Michel Petrucciani", "year": 1980, "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["Cmaj7", "Em7", "A7", "Dm7", "G7"], "description": "Základní ii-V-I a modulační postup"},
                {"chords": ["Fmaj7", "Fm7", "Cmaj7"], "description": "Plný modulující bridge"}
            ]
        },
        "Brazilian Like": {
            "key": "D", "composer": "Michel Petrucciani", "year": 1982, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Dmaj7", "G7", "Cmaj7", "F#7"], "description": "Typický bossa nova postup"},
                {"chords": ["Bm7", "E7", "Amaj7"], "description": "ii-V-I v A dur"}
            ]
        },
        "Little Peace in C For You": {
            "key": "C", "composer": "Michel Petrucciani", "year": 1985, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Cmaj7", "Am7", "Dm7", "G7", "Cmaj7"], "description": "Klasický jazzový ii-V-I loop"},
                {"chords": ["Fmaj7", "Em7", "A7", "Dm7"], "description": "Modulační sekvence s chromatickými přechody"}
            ]
        },

        # --- Blues / Bebop ---
        "C Jam Blues": {
            "key": "C", "composer": "Duke Ellington", "year": 1942, "difficulty": "Easy-Medium",
            "progressions": [
                {"chords": ["C7", "F7", "C7", "G7"], "description": "12-taktový bluesový základ"}
            ]
        },
        "Now's the Time": {
            "key": "F", "composer": "Charlie Parker", "year": 1945, "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["F7", "Bb7", "F7", "C7"], "description": "Bebop bluesová sekvence"}
            ]
        },

        # --- ii-V-I Variace ---
        "ii-V-I Dur základní": {
            "key": "C", "difficulty": "Easy",
            "progressions": [
                {"chords": ["Dm7", "G7", "Cmaj7"], "description": "Základní ii-V-I v C dur"}
            ]
        },
        "ii-V-I Moll základní": {
            "key": "Cm", "difficulty": "Easy",
            "progressions": [
                {"chords": ["Dm7b5", "G7", "Cm7"], "description": "Základní iiØ-V-i v C moll"}
            ]
        },
        "ii-V-I Dur s rozšířenými akordy": {
            "key": "C", "difficulty": "Medium",
            "progressions": [
                {"chords": ["Dm9", "G13", "Cmaj9"], "description": "ii-V-I s přidanými barvami a rozšířenými voicings"}
            ]
        },
        "ii-V-I Moll s alterovaným dominantem": {
            "key": "Cm", "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["Dm7b5", "G7b9#11", "Cm7"], "description": "iiØ-V-i s alterovaným dominantem"}
            ]
        },
        "ii-V-I Dur chromatická přechodová": {
            "key": "C", "difficulty": "Advanced",
            "progressions": [
                {"chords": ["Dm7", "D7", "G7", "Cmaj7"], "description": "Chromatická progrese s II7 do V7"}
            ]
        },
        "ii-V-I Moll modulující": {
            "key": "Cm", "difficulty": "Advanced",
            "progressions": [
                {"chords": ["Am7b5", "D7b9", "Gm7", "C7", "Fm7"], "description": "iiØ-V-i modulace do F moll"}
            ]
        },
        "ii-V-I s rozšířenými modulacemi": {
            "key": "C", "difficulty": "Very Advanced",
            "progressions": [
                {"chords": ["Dm7", "G7", "E7", "Amaj7", "D7", "Gmaj7"],
                 "description": "Sekvence ii-V modulující po terciích, Coltrane-style"}
            ]
        },
        # --- Lidové ---
        "Ó řebíčku zahradnický": {
            "key": "D", "difficulty": "Simple",
            "progressions": [
                {"chords": ["D", "Bm", "Em", "A7", "Em", "A7", "D", "A7", "D"],
                 "description": "Lidová píseň s jednoduchými akordy"}
            ]
        }

    }

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
