# main.py
"""
Piano Chord Analyzer - Jazz Training Edition
Vstupní bod aplikace - spouští modularizovanou verzi

Autor: Piano Chord Analyzer Team
Verze: 2.1
"""

import logging
import sys
import os

# Fix DPI scaling issues on Windows (must be before any GUI imports)
if sys.platform == 'win32':
    try:
        import ctypes
        # Set DPI awareness to avoid scaling issues when mixing Tkinter and PyQt5
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
    except Exception:
        pass  # Ignore errors on older Windows versions

# Konfigurace logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('piano_analyzer.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Hlavní vstupní bod aplikace.
    Inicializuje všechny komponenty a spouští GUI.
    """
    logger.info("=== Piano Chord Analyzer - Jazz Training Edition ===")
    logger.info("Spouštím aplikaci...")

    try:
        # Import tkinter pro kontrolu dostupnosti GUI
        import tkinter as tk
        logger.info("Tkinter: OK")

    except ImportError as e:
        logger.error(f"Tkinter není dostupný: {e}")
        print("CHYBA: Tkinter není nainstalován. Je součástí standardního Pythonu.")
        print("Na Linuxu nainstalujte: sudo apt-get install python3-tk")
        sys.exit(1)

    try:
        # Import MIDI podpory (volitelné)
        import mido
        logger.info("MIDI podpora: OK")

    except ImportError:
        logger.warning("MIDI podpora: NEDOSTUPNÁ (mido nenalezen)")
        print("Varování: MIDI knihovna není nainstalována.")
        print("Pro MIDI podporu spusťte: pip install mido python-rtmidi")
        print("Aplikace bude fungovat bez MIDI přehrávání.")

    try:
        # Import aplikačních modulů
        from music_analytics import MusicAnalytics
        from midi_playback import MidiPlayback
        from gui import PianoChordAnalyzer

        logger.info("Moduly načteny úspěšně")

        # Inicializace komponent
        logger.info("Inicializuji Music Analytics...")
        music_analytics = MusicAnalytics()

        logger.info("Inicializuji MIDI Playback...")
        midi_playback = MidiPlayback()

        logger.info("Inicializuji GUI...")
        app = PianoChordAnalyzer(music_analytics, midi_playback)

        # Spuštění aplikace
        logger.info("Spouštím hlavní smyčku aplikace")
        app.run()

    except ImportError as e:
        logger.error(f"Chyba při importu modulů: {e}")
        print(f"CHYBA: Nelze načíst moduly aplikace: {e}")
        print("Zkontrolujte, že všechny soubory jsou přítomny:")
        print("  - config.py")
        print("  - music_analytics.py")
        print("  - midi_playback.py")
        print("  - gui.py")
        print("  - database.json")
        sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Chybějící soubor: {e}")
        print(f"CHYBA: Chybějící soubor: {e}")
        print("Ujistěte se, že je soubor database.json přítomen v adresáři aplikace.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Kritická chyba: {e}", exc_info=True)
        print(f"KRITICKÁ CHYBA: {e}")
        print("Podrobnosti v souboru piano_analyzer.log")
        sys.exit(1)

    finally:
        logger.info("Aplikace ukončena")


if __name__ == '__main__':
    main()
