# main.py
"""
main.py - Vstupní bod refaktorované aplikace Piano Chord Analyzer.
Inicializuje centralizované logování před importem ostatních modulů.
"""

import sys
import logging
from pathlib import Path


def main():
    """Hlavní funkce aplikace s kompletní inicializací."""

    # PRVNÍ VĚCÍ - inicializace logování před jakýmikoli importy
    try:
        from config import LoggingConfig
        LoggingConfig.setup_logging()  # Automatická konfigurace
        logger = logging.getLogger(__name__)
        logger.info("Piano Chord Analyzer spuštěn")
        logger.info(f"Verze Pythonu: {sys.version}")

    except Exception as e:
        print(f"KRITICKÁ CHYBA při inicializaci logování: {e}")
        sys.exit(1)

    # Kontrola základních závislostí
    missing_deps = []

    try:
        import tkinter as tk
    except ImportError:
        missing_deps.append("tkinter (součást standardní Python instalace)")

    try:
        import mido
        import rtmidi
        logger.info("MIDI závislosti dostupné")
    except ImportError as e:
        logger.warning(f"MIDI závislosti nejsou dostupné: {e}")
        logger.info("Aplikace poběží bez MIDI funkcí")

    if missing_deps:
        error_msg = f"Chybí kritické závislosti: {', '.join(missing_deps)}"
        logger.error(error_msg)
        print(f"CHYBA: {error_msg}")
        print("Nainstalujte požadované balíčky: pip install -r requirements.txt")
        sys.exit(1)

    try:
        # Import hlavních komponent (po inicializaci logování)
        logger.info("Inicializuji základní komponenty...")

        # Import core komponent
        from core.app_state import ApplicationState
        from core.progression_manager import ProgressionManager
        from midi.player import MidiPlayer

        logger.info("Core komponenty inicializovány")

        # Import GUI komponenty
        logger.info("Inicializuji GUI...")
        from gui.main_window import MainWindow

        # Vytvoření a spuštění aplikace
        logger.info("Vytvářím hlavní okno aplikace...")

        app = MainWindow()

        logger.info("GUI úspěšně inicializováno")
        logger.info("=== Aplikace připravena k použití ===")

        # Spuštění hlavní smyčky
        app.run()

    except ImportError as e:
        logger.error(f"Chyba při importu modulů: {e}")
        print(f"CHYBA IMPORTU: {e}")
        print("Zkontrolujte, zda jsou všechny soubory na správném místě")
        print("Očekávaná struktura:")
        print("  core/          (music_theory.py, chord_analyzer.py, ...)")
        print("  midi/          (player.py)")
        print("  display/       (keyboard_display.py)")
        print("  gui/           (main_window.py, ...)")
        print("  config.py")
        print("  database.json")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Aplikace ukončena uživatelem (Ctrl+C)")

    except Exception as e:
        logger.error(f"Neočekávaná chyba: {e}", exc_info=True)
        print(f"KRITICKÁ CHYBA: {e}")
        print("Podrobnosti najdete v log souboru (pokud je nakonfigurován)")
        sys.exit(1)

    finally:
        logger.info("Čištění zdrojů...")
        try:
            # Cleanup MIDI
            if 'midi_player' in locals():
                midi_player.cleanup()
        except:
            pass

        logger.info("Piano Chord Analyzer ukončen")


def check_environment():
    """
    Kontroluje prostředí před spuštěním aplikace.

    Returns:
        bool: True pokud je prostředí v pořádku
    """
    print("=== Piano Chord Analyzer - Kontrola prostředí ===")

    # Kontrola Python verze
    if sys.version_info < (3, 8):
        print(f"CHYBA: Python 3.8+ je požadován, máte {sys.version}")
        return False
    print(f"Python verze: {sys.version.split()[0]} OK")

    # Kontrola struktury souborů
    required_files = [
        "config.py",
        "core/music_theory.py",
        "core/chord_analyzer.py",
        "core/progression_manager.py",
        "core/app_state.py",
        "midi/player.py",
        "display/keyboard_display.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"CHYBA: Chybí soubory: {', '.join(missing_files)}")
        return False
    print("Struktura souborů: OK")

    # Kontrola databáze
    if not Path("database.json").exists():
        print("VAROVÁNÍ: database.json nenalezena - bude použita fallback databáze")
    else:
        print("Databáze: OK")

    # Kontrola MIDI závislostí (volitelné)
    try:
        import mido
        print("MIDI podpora: OK")
    except ImportError:
        print("MIDI podpora: NEDOSTUPNÁ (aplikace bude fungovat bez MIDI)")

    print("=== Kontrola dokončena ===")
    return True


if __name__ == '__main__':
    # Kontrola prostředí před spuštěním
    if not check_environment():
        print("Opravte chyby a spusťte znovu")
        sys.exit(1)

    # Spuštění aplikace
    main()
