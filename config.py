# config.py
"""
config.py - Centralizovaná konfigurace aplikace.
Obsahuje nastavení, hudební konstanty a centralizované logování.
"""
import logging
import logging.config
import os
from typing import Dict, Any

# Globální debug flag
DEBUG = True


class AppConfig:
    """Centralizované nastavení aplikace."""

    # GUI nastavení
    WINDOW_TITLE = "Piano Chord Analyzer"
    WINDOW_SIZE = "1000x750"

    # Klávesové zkratky
    KEY_ANALYZE = '<Return>'
    KEY_PREV_CHORD = '<Left>'
    KEY_NEXT_CHORD = '<Right>'

    # MIDI výchozí hodnoty
    DEFAULT_MIDI_VELOCITY = 64
    DEFAULT_CHORD_DURATION = 1.0
    MIDI_ALL_NOTES_OFF_CC = 123

    # Logování
    LOG_FORMAT = '[{timestamp}] {message}'
    LOG_FILE = 'app.log' if DEBUG else None


class MusicalConstants:
    """Hudební konstanty používané v aplikaci."""

    PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    ENHARMONIC_MAP = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}
    BLACK_KEYS = {"C#", "D#", "F#", "G#", "A#"}

    # Rozměry klaviatury
    WHITE_KEY_WIDTH = 18
    WHITE_KEY_HEIGHT = 80
    BLACK_KEY_WIDTH = 12
    BLACK_KEY_HEIGHT = 50

    ARCHETYPE_SIZE = 88
    MIDI_BASE_OCTAVE = 4


class LoggingConfig:
    """Centralizovaná konfigurace logování pro celou aplikaci."""

    @staticmethod
    def setup_logging(config_file: str = None):
        """
        Nastaví centralizované logování pro všechny moduly.

        Args:
            config_file: Cesta k YAML/INI konfiguračnímu souboru (volitelné)
        """

        # Pokus o načtení z konfiguračního souboru
        if config_file and os.path.exists(config_file):
            try:
                if config_file.endswith(('.yaml', '.yml')):
                    try:
                        import yaml
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                            logging.config.dictConfig(config)
                            return
                    except ImportError:
                        print("PyYAML není nainstalován, použiji výchozí konfiguraci")
                elif config_file.endswith('.ini'):
                    logging.config.fileConfig(config_file, disable_existing_loggers=False)
                    return
            except Exception as e:
                print(f"Chyba při načítání konfigurace logování z {config_file}: {e}")
                print("Použiji výchozí konfiguraci...")

        # Výchozí konfigurace
        level = logging.DEBUG if DEBUG else logging.INFO

        # Console handler s UTF-8
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Formátování bez emotikonů
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Handlers seznam
        handlers = [console_handler]

        # File handler (pokud je definován)
        if AppConfig.LOG_FILE:
            try:
                file_handler = logging.FileHandler(AppConfig.LOG_FILE, encoding='utf-8')
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                handlers.append(file_handler)
            except Exception as e:
                print(f"Nelze vytvořit log soubor {AppConfig.LOG_FILE}: {e}")

        # Konfigurace root loggeru
        logging.basicConfig(
            level=level,
            handlers=handlers,
            force=True  # Přepíše existující konfiguraci
        )

        # Úvodní zpráva
        logger = logging.getLogger(__name__)
        logger.info("Centralizované logování inicializováno")
        if AppConfig.LOG_FILE:
            logger.info(f"Logování do souboru: {AppConfig.LOG_FILE}")


# Volitelná YAML konfigurace pro pokročilé uživatele
LOGGING_YAML_TEMPLATE = """
version: 1
disable_existing_loggers: false

formatters:
  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
  simple:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: simple
    stream: ext://sys.stdout

  file:
    class: logging.FileHandler
    level: DEBUG  
    formatter: detailed
    filename: app.log
    encoding: utf-8

loggers:
  core:
    level: DEBUG
    propagate: true
  midi:
    level: DEBUG
    propagate: true
  display:
    level: DEBUG
    propagate: true
  gui:
    level: INFO
    propagate: true

root:
  level: DEBUG
  handlers: [console, file]
"""