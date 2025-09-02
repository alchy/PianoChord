# core/music_theory.py
"""
core/music_theory.py - Centrální modul pro základní hudební teorii.
Obsahuje nezávislé funkce pro transpozici, parsování akordů a další hudební operace.
Tento modul nemá žádné závislosti na jiných modulech - lze použít samostatně.
"""

import logging
from typing import Tuple, List
from config import MusicalConstants

logger = logging.getLogger(__name__)


def transpose_note(note: str, semitones: int) -> str:
    """
    Transponuje základní notu o daný počet půltónů.
    Nezávislá funkce použitelná v jakémkoliv hudebním programu.

    Args:
        note: Původní nota (např. "C", "F#")
        semitones: Počet půltónů pro transpozici (kladný = výš, záporný = níž)

    Returns:
        str: Transponovaná nota

    Raises:
        ValueError: Pokud je nota neplatná

    Examples:
        >>> transpose_note("C", 5)
        "F"
        >>> transpose_note("F#", -1)
        "F"
    """
    # Normalizuje enharmonické názvy
    note = MusicalConstants.ENHARMONIC_MAP.get(note.upper(), note.upper())

    if note not in MusicalConstants.PIANO_KEYS:
        raise ValueError(f"Neplatná nota: {note}")

    index = MusicalConstants.PIANO_KEYS.index(note)
    new_index = (index + semitones) % 12
    return MusicalConstants.PIANO_KEYS[new_index]


def parse_chord_name(chord_full_name: str) -> Tuple[str, str]:
    """
    Rozparsuje celý název akordu na základní notu a typ.
    Optimalizováno pro složité typy jako '7#11' nebo '13b9'.
    Nezávislá funkce bez externích závislostí.

    Args:
        chord_full_name: Celý název akordu (např. "Cmaj7", "F#m7b5")

    Returns:
        Tuple[str, str]: (základní_nota, typ_akordu)

    Raises:
        ValueError: Pokud je název akordu neplatný

    Examples:
        >>> parse_chord_name("Cmaj7")
        ("C", "maj7")
        >>> parse_chord_name("F#m7b5")
        ("F#", "m7b5")
        >>> parse_chord_name("C")
        ("C", "")
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

    # Prázdný chord_type je validní (dur triáda)
    return base_note, chord_type


def transpose_chord(chord: str, semitones: int) -> str:
    """
    Transponuje celý akord (base_note + type) o daný počet půltónů.
    Používá lokální parse_chord_name funkci - žádné cyklické importy.

    Args:
        chord: Původní akord (např. "Cmaj7", "F#m")
        semitones: Počet půltónů pro transpozici

    Returns:
        str: Transponovaný akord

    Raises:
        ValueError: Pokud je akord neplatný

    Examples:
        >>> transpose_chord("Cmaj7", 7)
        "Gmaj7"
        >>> transpose_chord("Am", 3)
        "Cm"
    """
    try:
        base_note, chord_type = parse_chord_name(chord)
        new_base_note = transpose_note(base_note, semitones)
        return f"{new_base_note}{chord_type}"
    except Exception as e:
        logger.error(f"Chyba při transpozici akordu {chord}: {e}")
        raise


def get_fallback_chord_type(original_type: str) -> str:
    """
    Určí fallback typ akordu pro neznámé typy.
    Používá jednoduché heuristiky pro lepší uživatelskou zkušenost.

    Args:
        original_type: Původní (neznámý) typ akordu

    Returns:
        str: Fallback typ akordu

    Examples:
        >>> get_fallback_chord_type("")
        "maj"
        >>> get_fallback_chord_type("m13b5")
        "m7"
        >>> get_fallback_chord_type("sus9")
        "sus4"
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


def get_tritone_substitution(dominant_chord: str) -> str:
    """
    Vrátí tritonovou substituci pro dominantní akord.
    Tritonus je vzdálenost 6 půltónů.

    Args:
        dominant_chord: Dominantní akord (např. "G7")

    Returns:
        str: Tritonová substituce (např. "Db7")

    Examples:
        >>> get_tritone_substitution("G7")
        "Db7"
        >>> get_tritone_substitution("D7")
        "Ab7"
    """
    try:
        base_note, chord_type = parse_chord_name(dominant_chord)

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


