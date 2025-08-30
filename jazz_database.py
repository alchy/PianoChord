# jazz_database.py
"""
jazz_database.py - Databaze jazzovych standardu a jejich progresi.
"""
from typing import List, Dict, Optional, Any
from functools import lru_cache
from constants import transpose_chord  # NOVÉ: Import transpozice

# --- DEBUG ---
DEBUG = True


class JazzStandardsDatabase:
    """Databaze jazzovych standardu a jejich progresi."""

    JAZZ_STANDARDS = {
        "Fly Me to the Moon": {
            "key": "C", "composer": "Bart Howard", "year": 1954, "difficulty": "Easy-Medium",
            "progressions": [
                {"chords": ["Am7", "Dm7", "G7", "Cmaj7"], "description": "vi-ii-V-I hlavní progrese"},
                {"chords": ["Fmaj7", "Bm7b5", "E7", "Am7"], "description": "IV-viiø-III7-vi modulace do vi"},
            ]
        },
        "Autumn Leaves": {
            "key": "Gm", "composer": "Joseph Kosma", "year": 1945, "difficulty": "Easy-Medium",
            "progressions": [
                {"chords": ["Cm7", "F7", "Bbmaj7", "Ebmaj7"], "description": "ii-V-I-IV v Bb dur (relativní dur)"},
                {"chords": ["Am7b5", "D7", "Gm"], "description": "iiø-V-i v G moll"},
            ]
        },
        "All The Things You Are": {
            "key": "Ab", "composer": "Jerome Kern", "year": 1939, "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["Fm7", "Bbm7", "Eb7", "Abmaj7"], "description": "vi-ii-V-I v Ab dur"},
                {"chords": ["Dbmaj7", "G7", "Cmaj7"], "description": "IV-VII7-III modulace do C dur"},
                {"chords": ["Am7", "D7", "Gmaj7"], "description": "ii-V-I v G dur (bridge)"},
            ]
        },
        "Blue Bossa": {
            "key": "Cm", "composer": "Kenny Dorham", "year": 1963, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Cm7", "Fm7", "Dm7b5", "G7", "Cm7"], "description": "i-iv-iiø-V-i v C moll"},
                {"chords": ["Ebm7", "Ab7", "Dbmaj7"], "description": "ii-V-I v Db dur"},
            ]
        },
        "Giant Steps": {
            "key": "B", "composer": "John Coltrane", "year": 1959, "difficulty": "Very Advanced",
            "progressions": [
                {"chords": ["Bmaj7", "D7", "Gmaj7", "Bb7", "Ebmaj7"],
                 "description": "Coltrane changes - terciové vztahy"},
                {"chords": ["Am7", "D7", "Gmaj7"], "description": "ii-V-I v G dur"},
                {"chords": ["C#m7", "F#7", "Bmaj7"], "description": "ii-V-I v B dur"},
            ]
        },
        "Take The A Train": {
            "key": "C", "composer": "Billy Strayhorn", "year": 1939, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Cmaj7", "Cmaj7", "D7", "D7"], "description": "Bridge modulace"},
                {"chords": ["Dm7", "G7", "Cmaj7", "A7"], "description": "ii-V-I-VI7 turnaround"},
            ]
        },
        "Satin Doll": {
            "key": "C", "composer": "Duke Ellington", "year": 1953, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Dm7", "G7", "Dm7", "G7"], "description": "Opakující se ii-V"},
                {"chords": ["Em7", "A7", "Dm7", "G7"], "description": "iii-VI7-ii-V prodloužení"},
            ]
        },
        "Stella by Starlight": {
            "key": "Bb", "composer": "Victor Young", "year": 1944, "difficulty": "Medium-Advanced",
            "progressions": [
                {"chords": ["Em7b5", "A7b9", "Cm7", "F7"], "description": "Unresolved iiø-V leading to ii-V"},
                {"chords": ["Bbmaj7", "Bdim7", "Cm7", "F7"], "description": "I - #io7 - ii-V turnaround"},
                {"chords": ["Dm7", "G7", "Cm7", "F7"], "description": "ii-V-ii-V cycle"}
            ]
        },
        "My Funny Valentine": {
            "key": "Cm", "composer": "Richard Rodgers", "year": 1937, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Cm", "Cm(maj7)", "Cm7", "Cm6"], "description": "Descending bass line in minor i chord"},
                {"chords": ["Abmaj7", "Fm7", "Dm7b5", "G7"], "description": "VI-ii-vø-V progression"},
                {"chords": ["Cm", "Eb7", "Abmaj7", "D7b9"], "description": "i-III-VI-II7 turnaround"}
            ]
        },
        "Summertime": {
            "key": "Am", "composer": "George Gershwin", "year": 1935, "difficulty": "Easy",
            "progressions": [
                {"chords": ["Am", "E7", "Am", "E7"], "description": "Basic i-V-i progression"},
                {"chords": ["Dm7", "G7", "C", "F"], "description": "iv-VII7-III-VI in relative major"},
                {"chords": ["Am", "Dm", "Am", "E7"], "description": "i-iv-i-V cycle"}
            ]
        },
        "Body and Soul": {
            "key": "Db", "composer": "Johnny Green", "year": 1930, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Ebmaj7", "Ab7", "Dbmaj7", "Dbmaj7"], "description": "ii-V-I in Db maj"},
                {"chords": ["Ebm7", "Ab7", "Dbmaj7", "B7"], "description": "ii-V-I with turnaround to bridge"},
                {"chords": ["Bbm7", "Eb7", "Abmaj7", "G7"], "description": "Bridge: ii-V-I in Ab, then V/ii"}
            ]
        },
        "Night and Day": {
            "key": "Eb", "composer": "Cole Porter", "year": 1932, "difficulty": "Medium",
            "progressions": [
                {"chords": ["Eb", "Fm7", "Bb7", "Eb"], "description": "I-ii-V-I basic progression"},
                {"chords": ["Gbm7b5", "Fm7", "Em7", "Ebm7"],
                 "description": "Chromatic descending half-diminished chords"},
                {"chords": ["Dm7", "G7", "Cm7", "F7"], "description": "Bridge: ii-V-ii-V in Bb"}
            ]
        },
        "Georgia (On My Mind)": {
            "key": "F", "composer": "Hoagy Carmichael", "year": 1930, "difficulty": "Medium",
            "progressions": [
                {"chords": ["F", "Am7", "Dm7", "G7", "C7", "F"], "description": "Hlavní progrese s vi-ii-V-I modulací"},
                {"chords": ["Bbmaj7", "Bdim7", "C7", "F"], "description": "IV-#iio7-V-I turnaround"}
            ]
        },
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
        "ii-V-I Dur základní": {
            "key": "C", "difficulty": "Easy",
            "progressions": [
                {"chords": ["Dm7", "G7", "Cmaj7"], "description": "Základní ii-V-I v C dur"}
            ]
        },
        "ii-V-I Moll základní": {
            "key": "Cm", "difficulty": "Easy",
            "progressions": [
                {"chords": ["Dm7b5", "G7", "Cm7"], "description": "Základní iiø-V-i v C moll"}
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
                {"chords": ["Dm7b5", "G7b9#11", "Cm7"], "description": "iiø-V-i s alterovaným dominantem"}
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
                {"chords": ["Am7b5", "D7b9", "Gm7", "C7", "Fm7"], "description": "iiø-V-i modulace do F moll"}
            ]
        },
        "ii-V-I s rozšířenými modulacemi": {
            "key": "C", "difficulty": "Very Advanced",
            "progressions": [
                {"chords": ["Dm7", "G7", "E7", "Amaj7", "D7", "Gmaj7"],
                 "description": "Sekvence ii-V modulující po terciích, Coltrane-style"}
            ]
        }
    }

    # NOVÉ: Slovník pro transponované verze (vytvořen při inicializaci)
    TRANSPOSED_STANDARDS = {}

    @classmethod
    def _initialize_transposed_standards(cls):
        """Vytvoří transponované verze standardů pro všechny 11 transpozic."""
        if cls.TRANSPOSED_STANDARDS:  # Už inicializováno
            return
        from constants import transpose_note  # Import zde pro vyhnutí se cyklům
        for song_name, song_data in cls.JAZZ_STANDARDS.items():
            original_key = song_data["key"]
            for semitones in range(1, 12):  # 1 až 11
                transposed_key = transpose_note(original_key, semitones) if len(original_key) == 1 else transpose_chord(original_key, semitones)
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
        if DEBUG:
            print(f"Inicializováno {len(cls.TRANSPOSED_STANDARDS)} transponovaných standardů.")

    @classmethod
    def __init__(cls):
        cls._initialize_transposed_standards()  # NOVÉ: Inicializace při prvním použití třídy

    @classmethod
    def get_song_info(cls, song_name: str) -> Optional[Dict]:
        """Ziska kompletni informace o pisni."""
        cls._initialize_transposed_standards()  # Zajištění inicializace
        return cls.JAZZ_STANDARDS.get(song_name) or cls.TRANSPOSED_STANDARDS.get(song_name)

    @classmethod
    def get_all_songs(cls) -> List[str]:
        """Vrati seznam vsech pisni v databazi."""
        cls._initialize_transposed_standards()
        return sorted(list(cls.JAZZ_STANDARDS.keys()) + list(cls.TRANSPOSED_STANDARDS.keys()))

    @classmethod
    @lru_cache(maxsize=128)
    def find_progressions_by_chord(cls, base_note: str, chord_type: str) -> List[Dict[str, Any]]:
        """Hleda progrese, ktere obsahuji dany akord, včetně transponovaných verzí."""
        cls._initialize_transposed_standards()
        target_chord = f"{base_note}{chord_type}"
        results = []

        # Nejdřív prohledat originály
        for song_name, song_data in cls.JAZZ_STANDARDS.items():
            for prog in song_data["progressions"]:
                if any(c.upper() == target_chord.upper() for c in prog["chords"]):
                    prog_copy = prog.copy()
                    prog_copy['song'] = song_name
                    prog_copy['transposed_by'] = 0  # NOVÉ: Označení jako originál
                    prog_copy['transposed_key'] = None
                    results.append(prog_copy)

        # Pak transponované
        for song_name, song_data in cls.TRANSPOSED_STANDARDS.items():
            for prog in song_data["progressions"]:
                if any(c.upper() == target_chord.upper() for c in prog["chords"]):
                    prog_copy = prog.copy()
                    prog_copy['song'] = song_name.split("_trans_")[0]  # Původní název písně
                    prog_copy['transposed_by'] = song_data["transposed_by"]  # NOVÉ
                    prog_copy['transposed_key'] = song_data["key"]
                    prog_copy['original_key'] = song_data["original_key"]
                    results.append(prog_copy)

        if DEBUG:
            print(f"Nalezeno {len(results)} realnych progresi pro akord {target_chord} (včetně transpozic)")

        return results