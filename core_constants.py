# core_constants.py
"""
core_constants.py - Rozšířené hudební konstanty a knihovna akordů.
"""
from typing import List, Tuple
from functools import lru_cache
import logging
from utils_config import MusicalConstants

logger = logging.getLogger(__name__)


class ChordLibrary:
    """
    Knihovna akordů a jejich voicingů - rozšířená o Drop 2 voicingy.
    Podporuje tři typy voicingů: Root, Smooth a Drop 2.
    """

    # Definice akordových typů s intervaly od základní noty (v půltónech)
    CHORD_VOICINGS = {
        # Major types
        "maj": [0, 4, 7],  # Základní dur triáda (např. Cmaj: C-E-G)
        "maj7": [0, 4, 7, 11],  # Dur septakord (např. Cmaj7: C-E-G-B)
        "maj9": [0, 4, 7, 11, 14],  # Dur nona (např. Cmaj9: C-E-G-B-D)
        "6": [0, 4, 7, 9],  # Dur sexta (např. C6: C-E-G-A)
        "maj7b5": [0, 4, 6, 11],  # Maj7 s flat five (např. Cmaj7b5: C-E-Gb-B)
        "maj7#5": [0, 4, 8, 11],  # Maj7 s sharp five (např. Cmaj7#5: C-E-G#-B)

        # Minor types
        "m": [0, 3, 7],  # Základní moll triáda (např. Cm: C-Eb-G)
        "m7": [0, 3, 7, 10],  # Moll septakord (např. Cm7: C-Eb-G-Bb)
        "m9": [0, 3, 7, 10, 14],  # Moll nona (např. Cm9: C-Eb-G-Bb-D)
        "m6": [0, 3, 7, 9],  # Moll sexta (např. Cm6: C-Eb-G-A)
        "m7b5": [0, 3, 6, 10],  # Moll septakord se sníženou kvintou (např. Cm7b5: C-Eb-Gb-Bb)
        "m(maj7)": [0, 3, 7, 11],  # Moll s dur septimou (např. Cm(maj7): C-Eb-G-B)

        # Dominant types
        "7": [0, 4, 7, 10],  # Dominantní septakord (např. C7: C-E-G-Bb)
        "9": [0, 4, 7, 10, 14],  # Dominantní nona (např. C9: C-E-G-Bb-D)
        "13": [0, 4, 7, 10, 14, 21],  # Dominantní třináctka (např. C13: C-E-G-Bb-D-A)
        "7b9": [0, 4, 7, 10, 13],  # Dominantní septakord se sníženou nonou (např. C7b9: C-E-G-Bb-Db)
        "7b5": [0, 4, 6, 10],  # Dominant 7 s flat five (např. C7b5: C-E-Gb-Bb)
        "7#5": [0, 4, 8, 10],  # Dominant 7 s sharp five (např. C7#5: C-E-G#-Bb)

        # Diminished / Other
        "dim": [0, 3, 6],  # Zmenšená triáda (např. Cdim: C-Eb-Gb)
        "dim7": [0, 3, 6, 9],  # Zmenšený septakord (např. Cdim7: C-Eb-Gb-A)
        "aug": [0, 4, 8],  # Zvětšená triáda (např. Caug: C-E-G#)
        "sus2": [0, 2, 7],  # Suspended second (např. Csus2: C-D-G)
        "sus4": [0, 5, 7],  # Suspended fourth (např. Csus4: C-F-G)
    }

    @classmethod
    @lru_cache(maxsize=256)
    def get_root_voicing(cls, base_note: str, chord_type: str) -> List[int]:
        """
        Vrací MIDI noty pro akord v základním tvaru (root position).
        Všechny noty jsou v těsné poloze nad sebou.
        Používá cache pro rychlost při opakovaném volání.

        Args:
            base_note: Základní nota akordu (např. "C", "F#")
            chord_type: Typ akordu (např. "maj7", "m7")

        Returns:
            List[int]: MIDI čísla not akordu v root voicingu
        """
        # Fallback pro prázdný chord_type
        if not chord_type:
            chord_type = "maj"

        if chord_type not in cls.CHORD_VOICINGS:
            logger.warning(f"Neznámý typ akordu: {chord_type}, používám fallback")
            chord_type = cls._get_fallback_chord_type(chord_type)

        try:
            base_note_val = MusicalConstants.PIANO_KEYS.index(base_note)
        except ValueError:
            raise ValueError(f"Neplatná základní nota: {base_note}")

        intervals = cls.CHORD_VOICINGS[chord_type]

        # Posun na základní oktávu (např. C4)
        base_midi = 12 * MusicalConstants.MIDI_BASE_OCTAVE + base_note_val

        return [base_midi + i for i in intervals]

    @classmethod
    def get_smooth_voicing(cls, base_note: str, chord_type: str, prev_chord_midi: List[int]) -> List[int]:
        """
        Najde nejbližší inverzi akordu k předchozímu akordu pro plynulé přechody.
        Minimalizuje pohyb hlasů mezi akordy (voice leading).
        Pokud není předchozí akord, vrací root voicing.

        Args:
            base_note: Základní nota nového akordu
            chord_type: Typ nového akordu
            prev_chord_midi: MIDI noty předchozího akordu

        Returns:
            List[int]: MIDI čísla not v smooth voicingu
        """
        if not prev_chord_midi:
            return cls.get_root_voicing(base_note, chord_type)

        root_voicing = cls.get_root_voicing(base_note, chord_type)
        best_voicing = root_voicing
        min_distance = float('inf')

        # Vypočítá průměrnou výšku předchozího akordu
        avg_prev = sum(prev_chord_midi) / len(prev_chord_midi)

        # Prozkoumá různé oktávy a inverze pro nejmenší vzdálenost
        for octave_shift in range(-2, 3):
            for inversion in range(len(root_voicing)):
                # Vytvoří inverzi (rotuje noty)
                inverted_notes = root_voicing[inversion:] + [note + 12 for note in root_voicing[:inversion]]
                current_voicing = [note + octave_shift * 12 for note in inverted_notes]

                # Vypočítá vzdálenost od předchozího akordu
                avg_current = sum(current_voicing) / len(current_voicing)
                distance = abs(avg_current - avg_prev)

                if distance < min_distance:
                    min_distance = distance
                    best_voicing = current_voicing

        return best_voicing

    @classmethod
    def get_drop2_voicing(cls, base_note: str, chord_type: str) -> List[int]:
        """
        Vytvoří Drop 2 voicing - druhý nejvyšší tón se posune o oktávu dolů.
        Drop 2 voicing vytváří otevřenější zvuk vhodný pro jazzové aranže.

        Proces:
        1. Začne s root voicingem v close position
        2. Přesune druhý nejvyšší tón o oktávu dolů
        3. Seřadí noty vzestupně

        Args:
            base_note: Základní nota akordu
            chord_type: Typ akordu

        Returns:
            List[int]: MIDI čísla not v Drop 2 voicingu

        Example:
            Cmaj7 root: [60, 64, 67, 71] (C, E, G, B)
            Cmaj7 drop2: [60, 55, 67, 71] (C, G-oktáva, G, B)
        """
        # Získá základní voicing
        root_voicing = cls.get_root_voicing(base_note, chord_type)

        # Pro triády (3 noty) nemá Drop 2 smysl, vrací root voicing
        if len(root_voicing) < 4:
            logger.debug(f"Drop 2 není vhodný pro triády, používám root voicing pro {base_note}{chord_type}")
            return root_voicing

        # Vytvoří kopii pro úpravu
        drop2_voicing = root_voicing.copy()

        # Najde druhý nejvyšší tón (předposlední v seřazeném seznamu)
        sorted_notes = sorted(drop2_voicing)
        second_highest = sorted_notes[-2]

        # Najde index druhého nejvyššího tónu v původním voicingu
        second_highest_index = drop2_voicing.index(second_highest)

        # Posune druhý nejvyšší tón o oktávu dolů
        drop2_voicing[second_highest_index] = second_highest - 12

        # Seřadí noty vzestupně pro správné zobrazení
        drop2_voicing.sort()

        logger.debug(f"Drop 2 voicing pro {base_note}{chord_type}: {root_voicing} → {drop2_voicing}")
        return drop2_voicing

    @classmethod
    def get_voicing_by_type(cls, base_note: str, chord_type: str, voicing_type: str,
                            prev_chord_midi: List[int] = None) -> Tuple[List[int], str]:
        """
        Univerzální metoda pro získání voicingu podle typu.
        Centralizuje logiku volby voicingu a vrací i barvu pro zobrazení.

        Args:
            base_note: Základní nota akordu
            chord_type: Typ akordu
            voicing_type: Typ voicingu ("root", "smooth", "drop2")
            prev_chord_midi: Předchozí akord pro smooth voicing

        Returns:
            Tuple[List[int], str]: (MIDI noty, barva pro zobrazení)
        """
        if voicing_type == "smooth":
            return cls.get_smooth_voicing(base_note, chord_type, prev_chord_midi or []), "green"
        elif voicing_type == "drop2":
            return cls.get_drop2_voicing(base_note, chord_type), "blue"
        else:  # root voicing (default)
            return cls.get_root_voicing(base_note, chord_type), "red"

    @classmethod
    def _get_fallback_chord_type(cls, original_type: str) -> str:
        """
        Určí fallback typ akordu pro neznámé typy.
        Používá jednoduché heuristiky pro lepší uživatelskou zkušenost.

        Args:
            original_type: Původní (neznámý) typ akordu

        Returns:
            str: Fallback typ akordu
        """
        if not original_type:
            return "maj"
        elif original_type.startswith('m'):
            return 'm7'
        elif 'maj' in original_type:
            return 'maj7'
        elif 'sus' in original_type:
            return 'sus4'
        elif 'dim' in original_type:
            return 'dim7'
        else:
            return '7'  # Default pro dominantní typy

    @staticmethod
    def midi_to_key_nr(midi_note: int, base_octave_midi_start: int = 21) -> int:
        """
        Převede MIDI číslo na číslo klávesy pro zobrazení na klaviatuře.
        A0 (MIDI 21) = klávesa číslo 0.

        Args:
            midi_note: MIDI číslo noty (21-108 pro 88klávesovou klaviaturu)
            base_octave_midi_start: MIDI číslo první klávesy (A0 = 21)

        Returns:
            int: Číslo klávesy pro zobrazení (0-87)
        """
        return midi_note - base_octave_midi_start


def transpose_note(note: str, semitones: int) -> str:
    """
    Transponuje základní notu o daný počet půltónů.
    Jednoduché a čitelné řešení bez složitých optimalizací.

    Args:
        note: Původní nota (např. "C", "F#")
        semitones: Počet půltónů pro transpozici (kladný = výš, záporný = níž)

    Returns:
        str: Transponovaná nota
    """
    # Normalizuje enharmonické názvy
    note = MusicalConstants.ENHARMONIC_MAP.get(note.upper(), note.upper())

    if note not in MusicalConstants.PIANO_KEYS:
        raise ValueError(f"Neplatná nota: {note}")

    index = MusicalConstants.PIANO_KEYS.index(note)
    new_index = (index + semitones) % 12
    return MusicalConstants.PIANO_KEYS[new_index]


def transpose_chord(chord: str, semitones: int) -> str:
    """
    Transponuje celý akord (base_note + type) o daný počet půltónů.
    Importuje HarmonyAnalyzer lokálně pro vyhnutí cyklickým importům.
    """
    from core_harmony import HarmonyAnalyzer  # <-- Musí být takto!

    base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord)
    new_base_note = transpose_note(base_note, semitones)
    return f"{new_base_note}{chord_type}"