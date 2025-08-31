# gui_analysis.py
"""
gui_analysis.py - Refaktorované komponenty pro analýzu akordů v GUI.
Zjednodušeno pro lepší čitelnost a údržbu.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from main_window import MainWindow

logger = logging.getLogger(__name__)


class AnalysisHandler:
    """
    Refaktorovaná třída pro zpracování analýzy v GUI.
    Zodpovídá pouze za zobrazení výsledků analýzy.
    """

    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window

        # GUI komponenty
        self.chord_name_label: tk.Label = None
        self.chord_notes_label: tk.Label = None
        self.prog_tree: ttk.Treeview = None

        # Data pro treeview
        self.prog_tree_data: Dict[str, Dict[str, Any]] = {}

    def create_analysis_tab(self, parent: ttk.Frame) -> None:
        """Vytvoří tab pro analýzu akordů."""
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        # Sekce s informacemi o akordu
        self._create_chord_info_section(parent)

        # Sekce s progresemi
        self._create_progressions_section(parent)

    def _create_chord_info_section(self, parent: ttk.Frame) -> None:
        """Vytvoří sekci s informacemi o aktuálním akordu."""
        chord_info_frame = ttk.Labelframe(parent, text="Informace o akordu", padding=10)
        chord_info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.chord_name_label = ttk.Label(
            chord_info_frame,
            text="Akord: -",
            font=("Segoe UI", 10, "bold")
        )
        self.chord_name_label.pack(anchor="w")

        self.chord_notes_label = ttk.Label(chord_info_frame, text="Noty: -")
        self.chord_notes_label.pack(anchor="w")

    def _create_progressions_section(self, parent: ttk.Frame) -> None:
        """Vytvoří sekci se seznamem progresí."""
        prog_frame = ttk.Labelframe(
            parent,
            text="Reálné progrese (z jazzových standardů)",
            padding=10
        )
        prog_frame.grid(row=1, column=0, sticky="nsew")
        prog_frame.rowconfigure(0, weight=1)
        prog_frame.columnconfigure(0, weight=1)

        # Treeview pro progrese
        columns = ("Progrese", "Popis", "Píseň", "Transpozice")
        self.prog_tree = ttk.Treeview(prog_frame, columns=columns, show="headings")

        # Nastavení sloupců
        column_widths = {"Progrese": 200, "Popis": 250, "Píseň": 150, "Transpozice": 100}
        for col in columns:
            self.prog_tree.heading(col, text=col)
            self.prog_tree.column(col, width=column_widths.get(col, 150), anchor="w")

        self.prog_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar pro treeview
        scrollbar = ttk.Scrollbar(prog_frame, orient="vertical", command=self.prog_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.prog_tree.configure(yscrollcommand=scrollbar.set)

        # Event handler pro double-click
        self.prog_tree.bind("<Double-1>", self._on_progression_double_click)

    def display_analysis_results(self, analysis: Dict[str, Any]) -> None:
        """
        Zobrazí výsledky analýzy akordu v GUI.
        Aktualizuje jak informace o akordu, tak seznam progresí.
        """
        # Aktualizace informací o akordu
        self.chord_name_label.config(text=f"Akord: {analysis['chord_name']}")
        self.chord_notes_label.config(text=f"Noty: {', '.join(analysis['chord_notes'])}")

        # Vymazání předchozích progresí
        self._clear_progressions()

        # Naplnění nových progresí
        self._populate_progressions(analysis["real_progressions"])

        logger.debug(f"Zobrazeny výsledky analýzy pro akord: {analysis['chord_name']}")

    def _clear_progressions(self) -> None:
        """Vymaže všechny progrese z treeview."""
        for item in self.prog_tree.get_children():
            self.prog_tree.delete(item)
        self.prog_tree_data.clear()

    def _populate_progressions(self, progressions: list) -> None:
        """Naplní treeview progresemi."""
        for prog in progressions:
            # Formátování dat pro zobrazení
            chords_str = " → ".join(prog["chords"])
            transposed_str = self._format_transposition_info(prog)

            values = (
                chords_str,
                prog["description"],
                prog["song"],
                transposed_str
            )

            # Vložení do treeview
            item_id = self.prog_tree.insert("", "end", values=values)
            self.prog_tree_data[item_id] = prog

    def _format_transposition_info(self, prog: Dict[str, Any]) -> str:
        """Formátuje informaci o transpozici."""
        transposed_by = prog.get('transposed_by', 0)
        if transposed_by > 0:
            return f"+{transposed_by} půltónů"
        else:
            return "Originál"

    def _on_progression_double_click(self, event) -> None:
        """
        Obslužná metoda pro double-click na progrese.
        Nahraje vybranou progrese do progression playeru.
        """
        selected_items = self.prog_tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        prog_data = self.prog_tree_data.get(item_id)

        if not prog_data:
            logger.warning("Nenalezena data pro vybranou progrese")
            return

        chords = prog_data.get('chords', [])
        if not chords:
            self.main_window.app_state.log("Vybraná progrese nemá akordy - nelze nahrát")
            return

        # Načte progrese do aplikace
        song_name = prog_data['song']
        self.main_window.load_progression(chords, f"{song_name} (z analýzy)")

        # Zobrazí první akord
        first_chord = chords[0]
        self.main_window._display_chord_on_keyboard(first_chord)

        logger.info(f"Nahraná progrese z analýzy: {song_name}")

    def reset_display(self) -> None:
        """Resetuje zobrazení analýzy do výchozího stavu."""
        if self.chord_name_label:
            self.chord_name_label.config(text="Akord: -")

        if self.chord_notes_label:
            self.chord_notes_label.config(text="Noty: -")

        if self.prog_tree:
            self._clear_progressions()

        logger.debug("Zobrazení analýzy resetováno")
