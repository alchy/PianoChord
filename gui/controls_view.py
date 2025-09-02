# gui/controls_view.py
"""
gui/controls_view.py - Refaktorovaný manager pro všechny ovládací prvky GUI.
Čistě oddělená GUI vrstva bez hudební logiky.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Callable, TYPE_CHECKING
import logging
from config import AppConfig

if TYPE_CHECKING:
    from core.app_state import ApplicationState
    from midi.player import MidiPlayer

logger = logging.getLogger(__name__)


class ControlsView:
    """
    Refaktorovaný manager pro všechny ovládací prvky a uživatelské vstupy.
    Pouze GUI logika - veškerá hudební logika je v callback funkcích.
    """

    def __init__(self, app_state: 'ApplicationState', midi_player: 'MidiPlayer'):
        """
        Inicializuje ControlsView s referencemi na stav a MIDI.

        Args:
            app_state: Instance ApplicationState
            midi_player: Instance MidiPlayer
        """
        self.app_state = app_state
        self.midi_player = midi_player

        # GUI komponenty
        self.chord_entry: Optional[ttk.Entry] = None
        self.midi_port_combo: Optional[ttk.Combobox] = None
        self.velocity_label: Optional[ttk.Label] = None
        self.log_text: Optional[tk.Text] = None

        # Tkinter variables - OPRAVA: synchronizace s app_state
        self.voicing_var = tk.StringVar(value=app_state.get_voicing_type())
        # OPRAVA: MIDI enabled se nastavuje podle skutečného stavu MIDI playeru
        self.midi_enabled_var = tk.IntVar(value=1 if midi_player.is_enabled else 0)
        self.midi_velocity_var = tk.DoubleVar(value=app_state.midi_velocity)

        # Callback funkce (nastavují se z MainWindow)
        self.on_analyze_chord: Optional[Callable[[str], None]] = None
        self.on_voicing_changed: Optional[Callable[[str], None]] = None
        self.on_midi_settings_changed: Optional[Callable[[], None]] = None

        # Nastavení callback pro automatické změny
        self._setup_variable_callbacks()

        logger.debug("ControlsView inicializován")

    def _setup_variable_callbacks(self) -> None:
        """Nastavení callback pro automatické reakce na změny proměnných."""

        def on_voicing_change(*args):
            new_voicing = self.voicing_var.get()
            self.app_state.set_voicing_type(new_voicing)
            if self.on_voicing_changed:
                self.on_voicing_changed(new_voicing)

        def on_midi_enabled_change(*args):
            enabled = self.midi_enabled_var.get() == 1
            self.app_state.set_midi_enabled(enabled)
            self.midi_player.set_enabled(enabled)
            if self.on_midi_settings_changed:
                self.on_midi_settings_changed()

        def on_velocity_change(*args):
            velocity = int(self.midi_velocity_var.get())
            self.app_state.set_midi_velocity(velocity)
            self.midi_player.set_velocity(velocity)
            self._update_velocity_label()

        self.voicing_var.trace_add("write", on_voicing_change)
        self.midi_enabled_var.trace_add("write", on_midi_enabled_change)
        self.midi_velocity_var.trace_add("write", on_velocity_change)

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
        self.chord_entry.bind('<Return>', self._on_analyze_key_press)

        ttk.Button(input_frame, text="Analyzovat", command=self._analyze_chord).pack(side=tk.LEFT, padx=5)

        # Separator
        separator = ttk.Separator(input_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill='y', padx=10, pady=5)

        # Voicing type selection
        voicing_frame = ttk.LabelFrame(input_frame, text="Voicing typ", padding=5)
        voicing_frame.pack(side=tk.LEFT, padx=5)

        # Radio buttony pro voicing typy
        voicing_options = [
            ("Root", "root"),
            ("Smooth", "smooth"),
            ("Drop 2", "drop2")
        ]

        for text, value in voicing_options:
            ttk.Radiobutton(
                voicing_frame,
                text=text,
                variable=self.voicing_var,
                value=value
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
            variable=self.midi_enabled_var
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

        self.velocity_label = ttk.Label(midi_frame, text=str(self.app_state.midi_velocity))
        self.velocity_label.pack(side=tk.LEFT, padx=5)

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
        # Log text area
        self.log_text = tk.Text(parent, height=10, wrap="word", state='disabled')
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbar pro log
        log_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # Log control buttons
        log_buttons = ttk.Frame(parent)
        log_buttons.pack(fill="x", padx=10, pady=5)

        ttk.Button(log_buttons, text="Exportovat log", command=self._export_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Kopírovat log", command=self._copy_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Vymazat log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Reset GUI", command=self._reset_gui).pack(side=tk.LEFT, padx=5)

    def initialize_midi_gui(self) -> None:
        """
        Inicializuje MIDI GUI komponenty s dostupnými porty.
        OPRAVA: Správně synchronizuje MIDI stav s GUI.
        """
        if not self.midi_player:
            return

        success = self.midi_player.initialize()

        if success:
            # Aktualizuje seznam portů v comboboxu
            available_ports = self.midi_player.get_available_ports()
            if self.midi_port_combo:
                self.midi_port_combo['values'] = available_ports
                if available_ports:
                    current_port = self.midi_player.current_port_name
                    if current_port:
                        self.midi_port_combo.set(current_port)
                    else:
                        self.midi_port_combo.set(available_ports[0])

            # OPRAVA: Synchronizuje MIDI enabled stav mezi app_state, midi_player a GUI
            if self.app_state.midi_enabled:
                self.midi_player.set_enabled(True)
                self.midi_enabled_var.set(1)
            else:
                self.midi_player.set_enabled(False)
                self.midi_enabled_var.set(0)

        else:
            # Zakáže MIDI prvky při selhání inicializace
            self.midi_enabled_var.set(0)
            self.app_state.set_midi_enabled(False)
            self.midi_player.set_enabled(False)
            if self.midi_port_combo:
                self.midi_port_combo.config(state="disabled")

    def update_log_display(self) -> None:
        """Aktualizuje zobrazení logu v GUI."""
        if not self.log_text:
            return

        # Povolí editaci, aktualizuje obsah, zakáže editaci
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(1.0, self.app_state.get_log_content())
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def get_chord_input(self) -> str:
        """
        Vrací aktuální hodnotu z chord input pole.

        Returns:
            str: Text z chord entry
        """
        return self.chord_entry.get().strip() if self.chord_entry else ""

    def clear_chord_input(self) -> None:
        """Vymaže vstupní pole pro akord."""
        if self.chord_entry:
            self.chord_entry.delete(0, tk.END)

    def focus_chord_input(self) -> None:
        """Zaměří vstupní pole pro akord."""
        if self.chord_entry:
            self.chord_entry.focus()

    def set_chord_input(self, chord_name: str) -> None:
        """
        Nastaví text ve vstupním poli.

        Args:
            chord_name: Název akordu k nastavení
        """
        if self.chord_entry:
            self.chord_entry.delete(0, tk.END)
            self.chord_entry.insert(0, chord_name)

    # Private event handlers
    def _on_analyze_key_press(self, event) -> None:
        """Handler pro stisk Enter v chord entry."""
        self._analyze_chord()

    def _analyze_chord(self) -> None:
        """Analyzuje zadaný akord přes callback."""
        chord_name = self.get_chord_input()
        if not chord_name:
            messagebox.showwarning("Vstup", "Zadejte název akordu.")
            return

        if self.on_analyze_chord:
            try:
                self.on_analyze_chord(chord_name)
            except Exception as e:
                logger.error(f"Chyba v callback analyze_chord: {e}")
                messagebox.showerror("Chyba", f"Chyba při analýze: {e}")

    def _on_midi_port_changed(self, event=None) -> None:
        """Handler pro změnu MIDI portu."""
        selected_port = self.midi_port_combo.get()
        if selected_port and selected_port != self.midi_player.current_port_name:
            success = self.midi_player.set_port(selected_port)
            if not success:
                # Vrátí na předchozí port při selhání
                if self.midi_player.current_port_name:
                    self.midi_port_combo.set(self.midi_player.current_port_name)

    def _update_velocity_label(self) -> None:
        """Aktualizuje label pro velocity."""
        value = int(round(self.midi_velocity_var.get()))
        if self.velocity_label:
            self.velocity_label.config(text=str(value))

    def _stop_midi(self) -> None:
        """Zastaví všechny MIDI noty."""
        if self.midi_player.stop_all_notes():
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
                self.app_state.log(f"Log exportován do {file_path}")
            except IOError as e:
                messagebox.showerror("Chyba při ukládání", str(e))

    def _copy_log(self) -> None:
        """Zkopíruje log do schránky."""
        content = self.app_state.get_log_content()
        if not content:
            messagebox.showinfo("Kopírování", "Není co kopírovat z logu.")
            return

        # Zkopíruje do schránky
        try:
            import tkinter as tk
            root = tk._default_root or tk.Tk()
            root.clipboard_clear()
            root.clipboard_append(content)
            messagebox.showinfo("Kopírování", "Obsah logu byl zkopírován do schránky.")
            self.app_state.log("Log zkopírován do schránky")
        except Exception as e:
            logger.error(f"Chyba při kopírování do schránky: {e}")
            messagebox.showerror("Chyba", f"Chyba při kopírování: {e}")

    def _clear_log(self) -> None:
        """Vymaže log po potvrzení."""
        if messagebox.askyesno("Vymazat log", "Opravdu chcete vymazat všechny log záznamy?"):
            self.app_state.clear_log()
            self.update_log_display()

    def _reset_gui(self) -> None:
        """Resetuje GUI do výchozího stavu."""
        if messagebox.askyesno("Reset GUI", "Opravdu chcete resetovat GUI do výchozího stavu?"):
            # Vymaže vstupní pole
            self.clear_chord_input()

            # Resetuje stav aplikace (ale zachová uživatelská nastavení)
            self.app_state.reset_state(keep_settings=True)

            # Aktualizuje log display
            self.update_log_display()

            self.app_state.log("GUI resetováno")

    def setup_keyboard_shortcuts(self, root: tk.Tk, callbacks: dict) -> None:
        """
        Nastaví klávesové zkratky.

        Args:
            root: Hlavní tkinter okno
            callbacks: Slovník s callback funkcemi
        """
        root.bind(AppConfig.KEY_ANALYZE, lambda e: self._analyze_chord())

        if 'prev_chord' in callbacks:
            root.bind(AppConfig.KEY_PREV_CHORD, lambda e: callbacks['prev_chord']())

        if 'next_chord' in callbacks:
            root.bind(AppConfig.KEY_NEXT_CHORD, lambda e: callbacks['next_chord']())

    def get_debug_info(self) -> dict:
        """
        Vrací debug informace pro troubleshooting.

        Returns:
            dict: Debug informace o ControlsView
        """
        return {
            "chord_entry_configured": self.chord_entry is not None,
            "midi_port_combo_configured": self.midi_port_combo is not None,
            "log_text_configured": self.log_text is not None,
            "voicing_type": self.voicing_var.get(),
            "midi_enabled": self.midi_enabled_var.get(),
            "midi_velocity": self.midi_velocity_var.get(),
            "callbacks_set": {
                "analyze_chord": self.on_analyze_chord is not None,
                "voicing_changed": self.on_voicing_changed is not None,
                "midi_settings_changed": self.on_midi_settings_changed is not None
            }
        }
