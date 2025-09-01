# display_chord.py
"""
display_chord.py - Manager pro zobrazování a přehrávání akordů.
"""
import logging
from typing import List, Optional, TYPE_CHECKING
from tkinter import messagebox

from core_constants import ChordLibrary
from core_harmony import HarmonyAnalyzer

if TYPE_CHECKING:
    from gui_main_window import MainWindow
    from core_state import ApplicationState
    from hw_midi import MidiManager
    from gui_controls import ControlsManager
    from gui_keyboard import ArchetypeKeyboard

logger = logging.getLogger(__name__)


class ChordDisplayManager:
    """
    Manager pro zobrazování a přehrávání akordů.
    OPRAVA: Rozšířen o kontrolu nad MIDI přehráváním podle kontextu.
    Spravuje zobrazení na klaviatuře, MIDI playback a progression handling.
    """

    def __init__(self, main_window: 'MainWindow', app_state: 'ApplicationState', midi_manager: 'MidiManager'):
        self.main_window = main_window
        self.app_state = app_state
        self.midi_manager = midi_manager

        # Reference na ostatní managery (nastaví se později)
        self.controls_manager: Optional['ControlsManager'] = None
        self.keyboard: Optional['ArchetypeKeyboard'] = None

    def set_controls_manager(self, controls_manager: 'ControlsManager') -> None:
        """Nastaví referenci na controls manager pro komunikaci."""
        self.controls_manager = controls_manager

    def set_keyboard(self, keyboard: 'ArchetypeKeyboard') -> None:
        """Nastaví referenci na klaviaturu pro zobrazování."""
        self.keyboard = keyboard

    def display_chord_on_keyboard(self, chord_name: str, force_update: bool = False, play_midi: bool = True) -> None:
        """
        Zobrazí akord na klaviatuře a případně přehraje MIDI.
        OPRAVA: Přidán parametr play_midi pro selektivní potlačení zvuku.
        Podporuje všechny tři typy voicingů s automatickým výběrem barvy.

        Args:
            chord_name: Název akordu k zobrazení
            force_update: Pokud True, překreslí i když je akord stejný
            play_midi: Pokud False, nepřehrává MIDI (jen vizuální zobrazení)
        """
        try:
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_name)

            # Získá aktuální typ voicingu ze stavu
            voicing_type = self.app_state.get_voicing_type()

            # Získá předchozí akord pro smooth voicing
            prev_chord_midi = self.app_state.get_previous_chord_midi() if voicing_type == "smooth" else None

            # Získá MIDI noty a barvu podle typu voicingu
            midi_notes, color = ChordLibrary.get_voicing_by_type(
                base_note, chord_type, voicing_type, prev_chord_midi
            )

            # OPRAVA: Přehraje MIDI pouze pokud je povoleno AND play_midi=True
            if play_midi and self.app_state.midi_enabled:
                if self.controls_manager:
                    velocity = self.controls_manager.get_midi_velocity()
                    self.midi_manager.set_velocity(velocity)

                if self.midi_manager.play_chord(midi_notes):
                    self.app_state.set_chord_played(chord_name, midi_notes)

            # Zobrazí na klaviatuře (jen pokud se změnil akord nebo force_update)
            if chord_name != self.app_state.last_displayed_chord or force_update:
                if self.keyboard:
                    keys_to_highlight = [ChordLibrary.midi_to_key_nr(note) for note in midi_notes]
                    self.keyboard.draw(keys_to_highlight, color=color)
                self.app_state.last_displayed_chord = chord_name

                # Aktualizuje stav pro smooth voicing
                if voicing_type != "smooth":
                    # Pro non-smooth voicingy aktualizujeme předchozí akord
                    self.app_state.set_chord_played(chord_name, midi_notes)

            # Logování informací o voicingu a přehrávání
            voicing_info = f"{voicing_type} voicing"
            if voicing_type == "drop2" and len(midi_notes) < 4:
                voicing_info += " (fallback na root - triáda)"

            midi_info = " + MIDI" if (play_midi and self.app_state.midi_enabled) else " (pouze vizuálně)"
            self.app_state.log(f"Zobrazen {chord_name} - {voicing_info}{midi_info}")

        except (ValueError, IndexError) as e:
            messagebox.showerror("Chyba zobrazení", str(e))
            self.app_state.log(f"CHYBA zobrazení: {e}")
            if self.keyboard:
                self.keyboard.clear_highlights()

    def display_chord_visual_only(self, chord_name: str, force_update: bool = False) -> None:
        """
        NOVÁ METODA: Zobrazí akord pouze vizuálně bez MIDI přehrávání.
        Užitečné pro analýzu akordů, kde nechceme rušit zvukem.

        Args:
            chord_name: Název akordu k zobrazení
            force_update: Pokud True, překreslí i když je akord stejný
        """
        self.display_chord_on_keyboard(chord_name, force_update, play_midi=False)

    def step_progression(self, step: int) -> None:
        """
        Krok v progesi.
        Zachovává funkcionalitu s novým voicing systémem.
        POZN: V progression playeru se přehrává MIDI normálně.

        Args:
            step: Počet kroků (kladný = dopředu, záporný = dozadu)
        """
        if self.app_state.step_progression(step):
            # Aktualizuje progression player display
            if self.main_window.progression_handler:
                self.main_window.progression_handler.update_progression_display()

            # Zobrazí aktuální akord S MIDI (v progression playeru je to žádoucí)
            current_chord = self.app_state.get_current_chord()
            if current_chord:
                self.display_chord_on_keyboard(current_chord, play_midi=True)

    def jump_to_chord(self, index: int) -> None:
        """
        Skočí na konkrétní akord v progesi.
        POZN: V progression playeru se přehrává MIDI normálně.

        Args:
            index: Index akordu v progesi (0-based)
        """
        if self.app_state.jump_to_chord_index(index):
            # Aktualizuje progression player display
            if self.main_window.progression_handler:
                self.main_window.progression_handler.update_progression_display()

            # Zobrazí akord S MIDI (v progression playeru je to žádoucí)
            current_chord = self.app_state.get_current_chord()
            if current_chord:
                self.display_chord_on_keyboard(current_chord, play_midi=True)

    def load_progression(self, chords: List[str], source_name: str) -> None:
        """
        Nahraje progrese a aktualizuje GUI.
        POZN: První akord se zobrazí pouze vizuálně, bez MIDI.

        Args:
            chords: Seznam akordů v progesi
            source_name: Název zdroje progrese (pro logování)
        """
        # Nahraje progrese do app_state
        self.app_state.load_progression(chords, source_name)

        # Aktualizuje progression handler
        if self.main_window.progression_handler:
            self.main_window.progression_handler.create_progression_buttons()
            self.main_window.progression_handler.update_progression_display()

        # OPRAVA: Zobrazí první akord pouze vizuálně (bez MIDI při načítání)
        if chords:
            self.display_chord_visual_only(chords[0])

    def clear_keyboard_highlights(self) -> None:
        """Vyčistí zvýraznění na klaviatuře."""
        if self.keyboard:
            self.keyboard.clear_highlights()
            self.app_state.last_displayed_chord = None

    def reset_display_state(self) -> None:
        """Resetuje stav zobrazování akordů."""
        self.clear_keyboard_highlights()
        self.app_state.reset_state()
        logger.debug("Stav zobrazování akordů resetován")

    def get_current_voicing_info(self) -> dict:
        """
        Vrací informace o aktuálním voicingu pro debugging.

        Returns:
            dict: Informace o voicingu a stavu
        """
        return {
            "voicing_type": self.app_state.get_voicing_type(),
            "last_displayed_chord": self.app_state.last_displayed_chord,
            "has_previous_midi": bool(self.app_state.get_previous_chord_midi()),
            "midi_enabled": self.app_state.midi_enabled
        }
