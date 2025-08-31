# app_state.py
"""
app_state.py - Centralizovaná správa stavu aplikace.
Odděluje logiku stavu od GUI komponente pro lepší údržbu.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import AppConfig

logger = logging.getLogger(__name__)


class ApplicationState:
    """Centralizovaný stav aplikace - oddělený od GUI."""

    def __init__(self):
        # Stav aktuální analýzy
        self.current_analysis: Dict[str, Any] = {}
        self.last_displayed_chord: Optional[str] = None

        # Stav progrese
        self.current_progression_chords: List[str] = []
        self.current_progression_index: int = 0

        # MIDI stav
        self.previous_chord_midi: List[int] = []
        self.last_played_chord: Optional[str] = None

        # Nastavení
        self.smooth_voicing_enabled: bool = False
        self.midi_enabled: bool = False
        self.midi_velocity: int = AppConfig.DEFAULT_MIDI_VELOCITY

        # Log historie
        self.log_messages: List[str] = []

    def set_current_chord_analysis(self, analysis: Dict[str, Any]) -> None:
        """Nastaví výsledky aktuální analýzy akordu."""
        self.current_analysis = analysis
        chord_name = analysis.get('chord_name', 'Unknown')
        self.log(f"Analyzován akord: {chord_name}")

    def load_progression(self, chords: List[str], source_name: str) -> None:
        """Nahraje novou progrese a resetuje pozici."""
        self.current_progression_chords = chords.copy()
        self.current_progression_index = 0
        self.log(f"Nahraná progrese z: {source_name} ({len(chords)} akordů)")

    def step_progression(self, step: int) -> bool:
        """
        Posune se o krok v prgresi.
        Vrací True pokud byl krok úspěšný, False pokud dosáhli konce/začátku.
        """
        if not self.current_progression_chords:
            return False

        new_index = self.current_progression_index + step

        if 0 <= new_index < len(self.current_progression_chords):
            self.current_progression_index = new_index
            return True
        else:
            # Logování hranic progrese
            if new_index >= len(self.current_progression_chords):
                self.log("Dosažen konec progrese")
            else:
                self.log("Dosažen začátek progrese")
            return False

    def jump_to_chord_index(self, index: int) -> bool:
        """Skočí na konkrétní akord v prgresi."""
        if not self.current_progression_chords or not (0 <= index < len(self.current_progression_chords)):
            return False

        self.current_progression_index = index
        return True

    def get_current_chord(self) -> Optional[str]:
        """Vrací aktuální akord z progrese."""
        if not self.current_progression_chords:
            return None
        return self.current_progression_chords[self.current_progression_index]

    def set_chord_played(self, chord_name: str, midi_notes: List[int]) -> None:
        """Zaznamenává přehrání akordu."""
        self.last_played_chord = chord_name
        self.previous_chord_midi = midi_notes.copy()
        self.log(f"Přehrán MIDI akord: {chord_name}")

    def reset_state(self) -> None:
        """Resetuje celý stav aplikace."""
        self.current_analysis.clear()
        self.last_displayed_chord = None
        self.current_progression_chords.clear()
        self.current_progression_index = 0
        self.previous_chord_midi.clear()
        self.last_played_chord = None
        self.log("Stav aplikace resetován")

    def log(self, message: str) -> None:
        """Přidá zprávu do logu s timestampem."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = AppConfig.LOG_FORMAT.format(timestamp=timestamp, message=message)
        self.log_messages.append(formatted_msg)
        logger.info(message)

    def get_log_content(self) -> str:
        """Vrací celý obsah logu jako string."""
        return '\n'.join(self.log_messages)

    def clear_log(self) -> None:
        """Vymaže historii logu."""
        self.log_messages.clear()
        self.log("Log vymazán")
