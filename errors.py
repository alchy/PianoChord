# errors.py
"""
Centralized error handling for Piano Chord Analyzer.
Contains all custom exceptions and error utilities.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class PianoAnalyzerError(Exception):
    """Base exception for Piano Chord Analyzer."""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ChordParsingError(PianoAnalyzerError):
    """Raised when chord parsing fails."""
    pass


class MidiError(PianoAnalyzerError):
    """Raised when MIDI operations fail."""
    pass


class DatabaseError(PianoAnalyzerError):
    """Raised when database operations fail."""
    pass


class VoicingError(PianoAnalyzerError):
    """Raised when voicing calculation fails."""
    pass


class TranspositionError(PianoAnalyzerError):
    """Raised when transposition fails."""
    pass


def handle_error(func):
    """
    Decorator for basic error handling with logging.
    Catches exceptions and logs them appropriately.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PianoAnalyzerError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise PianoAnalyzerError(f"Unexpected error in {func.__name__}: {str(e)}")

    return wrapper


def safe_execute(operation, default_value=None, error_message="Operation failed"):
    """
    Safely execute an operation and return default value on error.

    Args:
        operation: Function to execute
        default_value: Value to return on error
        error_message: Message to log on error

    Returns:
        Operation result or default_value on error
    """
    try:
        return operation()
    except Exception as e:
        logger.warning(f"{error_message}: {e}")
        return default_value


def validate_chord_name(chord_name: str) -> str:
    """
    Validates and cleans chord name input.

    Args:
        chord_name: Raw chord name input

    Returns:
        Cleaned chord name

    Raises:
        ChordParsingError: If chord name is invalid
    """
    if not chord_name or not isinstance(chord_name, str):
        raise ChordParsingError("Chord name must be a non-empty string")

    cleaned = chord_name.strip()
    if not cleaned:
        raise ChordParsingError("Chord name cannot be empty")

    return cleaned


def validate_midi_port(port_name: str, available_ports: list) -> str:
    """
    Validates MIDI port name.

    Args:
        port_name: MIDI port name to validate
        available_ports: List of available port names

    Returns:
        Validated port name

    Raises:
        MidiError: If port is invalid
    """
    if not port_name:
        raise MidiError("MIDI port name cannot be empty")

    if port_name not in available_ports:
        raise MidiError(f"MIDI port '{port_name}' not available. Available ports: {available_ports}")

    return port_name


def log_and_suppress(func, *args, **kwargs):
    """
    Execute function and suppress exceptions while logging them.
    Useful for cleanup operations that shouldn't fail the main flow.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Suppressed error in {func.__name__}: {e}")
        return None
