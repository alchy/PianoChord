# gui_analysis.py
"""
gui_analysis.py - Komponenty pro analýzu akordů v GUI.
Obsahuje metody pro vytvoření analysis tabu, analýzu a zobrazení výsledků.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from constants import ChordLibrary
from harmony_analyzer import HarmonyAnalyzer
from gui_keyboard import ArchetypeKeyboard

DEBUG = True


class AnalysisHandler:
    """Třída pro zpracování analýzy v GUI. Oddělená pro lepší modularitu."""

    def __init__(self, parent_gui):
        self.parent_gui = parent_gui
        self.chord_name_label = None
        self.chord_notes_label = None
        self.prog_tree = None
        self.prog_tree_data = {}

    def create_analysis_tab(self, parent: ttk.Frame):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)
        chord_info_frame = ttk.Labelframe(parent, text="Chord Info", padding=10)
        chord_info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.chord_name_label = ttk.Label(chord_info_frame, text="Akord: -", font=("Segoe UI", 10, "bold"))
        self.chord_name_label.pack(anchor="w")
        self.chord_notes_label = ttk.Label(chord_info_frame, text="Noty: -")
        self.chord_notes_label.pack(anchor="w")
        prog_frame = ttk.Labelframe(parent, text="Real Progressions (from Jazz Standards)", padding=10)
        prog_frame.grid(row=1, column=0, sticky="nsew")
        prog_frame.rowconfigure(0, weight=1)
        prog_frame.columnconfigure(0, weight=1)
        cols = ("Progression", "Description", "Song", "Transposed")
        self.prog_tree = ttk.Treeview(prog_frame, columns=cols, show="headings")
        for col in cols:
            self.prog_tree.heading(col, text=col)
            self.prog_tree.column(col, width=150, anchor="w")
        self.prog_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(prog_frame, orient="vertical", command=self.prog_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.prog_tree.configure(yscrollcommand=scrollbar.set)
        self.prog_tree.bind("<Double-1>", self._on_prog_double_click)

    def analyze_harmony(self):
        chord_full_name = self.parent_gui.chord_entry.get().strip()
        if not chord_full_name:
            messagebox.showwarning("Vstup", "Zadejte název akordu.")
            return

        try:
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_full_name)
            analysis = HarmonyAnalyzer.analyze(base_note, chord_type)
            self.parent_gui.current_analysis = analysis
            self._display_analysis_results(analysis)
            self.parent_gui._display_chord(chord_full_name)
            self.parent_gui._log(f"Analyzován akord: {chord_full_name}")
        except ValueError as e:
            messagebox.showerror("Chyba analýzy", str(e))
            self.parent_gui._log(f"CHYBA analýzy: {e}")

    def _display_analysis_results(self, analysis: Dict[str, Any]):
        self.chord_name_label.config(text=f"Akord: {analysis['chord_name']}")
        self.chord_notes_label.config(text=f"Noty: {', '.join(analysis['chord_notes'])}")

        for item in self.prog_tree.get_children():
            self.prog_tree.delete(item)
        self.prog_tree_data.clear()

        for i, prog in enumerate(analysis["real_progressions"]):
            transposed = f"By {prog.get('transposed_by', 0)} semitones" if prog.get('transposed_by', 0) > 0 else "Original"
            values = (
                " ".join(prog["chords"]),
                prog["description"],
                prog["song"],
                transposed
            )
            iid = self.prog_tree.insert("", "end", values=values)
            self.prog_tree_data[iid] = prog

    def _on_prog_double_click(self, event):
        """Obslouží double-click na progrese – načte do progression playeru a zobrazení prvního akordu."""
        selected = self.prog_tree.selection()
        if not selected:
            return
        iid = selected[0]
        prog_data = self.prog_tree_data.get(iid)
        if prog_data:
            chords = prog_data.get('chords', [])
            if not chords:
                self.parent_gui._log("Vybraná progrese nemá akordy – nic se nenačítá.")
                return  # Optimalizace: Přeskoč prázdnou progrese
            self.parent_gui._load_specific_progression(chords, prog_data['song'])
            # NOVÉ: Zobraz první akord po načtení (oprava bugu pro zobrazení po výběru z analysis)
            first_chord = chords[0]
            self.parent_gui._display_chord(first_chord)
            # Přehraj MIDI prvního akordu (pokud enabled) – pro okamžitou zpětnou vazbu
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(first_chord)
            midi_notes = ChordLibrary.get_root_voicing(base_note, chord_type)
            self.parent_gui._play_current_chord(midi_notes, first_chord)
            self.parent_gui._log(f"Načtena a zobrazena progrese z analysis: {prog_data['song']}")