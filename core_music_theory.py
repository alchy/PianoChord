# core_music_theory.py
"""
core_music_theory.py - Centrální modul pro základní hudební teorii.
Obsahuje sdílené funkce pro transpozici, parsování akordů a další hudební operace.
Tento modul nemá závislosti na jiných core modulech - předchází cyklickým importům.
"""

import logging
from typing import Tuple
from utils_config import MusicalConstants

logger = logging.getLogger(__name__)


def transpose_note(note: str, semitones: int) -> str:
    """
    Transponuje základní notu o daný počet půltónů.
    Jednoduché a čitelné řešení bez složitých optimalizací.

    Args:
        note: Původní nota (např. "C", "F#")
        semitones: Počet půltónů pro transpozici (kladný = výš, záporný = níž)

    Returns:
        str: Transponovaná nota

    Raises:
        ValueError: Pokud je nota neplatná
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
    PŘENESENO z core_harmony.py pro odstranění cyklického importu.

    Args:
        chord_full_name: Celý název akordu (např. "Cmaj7", "F#m7b5")

    Returns:
        Tuple[str, str]: (základní_nota, typ_akordu)

    Raises:
        ValueError: Pokud je název akordu neplatný
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

    # Speciální případ pro akordy bez typu (např. "C") - fallback na prázdný string
    # Později bude handled v ChordLibrary
    if not chord_type and base_note in chord_full_name:
        chord_type = ""  # Nechá prázdné, bude handled později

    return base_note, chord_type


def transpose_chord(chord: str, semitones: int) -> str:
    """
    Transponuje celý akord (base_note + type) o daný počet půltónů.
    Nyní používá lokální parse_chord_name funkci - žádný cyklický import.

    Args:
        chord: Původní akord (např. "Cmaj7", "F#m")
        semitones: Počet půltónů pro transpozici

    Returns:
        str: Transponovaný akord

    Raises:
        ValueError: Pokud je akord neplatný
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
    PŘENESENO z core_constants.py pro centralizaci logiky.

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


def get_tritone_substitution(dominant_chord: str) -> str:
    """
    Vrátí tritonovou substituci pro dominantní akord.
    PŘENESENO z core_theory.py pro centralizaci.

    Args:
        dominant_chord: Dominantní akord (např. "G7")

    Returns:
        str: Tritonová substituce (např. "Db7")

    Example:
        >>> get_tritone_substitution("G7")
        "Db7"
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
