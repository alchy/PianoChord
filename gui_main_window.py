# gui_main_window.py
"""
gui_main_window.py - hlavní GUI okno.
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional

from utils_config import AppConfig, MusicalConstants
from core_state import ApplicationState
from hw_midi import MidiManager
from gui_keyboard import ArchetypeKeyboard
from gui_analysis import AnalysisHandler
from gui_progression import ProgressionHandler
from gui_controls import ControlsManager
from display_chord import ChordDisplayManager

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Refaktorované hlavní GUI okno.
    NOVÉ: Pouze koordinace - deleguje odpovědnosti na specializované managery.
    """

    def __init__(self):
        # Vytvoření hlavních komponent
        self.root = tk.Tk()
        self.app_state = ApplicationState()
        self.midi_manager = MidiManager()

        # GUI základní komponenty
        self.canvas: Optional[tk.Canvas] = None
        self.keyboard: Optional[ArchetypeKeyboard] = None

        # Existující handlery (zůstávají)
        self.analysis_handler: Optional[AnalysisHandler] = None
        self.progression_handler: Optional[ProgressionHandler] = None

        # NOVÉ: Specializované managery
        self.controls_manager: Optional[ControlsManager] = None
        self.chord_display_manager: Optional[ChordDisplayManager] = None

        # Inicializace
        self._setup_window()
        self._setup_midi_callbacks()
        self._create_managers()
        self._create_gui_layout()
        self._setup_keyboard_shortcuts()
        self._initialize_midi()

    def _setup_window(self) -> None:
        """Nastaví základní vlastnosti hlavního okna."""
        self.root.title(AppConfig.WINDOW_TITLE)
        self.root.geometry(AppConfig.WINDOW_SIZE)

        # Grid konfigurace
        self.root.rowconfigure(0, weight=2)  # Klaviatura
        self.root.rowconfigure(1, weight=0)  # Vstupní sekce
        self.root.rowconfigure(2, weight=0)  # MIDI sekce
        self.root.rowconfigure(3, weight=3)  # Output notebook
        self.root.columnconfigure(0, weight=1)

    def _setup_midi_callbacks(self) -> None:
        """Nastaví callback funkce pro MIDI manager."""
        self.midi_manager.on_error = self._handle_midi_error
        self.midi_manager.on_success = self._handle_midi_success

    def _create_managers(self) -> None:
        """
        NOVÉ: Vytvoří specializované managery a propojí je.
        Každý manager má přístup k potřebným komponentám přes reference.
        """
        # Vytvoření managerů s referencemi
        self.controls_manager = ControlsManager(
            main_window=self,
            app_state=self.app_state,
            midi_manager=self.midi_manager
        )

        self.chord_display_manager = ChordDisplayManager(
            main_window=self,
            app_state=self.app_state,
            midi_manager=self.midi_manager
        )

        # Propojení managerů mezi sebou
        self.controls_manager.set_chord_display_manager(self.chord_display_manager)
        self.chord_display_manager.set_controls_manager(self.controls_manager)

    def _create_gui_layout(self) -> None:
        """Vytvoří základní rozložení GUI a deleguje vytvoření komponent."""
        # Klaviatura sekce
        self._create_keyboard_section()

        # Vstupní a MIDI sekce (deleguje na controls_manager)
        self.controls_manager.create_input_section(self.root, row=1)
        self.controls_manager.create_midi_section(self.root, row=2)

        # Output sekce s notebookem
        self._create_output_section()

    def _create_keyboard_section(self) -> None:
        """Vytvoří sekci s klaviaturou."""
        keyboard_frame = ttk.Frame(self.root, padding=10)
        keyboard_frame.grid(row=0, column=0, sticky="ew")
        keyboard_frame.columnconfigure(0, weight=1)

        # Výpočet rozměrů klaviatury
        keyboard_width = 52 * MusicalConstants.WHITE_KEY_WIDTH
        keyboard_height = 100

        self.canvas = tk.Canvas(keyboard_frame, width=keyboard_width, height=keyboard_height, bg="lightgray")
        self.canvas.grid(row=0, column=0, pady=10)

        self.keyboard = ArchetypeKeyboard(self.canvas, MusicalConstants.ARCHETYPE_SIZE)
        self.keyboard.draw()

        # Předá klaviaturu chord_display_manageru
        self.chord_display_manager.set_keyboard(self.keyboard)

    def _create_output_section(self) -> None:
        """Vytvoří výstupní sekci s notebookem."""
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=3, column=0, sticky="nsew", pady=10)

        # Existující handlery (zůstávají nezměněny)
        self.analysis_handler = AnalysisHandler(self)
        self.progression_handler = ProgressionHandler(self)

        # Analysis tab
        analysis_tab = ttk.Frame(notebook)
        notebook.add(analysis_tab, text="Analýza akordu")
        self.analysis_handler.create_analysis_tab(analysis_tab)

        # Progression player tab
        prog_player_tab = ttk.Frame(notebook)
        notebook.add(prog_player_tab, text="Progression Player")
        self.progression_handler.create_prog_player_tab(prog_player_tab)

        # Log tab (deleguje na controls_manager)
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="Log")
        self.controls_manager.create_log_tab(log_tab)

    def _setup_keyboard_shortcuts(self) -> None:
        """Nastaví klávesové zkratky - deleguje na controls_manager."""
        self.controls_manager.setup_keyboard_shortcuts(self.root)

    def _initialize_midi(self) -> None:
        """Inicializuje MIDI systém - deleguje na controls_manager."""
        self.controls_manager.initialize_midi_gui()

    # Event handlers (zjednodušené - většina delegována)
    def _handle_midi_error(self, error_message: str) -> None:
        """Handler pro MIDI chyby."""
        self.app_state.log(f"MIDI CHYBA: {error_message}")

    def _handle_midi_success(self, success_message: str) -> None:
        """Handler pro MIDI úspěchy."""
        self.app_state.log(success_message)

    # Veřejné rozhraní pro ostatní komponenty (zachováno pro kompatibilitu)
    def load_progression(self, chords: list, source_name: str) -> None:
        """Nahraje progrese - deleguje na chord_display_manager."""
        self.chord_display_manager.load_progression(chords, source_name)

    def jump_to_chord(self, index: int) -> None:
        """Skoči na konkrétní akord - deleguje na chord_display_manager."""
        self.chord_display_manager.jump_to_chord(index)

    def update_log_display(self) -> None:
        """Aktualizuje zobrazení logu - deleguje na controls_manager."""
        self.controls_manager.update_log_display()

    def _step_progression(self, step: int) -> None:
        """Krok v progesi - deleguje na chord_display_manager."""
        self.chord_display_manager.step_progression(step)

    def _display_chord_on_keyboard(self, chord_name: str, force_update: bool = False) -> None:
        """Zobrazí akord na klaviatuře - deleguje na chord_display_manager."""
        self.chord_display_manager.display_chord_on_keyboard(chord_name, force_update)

    def run(self) -> None:
        """
        Spustí hlavní smyčku aplikace.
        NOVÉ: Zjednodušeno - pouze setup log callback a spuštění.
        """
        try:
            # Nastaví callback pro aktualizaci logu
            original_log = self.app_state.log

            def log_with_gui_update(message: str):
                original_log(message)
                self.update_log_display()

            self.app_state.log = log_with_gui_update

            # Úvodní zpráva
            self.app_state.log(f"Aplikace spuštěna s {self.app_state.get_voicing_type()} voicingem")

            # Spustí GUI
            self.root.mainloop()

        finally:
            # Cleanup při ukončení
            self.midi_manager.cleanup()
            logger.info("Aplikace ukončena")
