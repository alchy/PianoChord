# gui_controls.py
"""
gui_controls.py - Manager pro všechny ovládací prvky GUI.
NOVÝ SOUBOR: Obsahuje input sekci, MIDI ovládání, log tab a event handling.
Zodpovídá za všechny způsoby, jak uživatel ovládá aplikaci.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, TYPE_CHECKING
import logging

from config import AppConfig
from harmony_analyzer import HarmonyAnalyzer

if TYPE_CHECKING:
    from main_window import MainWindow
    from app_state import ApplicationState
    from midi_manager import MidiManager
    from chord_display import ChordDisplayManager

logger = logging.getLogger(__name__)


class ControlsManager:
    """
    Manager pro všechny ovládací prvky a uživatelské vstupy.
    Spravuje input sekci, MIDI ovládání, log tab a klávesové zkratky.
    """

    def __init__(self, main_window: 'MainWindow', app_state: 'ApplicationState', midi_manager: 'MidiManager'):
        self.main_window = main_window
        self.app_state = app_state
        self.midi_manager = midi_manager

        # Reference na chord display manager (nastaví se později)
        self.chord_display_manager: Optional['ChordDisplayManager'] = None

        # GUI komponenty
        self.chord_entry: Optional[ttk.Entry] = None
        self.midi_port_combo: Optional[ttk.Combobox] = None
        self.velocity_label: Optional[ttk.Label] = None
        self.log_text: Optional[tk.Text] = None

        # Tkinter variables pro voicing a MIDI
        self.voicing_var = tk.StringVar(value="root")
        self.midi_enabled_var = tk.IntVar(value=0)
        self.midi_velocity_var = tk.DoubleVar(value=AppConfig.DEFAULT_MIDI_VELOCITY)

        # Nastavení callback pro voicing změny
        self._setup_voicing_callback()

    def set_chord_display_manager(self, chord_display_manager: 'ChordDisplayManager') -> None:
        """Nastaví referenci na chord display manager pro komunikaci."""
        self.chord_display_manager = chord_display_manager

    def _setup_voicing_callback(self) -> None:
        """
        Nastaví callback pro okamžité přepnutí voicingu.
        Když uživatel změní radio button, okamžitě se překreslí akord.
        """

        def on_voicing_change(*args):
            new_voicing = self.voicing_var.get()
            self.app_state.set_voicing_type(new_voicing)

            # Okamžitě překreslí aktuální akord s novým voicingem
            current_chord = self.app_state.last_displayed_chord
            if current_chord and self.chord_display_manager:
                self.chord_display_manager.display_chord_on_keyboard(current_chord, force_update=True)

        self.voicing_var.trace_add("write", on_voicing_change)

    def create_input_section(self, parent: tk.Widget, row: int) -> None:
        """
        Vytvoří vstupní sekci pro zadání akordu a voicing výběr.

        Args:
            parent: Rodičovský widget
            row: Řádek pro umístění v gridu
        """
        input_frame = ttk.Labelframe(parent, text="Vstup", padding=10)
        input_frame.grid(row=row, column=0, sticky="ew", pady=10)

        # Vstup pro akord
        ttk.Label(input_frame, text="Zadejte akord (např. Cmaj7):").pack(side=tk.LEFT, padx=5)

        self.chord_entry = ttk.Entry(input_frame, width=20)
        self.chord_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(input_frame, text="Analyzovat", command=self._analyze_chord).pack(side=tk.LEFT, padx=5)

        # Separator
        separator = ttk.Separator(input_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill='y', padx=10, pady=5)

        # Voicing type selection s radio buttony
        voicing_frame = ttk.LabelFrame(input_frame, text="Voicing typ", padding=5)
        voicing_frame.pack(side=tk.LEFT, padx=5)

        # Radio buttony pro voicing typy
        ttk.Radiobutton(
            voicing_frame,
            text="Root",
            variable=self.voicing_var,
            value="root"
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            voicing_frame,
            text="Smooth",
            variable=self.voicing_var,
            value="smooth"
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            voicing_frame,
            text="Drop 2",
            variable=self.voicing_var,
            value="drop2"
        ).pack(side=tk.LEFT, padx=2)

    def create_midi_section(self, parent: tk.Widget, row: int) -> None:
        """
        Vytvoří MIDI ovládací sekci.

        Args:
            parent: Rodičovský widget
            row: Řádek pro umístění v gridu
        """
        midi_frame = ttk.Labelframe(parent, text="MIDI", padding=10)
        midi_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))

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

    def create_log_tab(self, parent: ttk.Frame) -> None:
        """Vytvoří tab pro log zprávy."""
        self.log_text = tk.Text(parent, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Log control buttons
        log_buttons = ttk.Frame(parent)
        log_buttons.pack(fill="x")

        ttk.Button(log_buttons, text="Exportovat log", command=self._export_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Kopírovat log", command=self._copy_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Reset GUI", command=self._reset_gui).pack(side=tk.LEFT, padx=5)

    def setup_keyboard_shortcuts(self, root: tk.Tk) -> None:
        """Nastaví klávesové zkratky."""
        root.bind(AppConfig.KEY_ANALYZE, lambda e: self._analyze_chord())
        root.bind(AppConfig.KEY_PREV_CHORD, lambda e: self.main_window._step_progression(-1))
        root.bind(AppConfig.KEY_NEXT_CHORD, lambda e: self.main_window._step_progression(1))

    def initialize_midi_gui(self) -> None:
        """Inicializuje MIDI GUI komponenty."""
        success = self.midi_manager.initialize()

        if success:
            # Aktualizuje seznam portů v comboboxu
            available_ports = self.midi_manager.get_available_ports()
            if self.midi_port_combo:
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
        """
        Analyzuje zadaný akord.
        Používá nový voicing systém přes chord_display_manager.
        """
        chord_name = self.chord_entry.get().strip()
        if not chord_name:
            messagebox.showwarning("Vstup", "Zadejte název akordu.")
            return

        try:
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_name)
            analysis = HarmonyAnalyzer.analyze(base_note, chord_type)

            # Uloží analýzu do stavu
            self.app_state.set_current_chord_analysis(analysis)

            # Aktualizuje GUI přes existující handlery
            self.main_window.analysis_handler.display_analysis_results(analysis)

            # Zobrazí akord přes chord_display_manager
            if self.chord_display_manager:
                self.chord_display_manager.display_chord_on_keyboard(chord_name)

        except ValueError as e:
            messagebox.showerror("Chyba analýzy", str(e))
            self.app_state.log(f"CHYBA analýzy: {e}")

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
        if self.velocity_label:
            self.velocity_label.config(text=str(value))

    def _stop_midi(self) -> None:
        """Zastaví všechny MIDI noty."""
        if self.midi_manager.stop_all_notes():
            self.app_state.log("Všechny MIDI noty zastaveny")

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

        self.main_window.root.clipboard_clear()
        self.main_window.root.clipboard_append(content)
        messagebox.showinfo("Kopírování", "Obsah logu byl zkopírován do schránky.")

    def _reset_gui(self) -> None:
        """
        Resetuje celé GUI do výchozího stavu.
        Zachovává voicing typ podle uživatelské preference.
        """
        # Vymaže vstupní pole
        if self.chord_entry:
            self.chord_entry.delete(0, tk.END)

        # Vyčistí klaviaturu přes main_window
        if self.main_window.keyboard:
            self.main_window.keyboard.clear_highlights()

        # Resetuje stav aplikace (ale ne voicing typ)
        self.app_state.reset_state()

        # Aktualizuje handlery přes main_window
        if self.main_window.analysis_handler:
            self.main_window.analysis_handler.reset_display()

        if self.main_window.progression_handler:
            self.main_window.progression_handler.reset_display()

        self.app_state.log("GUI resetováno")

    def update_log_display(self) -> None:
        """Aktualizuje zobrazení logu v GUI."""
        if self.log_text:
            # Vymaže současný obsah
            self.log_text.delete(1.0, tk.END)
            # Vloží nový obsah
            self.log_text.insert(1.0, self.app_state.get_log_content())
            self.log_text.see(tk.END)

    def get_midi_velocity(self) -> int:
        """Vrací aktuální MIDI velocity pro chord_display_manager."""
        return int(self.midi_velocity_var.get())
