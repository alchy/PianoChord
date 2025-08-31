# main_window.py
"""
main_window.py - Refaktorovaná hlavní třída GUI.
Zjednodušená pro lepší čitelnost a údržbu.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Optional

from config import AppConfig, MusicalConstants
from app_state import ApplicationState
from midi_manager import MidiManager
from constants import ChordLibrary
from harmony_analyzer import HarmonyAnalyzer
from gui_keyboard import ArchetypeKeyboard
from gui_analysis import AnalysisHandler
from gui_progression import ProgressionHandler

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Refaktorované hlavní GUI okno.
    Zodpovídá pouze za vytvoření a koordinaci GUI komponent.
    """

    def __init__(self):
        # Vytvoří hlavní komponenty
        self.root = tk.Tk()
        self.app_state = ApplicationState()
        self.midi_manager = MidiManager()

        # GUI komponenty
        self.canvas: Optional[tk.Canvas] = None
        self.keyboard: Optional[ArchetypeKeyboard] = None
        self.chord_entry: Optional[ttk.Entry] = None
        self.analysis_handler: Optional[AnalysisHandler] = None
        self.progression_handler: Optional[ProgressionHandler] = None

        # MIDI GUI prvky
        self.midi_port_combo: Optional[ttk.Combobox] = None
        self.velocity_label: Optional[ttk.Label] = None

        # Tkinter variables
        self.smooth_var = tk.IntVar(value=0)
        self.midi_enabled_var = tk.IntVar(value=0)
        self.midi_velocity_var = tk.DoubleVar(value=AppConfig.DEFAULT_MIDI_VELOCITY)

        # Inicializace
        self._setup_window()
        self._setup_midi_callbacks()
        self._create_gui_components()
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

    def _create_gui_components(self) -> None:
        """Vytvoří všechny GUI komponenty."""
        self._create_keyboard_section()
        self._create_input_section()
        self._create_midi_section()
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

    def _create_input_section(self) -> None:
        """Vytvoří vstupní sekci pro zadání akordu."""
        input_frame = ttk.Labelframe(self.root, text="Vstup", padding=10)
        input_frame.grid(row=1, column=0, sticky="ew", pady=10)

        ttk.Label(input_frame, text="Zadejte akord (např. Cmaj7):").pack(side=tk.LEFT, padx=5)

        self.chord_entry = ttk.Entry(input_frame, width=20)
        self.chord_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(input_frame, text="Analyzovat", command=self._analyze_chord).pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(
            input_frame,
            text="Smooth voicing",
            variable=self.smooth_var,
            command=self._on_smooth_voicing_changed
        ).pack(side=tk.LEFT, padx=5)

    def _create_midi_section(self) -> None:
        """Vytvoří MIDI ovládací sekci."""
        midi_frame = ttk.Labelframe(self.root, text="MIDI", padding=10)
        midi_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # MIDI enable checkbox
        ttk.Checkbutton(
            midi_frame,
            text="Přehrát MIDI",
            variable=self.midi_enabled_var,
            command=self._on_midi_enabled_changed
        ).pack(side=tk.LEFT, padx=5)

        # Velocity slider
        ttk.Label(midi_frame, text="Velocity:").pack(side=tk.LEFT, padx=5)

        velocity_slider = ttk.Scale(
            midi_frame,
            from_=0,
            to=127,
            orient=tk.HORIZONTAL,
            variable=self.midi_velocity_var,
            length=100
        )
        velocity_slider.pack(side=tk.LEFT, padx=5)

        self.velocity_label = ttk.Label(midi_frame, text=str(AppConfig.DEFAULT_MIDI_VELOCITY))
        self.velocity_label.pack(side=tk.LEFT, padx=5)

        # Velocity trace pro update labelu
        self.midi_velocity_var.trace_add("write", self._update_velocity_label)

        # Control buttons
        ttk.Button(midi_frame, text="Stop MIDI", command=self._stop_midi).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            midi_frame,
            text="Reset Velocity",
            command=lambda: self.midi_velocity_var.set(AppConfig.DEFAULT_MIDI_VELOCITY)
        ).pack(side=tk.LEFT, padx=5)

        # MIDI port selection
        ttk.Label(midi_frame, text="MIDI Port:").pack(side=tk.LEFT, padx=5)

        self.midi_port_combo = ttk.Combobox(midi_frame, width=30)
        self.midi_port_combo.pack(side=tk.LEFT, padx=5)
        self.midi_port_combo.bind("<<ComboboxSelected>>", self._on_midi_port_changed)

    def _create_output_section(self) -> None:
        """Vytvoří výstupní sekci s notebookem."""
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=3, column=0, sticky="nsew", pady=10)

        # Inicializace handlerů s referencí na tuto třídu
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

        # Log tab
        self._create_log_tab(notebook)

    def _create_log_tab(self, notebook: ttk.Notebook) -> None:
        """Vytvoří tab pro log zprávy."""
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="Log")

        self.log_text = tk.Text(log_tab, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Log control buttons
        log_buttons = ttk.Frame(log_tab)
        log_buttons.pack(fill="x")

        ttk.Button(log_buttons, text="Exportovat log", command=self._export_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Kopírovat log", command=self._copy_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Reset GUI", command=self._reset_gui).pack(side=tk.LEFT, padx=5)

    def _setup_keyboard_shortcuts(self) -> None:
        """Nastaví klávesové zkratky."""
        self.root.bind(AppConfig.KEY_ANALYZE, lambda e: self._analyze_chord())
        self.root.bind(AppConfig.KEY_PREV_CHORD, lambda e: self._step_progression(-1))
        self.root.bind(AppConfig.KEY_NEXT_CHORD, lambda e: self._step_progression(1))

    def _initialize_midi(self) -> None:
        """Inicializuje MIDI systém a aktualizuje GUI."""
        success = self.midi_manager.initialize()

        if success:
            # Aktualizuje seznam portů v comboboxu
            available_ports = self.midi_manager.get_available_ports()
            self.midi_port_combo['values'] = available_ports
            if available_ports:
                self.midi_port_combo.set(self.midi_manager.current_port_name or available_ports[0])
        else:
            # Zakáže MIDI prvky při selhání inicializace
            self.midi_enabled_var.set(0)
            if self.midi_port_combo:
                self.midi_port_combo.config(state="disabled")

    # Event handlers
    def _analyze_chord(self) -> None:
        """Analyzuje zadaný akord."""
        chord_name = self.chord_entry.get().strip()
        if not chord_name:
            messagebox.showwarning("Vstup", "Zadejte název akordu.")
            return

        try:
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_name)
            analysis = HarmonyAnalyzer.analyze(base_note, chord_type)

            # Uloží analýzu do stavu
            self.app_state.set_current_chord_analysis(analysis)

            # Aktualizuje GUI
            self.analysis_handler.display_analysis_results(analysis)
            self._display_chord_on_keyboard(chord_name)

        except ValueError as e:
            messagebox.showerror("Chyba analýzy", str(e))
            self.app_state.log(f"CHYBA analýzy: {e}")

    def _display_chord_on_keyboard(self, chord_name: str) -> None:
        """Zobrazí akord na klaviatuře a případně přehraje MIDI."""
        try:
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_name)

            # Získá MIDI noty podle nastavení smooth voicing
            if self.app_state.smooth_voicing_enabled:
                midi_notes = ChordLibrary.get_smooth_voicing(
                    base_note, chord_type, self.app_state.previous_chord_midi
                )
                color = "green"
            else:
                midi_notes = ChordLibrary.get_root_voicing(base_note, chord_type)
                color = "red"

            # Přehraje MIDI pokud je povoleno
            if self.app_state.midi_enabled:
                self.midi_manager.set_velocity(int(self.midi_velocity_var.get()))
                if self.midi_manager.play_chord(midi_notes):
                    self.app_state.set_chord_played(chord_name, midi_notes)

            # Zobrazí na klaviatuře (jen pokud se změnil akord)
            if chord_name != self.app_state.last_displayed_chord:
                keys_to_highlight = [ChordLibrary.midi_to_key_nr(note) for note in midi_notes]
                self.keyboard.draw(keys_to_highlight, color=color)
                self.app_state.last_displayed_chord = chord_name

        except (ValueError, IndexError) as e:
            messagebox.showerror("Chyba zobrazení", str(e))
            self.app_state.log(f"CHYBA zobrazení: {e}")
            if self.keyboard:
                self.keyboard.clear_highlights()

    def _step_progression(self, step: int) -> None:
        """Krok v progresi."""
        if self.app_state.step_progression(step):
            self.progression_handler.update_progression_display()
            # Zobrazí aktuální akord
            current_chord = self.app_state.get_current_chord()
            if current_chord:
                self._display_chord_on_keyboard(current_chord)

    def _on_smooth_voicing_changed(self) -> None:
        """Handler pro změnu smooth voicing."""
        self.app_state.smooth_voicing_enabled = self.smooth_var.get() == 1

    def _on_midi_enabled_changed(self) -> None:
        """Handler pro zapnutí/vypnutí MIDI."""
        enabled = self.midi_enabled_var.get() == 1
        self.midi_manager.set_enabled(enabled)
        self.app_state.midi_enabled = enabled

    def _on_midi_port_changed(self, event=None) -> None:
        """Handler pro změnu MIDI portu."""
        selected_port = self.midi_port_combo.get()
        if selected_port and selected_port != self.midi_manager.current_port_name:
            success = self.midi_manager.set_port(selected_port)
            if not success:
                # Vrátí na předchozí port při selhání
                if self.midi_manager.current_port_name:
                    self.midi_port_combo.set(self.midi_manager.current_port_name)

    def _update_velocity_label(self, *args) -> None:
        """Aktualizuje label pro velocity."""
        value = int(round(self.midi_velocity_var.get()))
        self.velocity_label.config(text=str(value))

    def _stop_midi(self) -> None:
        """Zastaví všechny MIDI noty."""
        if self.midi_manager.stop_all_notes():
            self.app_state.log("Všechny MIDI noty zastaveny")

    def _handle_midi_error(self, error_message: str) -> None:
        """Handler pro MIDI chyby."""
        self.app_state.log(f"MIDI CHYBA: {error_message}")
        messagebox.showerror("Chyba MIDI", error_message)

    def _handle_midi_success(self, success_message: str) -> None:
        """Handler pro MIDI úspěchy."""
        self.app_state.log(success_message)

    # Utility methods
    def _export_log(self) -> None:
        """Exportuje log do souboru."""
        content = self.app_state.get_log_content()
        if not content:
            messagebox.showinfo("Export", "Není co exportovat z logu.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Export", f"Log byl úspěšně uložen do: {file_path}")
            except IOError as e:
                messagebox.showerror("Chyba při ukládání", str(e))

    def _copy_log(self) -> None:
        """Zkopíruje log do schránky."""
        content = self.app_state.get_log_content()
        if not content:
            messagebox.showinfo("Kopírování", "Není co kopírovat z logu.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Kopírování", "Obsah logu byl zkopírován do schránky.")

    def _reset_gui(self) -> None:
        """Resetuje celé GUI do výchozího stavu."""
        # Vymaže vstupní pole
        if self.chord_entry:
            self.chord_entry.delete(0, tk.END)

        # Vyčistí klaviaturu
        if self.keyboard:
            self.keyboard.clear_highlights()

        # Resetuje stav aplikace
        self.app_state.reset_state()

        # Aktualizuje handlery
        if self.analysis_handler:
            self.analysis_handler.reset_display()

        if self.progression_handler:
            self.progression_handler.reset_display()

    def update_log_display(self) -> None:
        """Aktualizuje zobrazení logu v GUI."""
        if hasattr(self, 'log_text'):
            # Vymaže současný obsah
            self.log_text.delete(1.0, tk.END)
            # Vloží nový obsah
            self.log_text.insert(1.0, self.app_state.get_log_content())
            self.log_text.see(tk.END)

    def load_progression(self, chords: list, source_name: str) -> None:
        """Nahraje progrese - rozhraní pro ostatní komponenty."""
        self.app_state.load_progression(chords, source_name)
        if self.progression_handler:
            self.progression_handler.create_progression_buttons()
            self.progression_handler.update_progression_display()

    def jump_to_chord(self, index: int) -> None:
        """Skočí na konkrétní akord - rozhraní pro ostatní komponenty."""
        if self.app_state.jump_to_chord_index(index):
            if self.progression_handler:
                self.progression_handler.update_progression_display()
            # Zobrazí akord
            current_chord = self.app_state.get_current_chord()
            if current_chord:
                self._display_chord_on_keyboard(current_chord)

    def run(self) -> None:
        """Spustí hlavní smyčku aplikace."""
        try:
            # Nastaví callback pro aktualizaci logu
            original_log = self.app_state.log

            def log_with_gui_update(message: str):
                original_log(message)
                self.update_log_display()

            self.app_state.log = log_with_gui_update

            # Spustí GUI
            self.root.mainloop()

        finally:
            # Cleanup při ukončení
            self.midi_manager.cleanup()
            logger.info("Aplikace ukončena")
