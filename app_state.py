# app_state.py
"""
app_state.py - Centralizovaná správa stavu aplikace.
NOVÉ: Přidán stav pro typ voicingu (root/smooth/drop2).
Odděluje logiku stavu od GUI komponente pro lepší údržbu.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import AppConfig

logger = logging.getLogger(__name__)


class ApplicationState:
    """
    Centralizovaný stav aplikace - oddělený od GUI.
    Spravuje všechny důležité stavy včetně nového voicing typu.
    """

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

        # Nastavení voicingů - NOVÉ!
        self.voicing_type: str = "root"  # "root", "smooth", "drop2"
        self.midi_enabled: bool = False
        self.midi_velocity: int = AppConfig.DEFAULT_MIDI_VELOCITY

        # Log historie
        self.log_messages: List[str] = []

    def set_voicing_type(self, voicing_type: str) -> None:
        """
        Nastaví typ voicingu a zaloguje změnu.

        Args:
            voicing_type: Nový typ voicingu ("root", "smooth", "drop2")
        """
        valid_types = ["root", "smooth", "drop2"]
        if voicing_type not in valid_types:
            logger.warning(f"Neplatný typ voicingu: {voicing_type}, použit 'root'")
            voicing_type = "root"

        old_type = self.voicing_type
        self.voicing_type = voicing_type

        if old_type != voicing_type:
            self.log(f"Voicing změněn z '{old_type}' na '{voicing_type}'")

    def get_voicing_type(self) -> str:
        """
        Vrací aktuální typ voicingu.

        Returns:
            str: Aktuální typ voicingu
        """
        return self.voicing_type

    def set_current_chord_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Nastaví výsledky aktuální analýzy akordu.

        Args:
            analysis: Slovník s výsledky analýzy akordu
        """
        self.current_analysis = analysis
        chord_name = analysis.get('chord_name', 'Unknown')
        self.log(f"Analyzován akord: {chord_name}")

    def load_progression(self, chords: List[str], source_name: str) -> None:
        """
        Nahraje novou progrese a resetuje pozici.

        Args:
            chords: Seznam akordů v progrese
            source_name: Název zdroje progrese (pro logování)
        """
        self.current_progression_chords = chords.copy()
        self.current_progression_index = 0
        self.log(f"Nahraná progrese z: {source_name} ({len(chords)} akordů)")

    def step_progression(self, step: int) -> bool:
        """
        Posune se o krok v progrese.

        Args:
            step: Počet kroků (kladný = dopředu, záporný = dozadu)

        Returns:
            bool: True pokud byl krok úspěšný, False pokud dosáhli konce/začátku
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
        """
        Skočí na konkrétní akord v progrese.

        Args:
            index: Index akordu v progrese (0-based)

        Returns:
            bool: True pokud skok byl úspěšný
        """
        if not self.current_progression_chords or not (0 <= index < len(self.current_progression_chords)):
            return False

        self.current_progression_index = index
        return True

    def get_current_chord(self) -> Optional[str]:
        """
        Vrací aktuální akord z progrese.

        Returns:
            Optional[str]: Aktuální akord nebo None pokud není progrese
        """
        if not self.current_progression_chords:
            return None
        return self.current_progression_chords[self.current_progression_index]

    def set_chord_played(self, chord_name: str, midi_notes: List[int]) -> None:
        """
        Zaznamenává přehrání akordu pro MIDI a smooth voicing.

        Args:
            chord_name: Název přehraného akordu
            midi_notes: MIDI čísla přehraných not
        """
        self.last_played_chord = chord_name
        self.previous_chord_midi = midi_notes.copy()
        self.log(f"Přehrán MIDI akord: {chord_name}")

    def should_use_previous_chord_for_smooth(self) -> bool:
        """
        Určuje, zda použít předchozí akord pro smooth voicing.

        Returns:
            bool: True pokud máme předchozí akord a používáme smooth voicing
        """
        return self.voicing_type == "smooth" and bool(self.previous_chord_midi)

    def get_previous_chord_midi(self) -> List[int]:
        """
        Vrací MIDI noty předchozího akordu pro smooth voicing.

        Returns:
            List[int]: MIDI noty předchozího akordu
        """
        return self.previous_chord_midi.copy() if self.previous_chord_midi else []

    def reset_state(self) -> None:
        """
        Resetuje celý stav aplikace do výchozího stavu.
        Zachovává pouze základní nastavení.
        """
        self.current_analysis.clear()
        self.last_displayed_chord = None
        self.current_progression_chords.clear()
        self.current_progression_index = 0
        self.previous_chord_midi.clear()
        self.last_played_chord = None

        # Voicing typ se neresetuje - uživatel si může chtít zachovat preferenci
        # self.voicing_type = "root"  # Zakomentováno záměrně

        self.log("Stav aplikace resetován")

    def reset_voicing_state(self) -> None:
        """
        Resetuje pouze stav související s voicingem.
        Užitečné při změně typu voicingu.
        """
        self.previous_chord_midi.clear()
        self.last_played_chord = None
        self.log("Stav voicingu resetován")

    def log(self, message: str) -> None:
        """
        Přidá zprávu do logu s timestampem.

        Args:
            message: Zpráva k zalogování
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = AppConfig.LOG_FORMAT.format(timestamp=timestamp, message=message)
        self.log_messages.append(formatted_msg)
        logger.info(message)

    def get_log_content(self) -> str:
        """
        Vrací celý obsah logu jako string.

        Returns:
            str: Obsah logu oddělený novými řádky
        """
        return '\n'.join(self.log_messages)

    def clear_log(self) -> None:
        """Vymaže historii logu."""
        self.log_messages.clear()
        self.log("Log vymazán")

    def get_state_summary(self) -> Dict[str, Any]:
        """
        Vrací shrnutí aktuálního stavu pro debugging.

        Returns:
            Dict[str, Any]: Slovník s klíčovými stavy aplikace
        """
        return {
            "voicing_type": self.voicing_type,
            "current_chord": self.get_current_chord(),
            "progression_length": len(self.current_progression_chords),
            "progression_index": self.current_progression_index,
            "has_previous_midi": bool(self.previous_chord_midi),
            "midi_enabled": self.midi_enabled,
            "log_entries": len(self.log_messages)
        }
