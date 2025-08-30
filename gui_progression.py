# gui_progression.py
"""
gui_progression.py - Komponenty pro progression player v GUI.
Obsahuje metody pro vytvoření tabu, načítání a procházení progresí.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List

from jazz_database import JazzStandardsDatabase
from constants import ChordLibrary  # NOVÉ: Pro MIDI noty
from harmony_analyzer import HarmonyAnalyzer  # NOVÉ: Pro parse

DEBUG = True


class ProgressionHandler:
    """Třída pro zpracování progresí v GUI."""

    def __init__(self, parent_gui):
        self.parent_gui = parent_gui
        self.song_combo = None
        self.prog_chord_frame = None
        self.current_chord_label = None
        self.prog_chord_buttons = []

    def create_prog_player_tab(self, parent: ttk.Frame):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)
        control_frame = ttk.Frame(parent, padding=10)
        control_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(control_frame, text="Vyberte píseň:").pack(side=tk.LEFT, padx=5)
        songs = JazzStandardsDatabase.get_all_songs()
        self.song_combo = ttk.Combobox(control_frame, values=sorted(songs), width=30)
        self.song_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Načíst celou píseň", command=self._load_progression_from_combo).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exportovat progrese", command=self._export_progression).pack(side=tk.LEFT, padx=5)
        self.prog_chord_frame = ttk.Labelframe(parent, text="Aktuální progrese", padding=10)
        self.prog_chord_frame.grid(row=1, column=0, sticky="nsew")

    def _load_progression_from_combo(self):
        song_name = self.song_combo.get()
        if not song_name or song_name.startswith("Nahráno:"):
            messagebox.showinfo("Výběr", "Vyberte píseň ze seznamu pro nahrání celé skladby.")
            return
        song_data = JazzStandardsDatabase.get_song_info(song_name)
        if not song_data: return
        all_chords = [chord for prog in song_data["progressions"] for chord in prog["chords"]]
        self.parent_gui._load_specific_progression(all_chords, song_name)

    def _export_progression(self):
        if not self.parent_gui.current_progression_chords:
            messagebox.showinfo("Export", "Žádná progrese k exportu.")
            return
        content = "\n".join(self.parent_gui.current_progression_chords)
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Export", f"Progrese uložena do: {file_path}")

    def create_progression_buttons(self):
        for widget in self.prog_chord_frame.winfo_children(): widget.destroy()
        if not self.parent_gui.current_progression_chords: return
        control_frame = ttk.Frame(self.prog_chord_frame)
        control_frame.pack(fill="x", pady=5)
        ttk.Button(control_frame, text="<< Prev", command=lambda: self.parent_gui._step_progression(-1)).pack(side=tk.LEFT, padx=5)
        self.current_chord_label = ttk.Label(control_frame, text="-", font=("Segoe UI", 12, "bold"), width=15,
                                             anchor="center")
        self.current_chord_label.pack(side=tk.LEFT, expand=True, fill="x")
        ttk.Button(control_frame, text="Next >>", command=lambda: self.parent_gui._step_progression(1)).pack(side=tk.LEFT, padx=5)
        buttons_frame = ttk.Frame(self.prog_chord_frame)
        buttons_frame.pack(fill="both", expand=True)
        self.prog_chord_buttons = []
        for i, chord in enumerate(self.parent_gui.current_progression_chords):
            btn = ttk.Button(buttons_frame, text=chord, command=lambda idx=i, ch=chord: self._handle_chord_click(idx, ch))
            btn.grid(row=i // 8, column=i % 8, padx=2, pady=2, sticky="ew")
            self.prog_chord_buttons.append(btn)

    def _handle_chord_click(self, index: int, chord: str):
        """Obslouží klik na akord – skok a případné hraní MIDI (s použitím centralizované metody)."""
        self.parent_gui._jump_to_chord(index)
        if self.parent_gui.midi_enabled_var.get() == 1 and self.parent_gui.midi_player:
            try:
                base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord)
                midi_notes = ChordLibrary.get_root_voicing(base_note, chord_type)  # Použij root pro hraní
                self.parent_gui._play_current_chord(midi_notes, chord)  # Optimalizace: Použití centralizované metody
            except ValueError as e:
                messagebox.showerror("Chyba MIDI", str(e))
                self.parent_gui._log(f"CHYBA MIDI hraní v progrese: {e}")

    def update_progression_display(self):
        if not self.parent_gui.current_progression_chords: return
        style_name = "Accent.TButton"
        style = ttk.Style()
        style.configure(style_name, foreground="blue", font=('Segoe UI', 9, 'bold'))
        for i, btn in enumerate(self.prog_chord_buttons):
            btn.configure(style=style_name if i == self.parent_gui.current_progression_index else "TButton")
        current_chord = self.parent_gui.current_progression_chords[self.parent_gui.current_progression_index]
        self.current_chord_label.config(text=current_chord)
        self.parent_gui._display_chord(current_chord)
        self.parent_gui._log(f"Zobrazen akord: {current_chord}")