def get_chord_intervals(chord_type: str) -> List[int]:
    """
    Vrátí intervaly pro daný typ akordu v půltónech od základní noty.
    Nezávislá funkce pro použití v jiných programech.

    Args:
        chord_type: Typ akordu (např. "maj7", "m7", "dim7")

    Returns:
        List[int]: Seznam intervalů v půltónech

    Examples:
        >>> get_chord_intervals("maj7")
        [0, 4, 7, 11]
        >>> get_chord_intervals("m7")
        [0, 3, 7, 10]
    """
    # Základní definice akordových typů
    CHORD_INTERVALS = {
        # Major types
        "": [0, 4, 7],  # Základní dur (prázdný = dur triáda)
        "maj": [0, 4, 7],  # Dur triáda
        "maj7": [0, 4, 7, 11],  # Dur septakord
        "maj9": [0, 4, 7, 11, 14],  # Dur nona
        "6": [0, 4, 7, 9],  # Dur sexta
        "maj7b5": [0, 4, 6, 11],  # Maj7 s flat five
        "maj7#5": [0, 4, 8, 11],  # Maj7 s sharp five

        # Minor types
        "m": [0, 3, 7],  # Moll triáda
        "m7": [0, 3, 7, 10],  # Moll septakord
        "m9": [0, 3, 7, 10, 14],  # Moll nona
        "m6": [0, 3, 7, 9],  # Moll sexta
        "m7b5": [0, 3, 6, 10],  # Moll septakord se sníženou kvintou
        "m(maj7)": [0, 3, 7, 11],  # Moll s dur septimou

        # Dominant types
        "7": [0, 4, 7, 10],  # Dominantní septakord
        "9": [0, 4, 7, 10, 14],  # Dominantní nona
        "13": [0, 4, 7, 10, 14, 21],  # Dominantní třináctka
        "7b9": [0, 4, 7, 10, 13],  # Dominant 7 se sníženou nonou
        "7b5": [0, 4, 6, 10],  # Dominant 7 s flat five
        "7#5": [0, 4, 8, 10],  # Dominant 7 s sharp five

        # Diminished / Other
        "dim": [0, 3, 6],  # Zmenšená triáda
        "dim7": [0, 3, 6, 9],  # Zmenšený septakord
        "aug": [0, 4, 8],  # Zvětšená triáda
        "sus2": [0, 2, 7],  # Suspended second
        "sus4": [0, 5, 7],  # Suspended fourth
    }

    # Pokus o přímé nalezení
    if chord_type in CHORD_INTERVALS:
        return CHORD_INTERVALS[chord_type]

    # Fallback pro neznámé typy
    fallback_type = get_fallback_chord_type(chord_type)
    logger.warning(f"Neznámý typ akordu: {chord_type}, použiji fallback: {fallback_type}")

    return CHORD_INTERVALS.get(fallback_type, [0, 4, 7])  # Dur triáda jako poslední fallback


def validate_chord_name(chord_name: str) -> bool:
    """
    Validuje, zda je název akordu syntakticky správný.

    Args:
        chord_name: Název akordu k validaci

    Returns:
        bool: True pokud je název validní, False jinak

    Examples:
        >>> validate_chord_name("Cmaj7")
        True
        >>> validate_chord_name("Xyz123")
        False
    """
    try:
        base_note, chord_type = parse_chord_name(chord_name)
        # Pokud parsování prošlo, akord je validní
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    # Jednoduché testování funkcí
    print("Test transpozice:")
    print(f"C + 5 = {transpose_note('C', 5)}")  # F
    print(f"Cmaj7 + 7 = {transpose_chord('Cmaj7', 7)}")  # Gmaj7

    print("\nTest parsování:")
    print(f"'F#m7b5' -> {parse_chord_name('F#m7b5')}")

    print("\nTest tritonové substituce:")
    print(f"G7 -> {get_tritone_substitution('G7')}")  # Db7

    print("\nTest intervalů:")
    print(f"maj7 -> {get_chord_intervals('maj7')}")  # [0, 4, 7, 11]
