# gui_main.py
"""
gui_main.py - Hlavní GUI aplikace pro Piano Chord Analyzer.
Inicializuje okno, komponenty a handlery pro analýzu a progrese.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional
from datetime import datetime  # NOVÉ: Pro timestamp v logu

from constants import MusicalConstants, ChordLibrary
from harmony_analyzer import HarmonyAnalyzer
from gui_keyboard import ArchetypeKeyboard
from gui_analysis import AnalysisHandler
from gui_progression import ProgressionHandler
from midi_player import MidiPlayer  # NOVÉ: Import pro MIDI

DEBUG = True


class PianoGUI:
    """Hlavni trida pro GUI aplikace Piano Harmony Analyzer."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Piano Chord Analyzer")
        self.root.geometry("1000x750")

        self.current_analysis: Dict[str, Any] = {}
        self.prev_chord_midi: List[int] = []
        self.current_progression_chords: List[str] = []
        self.current_progression_index = 0
        self.last_displayed_chord_name: Optional[str] = None
        self.smooth_var = tk.IntVar(value=0)
        self.midi_enabled_var = tk.IntVar(value=0)  # NOVÉ: Toggle pro MIDI
        self.midi_player: Optional[MidiPlayer] = None  # NOVÉ: Instance MidiPlayer
        self.midi_port_combo: Optional[ttk.Combobox] = None  # NOVÉ: Combo pro porty

        # Inicializace handlerů na začátku
        try:
            self._initialize_handlers()
        except Exception as e:
            messagebox.showerror("Chyba inicializace", f"Nepodařilo se inicializovat handlery: {str(e)}")
            self._log(f"CHYBA inicializace handlerů: {e}")
            raise

        self.root.rowconfigure(0, weight=2)
        self.root.rowconfigure(1, weight=0)
        self.root.rowconfigure(2, weight=3)
        self.root.columnconfigure(0, weight=1)

        self._init_keyboard_frame()
        self._init_input_frame()
        self._init_output_notebook()

        # NOVÉ: Inicializace MIDI po GUI
        self._initialize_midi()

        self.root.bind('<Return>', lambda e: self.analysis_handler.analyze_harmony())
        self.root.bind('<Left>', lambda e: self._step_progression(-1))
        self.root.bind('<Right>', lambda e: self._step_progression(1))

    def _initialize_handlers(self):
        self.analysis_handler = AnalysisHandler(self)
        self.progression_handler = ProgressionHandler(self)

    def _initialize_midi(self):
        """Inicializuje MIDI player a načte porty s lepším error handlingem."""
        try:
            dummy_player = MidiPlayer()  # Pro načtení portů
            available_ports = dummy_player.get_available_ports()
            dummy_player.close()
            if available_ports:
                self.midi_player = MidiPlayer(available_ports[0])
                self.midi_port_combo['values'] = available_ports
                self.midi_port_combo.set(available_ports[0])
                self._log("MIDI inicializováno úspěšně.")
            else:
                raise ValueError("Žádný dostupný MIDI port.")
        except ImportError as e:
            messagebox.showwarning("MIDI inicializace", "Chybí závislost (např. mido nebo python-rtmidi). MIDI nebude dostupné. Nainstalujte z requirements.txt.")
            self._log(f"CHYBA MIDI importu: {e}")
            self.midi_enabled_var.set(0)  # Vypnout toggle
            self.midi_port_combo.config(state="disabled")  # Zakázat combo
        except ValueError as e:
            messagebox.showwarning("MIDI inicializace", f"{str(e)}\nTip: Nainstalujte virtuální MIDI port jako loopMIDI (pro Windows) nebo IAC Driver (pro Mac) a restartujte aplikaci.")
            self._log(f"CHYBA MIDI portu: {e}")
            self.midi_enabled_var.set(0)
            self.midi_port_combo.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Chyba MIDI", f"Nepodařilo se inicializovat MIDI: {str(e)}\nZkontrolujte instalaci python-rtmidi a MIDI porty.")
            self._log(f"CHYBA MIDI inicializace: {e}")
            self.midi_enabled_var.set(0)
            self.midi_port_combo.config(state="disabled")

    def run(self):
        self.root.mainloop()

    def _init_keyboard_frame(self):
        keyboard_frame = ttk.Frame(self.root, padding=10)
        keyboard_frame.grid(row=0, column=0, sticky="ew")

        keyboard_frame.columnconfigure(0, weight=1)

        keyboard_width = 52 * MusicalConstants.WHITE_KEY_WIDTH
        keyboard_height = 100

        self.canvas = tk.Canvas(keyboard_frame, width=keyboard_width, height=keyboard_height, bg="lightgray")
        self.canvas.grid(row=0, column=0, pady=10)

        self.keyboard = ArchetypeKeyboard(self.canvas, MusicalConstants.ARCHETYPE_SIZE)
        self.keyboard.draw()

    def _init_input_frame(self):
        input_frame = ttk.Labelframe(self.root, text="Ovládání", padding=10)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        ttk.Label(input_frame, text="Akord:").pack(side=tk.LEFT, padx=(0, 5))
        self.chord_entry = ttk.Entry(input_frame, width=15)
        self.chord_entry.pack(side=tk.LEFT, padx=5)
        analyze_btn = ttk.Button(input_frame, text="Analyzovat", command=self.analysis_handler.analyze_harmony)
        analyze_btn.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(analyze_btn, "Analyzuje zadaný akord a zobrazí progrese.")
        ttk.Checkbutton(input_frame, text="Smooth Voicings", variable=self.smooth_var,
                        command=self._on_smooth_voicing_toggle).pack(side=tk.LEFT, padx=10)
        # NOVÉ: MIDI toggle a port výběr
        ttk.Checkbutton(input_frame, text="Enable MIDI Play", variable=self.midi_enabled_var).pack(side=tk.LEFT, padx=10)
        ttk.Label(input_frame, text="MIDI Port:").pack(side=tk.LEFT, padx=(10, 5))
        self.midi_port_combo = ttk.Combobox(input_frame, width=20, state="readonly")
        self.midi_port_combo.pack(side=tk.LEFT, padx=5)
        self.midi_port_combo.bind("<<ComboboxSelected>>", self._on_midi_port_change)
        separator = ttk.Separator(input_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill='y', padx=15, pady=5)
        ttk.Button(input_frame, text="Reset", command=self._reset_gui).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Exportovat Log", command=self._export_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Kopírovat Log", command=self._copy_results).pack(side=tk.LEFT, padx=5)

    def _on_midi_port_change(self, event):
        if self.midi_player:
            try:
                self.midi_player.change_port(self.midi_port_combo.get())
                self._log(f"MIDI port změněn na: {self.midi_port_combo.get()}")
            except ValueError as e:
                messagebox.showerror("Chyba MIDI", str(e))
                self._log(f"CHYBA MIDI portu: {e}")

    def _init_output_notebook(self):
        notebook_frame = ttk.Frame(self.root, padding=10)
        notebook_frame.grid(row=2, column=0, sticky="nsew")
        notebook_frame.rowconfigure(0, weight=1)
        notebook_frame.columnconfigure(0, weight=1)
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        analysis_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(analysis_tab, text="Analysis")
        self.analysis_handler.create_analysis_tab(analysis_tab)
        prog_player_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(prog_player_tab, text="Progression Player")
        self.progression_handler.create_prog_player_tab(prog_player_tab)
        log_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_tab, text="Log")
        self._create_log_tab(log_tab)
        # NOVÉ: Event na změnu tabu pro auto-update display (např. při návratu do progression)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        """Obslouží změnu tabu – aktualizuje display pro progression tab."""
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        if tab_text == "Progression Player" and self.current_progression_chords:
            # Aktualizuj display při přepnutí na progression tab
            self.progression_handler.update_progression_display()
            self._log("Aktualizováno display při přepnutí na Progression Player.")

    def _create_log_tab(self, parent: ttk.Frame):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.log_text = tk.Text(parent, wrap="word", height=10)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _on_smooth_voicing_toggle(self):
        if self.last_displayed_chord_name:
            if DEBUG:
                state = "ON" if self.smooth_var.get() == 1 else "OFF"
                self._log(f"Smooth Voicing prepnuto na: {state}. Prekresluji akord.")
            self._display_chord(self.last_displayed_chord_name)

    def _display_chord(self, chord_full_name: str):
        """Zobrazí akord na klaviatuře a případně přehraje MIDI."""
        try:
            self.last_displayed_chord_name = chord_full_name
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_full_name)
            smooth = self.smooth_var.get() == 1

            if smooth:
                midi_notes = ChordLibrary.get_smooth_voicing(base_note, chord_type, self.prev_chord_midi)
            else:
                midi_notes = ChordLibrary.get_root_voicing(base_note, chord_type)

            self.prev_chord_midi = sorted(midi_notes)
            keys_to_highlight = [ChordLibrary.midi_to_key_nr(note) for note in midi_notes]
            color = "green" if smooth else "red"
            self.keyboard.draw(keys_to_highlight, color=color)

            # Přehraj MIDI (pokud enabled) – přesunutá logika pro optimalizaci
            self._play_current_chord(midi_notes, chord_full_name)
        except (ValueError, IndexError) as e:
            self.last_displayed_chord_name = None
            messagebox.showerror("Chyba zobrazení", str(e))
            self._log(f"CHYBA zobrazení: {e}")
            self.keyboard.clear_highlights()

    def _play_current_chord(self, midi_notes: List[int], chord_name: str):
        """Centralizovaná metoda pro hraní MIDI akordu (optimalizace proti duplicitě)."""
        if self.midi_enabled_var.get() == 1 and self.midi_player:
            try:
                self.midi_player.play_chord(midi_notes, duration=1.0, velocity=100)
                self._log(f"Přehrán MIDI akord: {chord_name}")
            except ValueError as e:
                messagebox.showerror("Chyba MIDI", str(e))
                self._log(f"CHYBA MIDI hraní: {e}")

    def _load_specific_progression(self, chords: List[str], song_name: str):
        self.current_progression_chords = chords
        self.current_progression_index = 0
        self.progression_handler.create_progression_buttons()
        self.progression_handler.update_progression_display()
        self._log(f"Nahrána progrese z písně: {song_name} (chords: {chords})")

    def _step_progression(self, step: int):
        if not self.current_progression_chords: return
        new_index = self.current_progression_index + step
        if 0 <= new_index < len(self.current_progression_chords):
            self.current_progression_index = new_index
            self.progression_handler.update_progression_display()
        elif new_index >= len(self.current_progression_chords):
            self._log("Konec progrese.")
        else:
            self._log("Začátek progrese.")

    def _jump_to_chord(self, index: int):
        self.current_progression_index = index
        self.progression_handler.update_progression_display()

    def _reset_gui(self):
        self.chord_entry.delete(0, tk.END)
        self.keyboard.clear_highlights()
        self.analysis_handler.chord_name_label.config(text="Akord: -")
        self.analysis_handler.chord_notes_label.config(text="Noty: -")
        for item in self.analysis_handler.prog_tree.get_children():
            self.analysis_handler.prog_tree.delete(item)
        self.current_progression_chords = []
        self.current_progression_index = 0
        self.progression_handler.create_progression_buttons()
        self._log("GUI resetováno.")

    def _log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def _export_results(self):
        content = self.log_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Export", "Není co exportovat z logu.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Export", f"Log byl úspěšně uložen do: {file_path}")
            except IOError as e:
                messagebox.showerror("Chyba při ukládání", str(e))

    def _copy_results(self):
        content = self.log_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Kopírování", "Není co kopírovat z logu.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Kopírování", "Obsah logu byl zkopírován do schránky.")

    def _create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.withdraw()
        label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1, padx=5, pady=3)
        label.pack()

        def show_tooltip(event):
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)