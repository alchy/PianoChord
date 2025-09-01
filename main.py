# main.py
"""
main.py - Vstupní bod aplikace.
"""

import sys
import logging
from utils_config import setup_logging

# Inicializace logování před importem ostatních modulů
setup_logging()
logger = logging.getLogger(__name__)


def main():
    """Hlavní funkce aplikace."""
    logger.info("Spouštím Piano Chord Analyzer")
    logger.info(f"Verze Pythonu: {sys.version}")

    try:
        # Import zde pro zajištění správné inicializace loggingu
        from gui_main_window import MainWindow

        # Vytvoření a spuštění aplikace
        app = MainWindow()
        app.run()

    except ImportError as e:
        logger.error(f"Chyba při importu závislostí: {e}")
        print(f"CHYBA: Chybí závislosti - {e}")
        print("Nainstalujte požadované balíčky: pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Neočekávaná chyba při spuštění aplikace: {e}")
        print(f"KRITICKÁ CHYBA: {e}")
        sys.exit(1)

    finally:
        logger.info("Aplikace ukončena")


if __name__ == '__main__':
    main()
