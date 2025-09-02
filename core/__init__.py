# core/__init__.py
"""
core/__init__.py - Inicializace core modulu pro Piano Chord Analyzer.
Exportuje hlavní třídy a funkce pro snadný import.
"""

import logging

# Inicializace loggeru pro core modul
logger = logging.getLogger(__name__)
logger.info("Core modul inicializován")

# Import hlavních tříd a funkcí pro externí použití
from .music_theory import (
    transpose_note,
    transpose_chord,
    parse_chord_name,
    get_fallback_chord_type,
    get_tritone_substitution,
    get_chord_intervals,
    validate_chord_name
)

from .chord_analyzer import (
    ChordAnalyzer,
    midi_to_key_number,
    key_number_to_midi
)

from .progression_manager import (
    ProgressionManager,
    analyze_progression_complexity
)

from .app_state import (
    ApplicationState,
    StateManager
)

# Verze core modulu
__version__ = "2.0.0"

# Seznam všech exportovaných objektů
__all__ = [
    # Music theory funkce
    "transpose_note",
    "transpose_chord",
    "parse_chord_name",
    "get_fallback_chord_type",
    "get_tritone_substitution",
    "get_chord_intervals",
    "validate_chord_name",

    # Chord analyzer
    "ChordAnalyzer",
    "midi_to_key_number",
    "key_number_to_midi",

    # Progression manager
    "ProgressionManager",
    "analyze_progression_complexity",

    # Application state
    "ApplicationState",
    "StateManager"
]


# Utility funkce pro rychlé testování core modulu
def test_core_functionality():
    """
    Testuje základní funkcionalitu core modulu.
    Užitečné pro rychlé ověření, že vše funguje správně.

    Returns:
        bool: True pokud všechny testy prošly
    """
    try:
        logger.info("Spouštím test core funkcionality...")

        # Test music theory
        result = transpose_chord("Cmaj7", 5)  # Fmaj7
        assert result == "Fmaj7", f"Transpozice selhala: {result}"

        # Test chord analyzer
        analysis = ChordAnalyzer.analyze_chord_name("Cmaj7")
        assert analysis["chord_name"] == "Cmaj7", "Analýza akordu selhala"

        # Test progression manager
        manager = ProgressionManager()
        manager.load_database()
        genres = manager.get_genres()
        assert len(genres) > 0, "Žádné žánry nenalezeny"

        # Test app state
        state = ApplicationState()
        state.set_voicing_type("smooth")
        assert state.get_voicing_type() == "smooth", "App state selhalo"

        logger.info("Všechny core testy prošly úspěšně")
        return True

    except Exception as e:
        logger.error(f"Core test selhal: {e}")
        return False


# Automatické testování při importu (pouze v debug módu)
from config import DEBUG

if DEBUG:
    logger.debug("Debug mód - spouštím automatické testy...")
    if not test_core_functionality():
        logger.warning("Některé core testy selhaly - aplikace může nefungovat správně")
