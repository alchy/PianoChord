# gui_analysis.py
"""
gui_analysis.py - komponenty pro analýzu akordů v GUI.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from gui_main_window import MainWindow

logger = logging.getLogger(__name__)


class AnalysisHandler:
    """
    Refaktorovaná třída pro zpracování analýzy v GUI.
    OPRAVA: Vrácen správný event handling a přidáno debugging.
    Odpovídá pouze za zobrazení výsledků analýzy.
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
            text="Reálné progrese (z jazzových standardů) - Klik pro výběr, Double-click pro náhled bez zvuku",
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

        # OPRAVA: Správné event handlery
        self.prog_tree.bind("<<TreeviewSelect>>", self._on_progression_select)
        self.prog_tree.bind("<Double-1>", self._on_progression_double_click)

    def display_analysis_results(self, analysis: Dict[str, Any]) -> None:
        """
        Zobrazí výsledky analýzy akordu v GUI.
        Aktualizuje jak informace o akordu, tak seznam progresí.

        Args:
            analysis: Slovník s výsledky analýzy akordu
        """
        # Aktualizace informací o akordu
        self.chord_name_label.config(text=f"Akord: {analysis['chord_name']}")
        self.chord_notes_label.config(text=f"Noty: {', '.join(analysis['chord_notes'])}")

        # Vymazání předchozích progresí
        self._clear_progressions()

        # OPRAVA: Debugging pro progrese
        real_progressions = analysis.get("real_progressions", [])
        logger.debug(f"Zobrazuji {len(real_progressions)} progresí pro akord {analysis['chord_name']}")

        # Naplnění nových progresí
        if real_progressions:
            self._populate_progressions(real_progressions)
            logger.info(f"Zobrazeno {len(real_progressions)} progresí pro akord {analysis['chord_name']}")
        else:
            logger.info(f"Žádné progrese nenalezeny pro akord {analysis['chord_name']}")

        logger.debug(f"Zobrazeny výsledky analýzy pro akord: {analysis['chord_name']}")

    def _clear_progressions(self) -> None:
        """Vymaže všechny progrese z treeview."""
        for item in self.prog_tree.get_children():
            self.prog_tree.delete(item)
        self.prog_tree_data.clear()
        logger.debug("Progrese vymazány z treeview")

    def _populate_progressions(self, progressions: list) -> None:
        """
        Naplní treeview progresemi.
        OPRAVA: Přidáno debugging pro sledování problémů.
        """
        logger.debug(f"Naplňuji treeview s {len(progressions)} progresemi")

        for i, prog in enumerate(progressions):
            try:
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

                logger.debug(f"Vložena progrese {i + 1}: {prog['song']} - {chords_str}")

            except Exception as e:
                logger.error(f"Chyba při vkládání progrese {i}: {e}")
                continue

        logger.debug(f"Treeview naplněn s {len(self.prog_tree_data)} progresemi")

    def _format_transposition_info(self, prog: Dict[str, Any]) -> str:
        """Formátuje informaci o transpozici."""
        transposed_by = prog.get('transposed_by', 0)
        if transposed_by > 0:
            original_key = prog.get('original_key', '')
            transposed_key = prog.get('transposed_key', '')
            return f"+{transposed_by} půltónů ({original_key} → {transposed_key})"
        else:
            return "Originál"

    def _on_progression_select(self, event) -> None:
        """
        NOVÁ METODA: Handler pro výběr progrese (single-click).
        Pouze loguje výběr bez dalších akcí.
        """
        selected_items = self.prog_tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        prog_data = self.prog_tree_data.get(item_id)

        if prog_data:
            song_name = prog_data['song']
            chords_str = " → ".join(prog_data['chords'])
            logger.debug(f"Vybrána progrese: {song_name} - {chords_str}")

    def _on_progression_double_click(self, event) -> None:
        """
        OPRAVA: Obsluha double-click na progrese.
        Nyní pouze zobrazuje progrese vizuálně BEZ MIDI přehrávání.
        Pro plné přehrávání s MIDI musí uživatel přejít do Progression Playeru.
        """
        selected_items = self.prog_tree.selection()
        if not selected_items:
            logger.debug("Double-click na progrese, ale žádná položka není vybrána")
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

        # OPRAVA: Načte progrese do aplikace (bez MIDI při načítání)
        song_name = prog_data['song']
        transposed_info = ""
        if prog_data.get('transposed_by', 0) > 0:
            transposed_info = f" (transpozice +{prog_data['transposed_by']})"

        source_description = f"{song_name}{transposed_info} (z analýzy - náhled)"

        self.main_window.load_progression(chords, source_description)

        # OPRAVA: Zobrazí první akord pouze VIZUÁLNĚ (bez MIDI)
        first_chord = chords[0]
        if self.main_window.chord_display_manager:
            self.main_window.chord_display_manager.display_chord_visual_only(first_chord)

        # Informační zpráva pro uživatele
        self.main_window.app_state.log(
            f"Náhled progrese z analýzy: {song_name} (pro přehrávání přejděte na Progression Player)"
        )

        logger.info(f"Nahrána progrese z analýzy (náhled): {song_name} - {len(chords)} akordů")

    def reset_display(self) -> None:
        """Resetuje zobrazení analýzy do výchozího stavu."""
        if self.chord_name_label:
            self.chord_name_label.config(text="Akord: -")

        if self.chord_notes_label:
            self.chord_notes_label.config(text="Noty: -")

        if self.prog_tree:
            self._clear_progressions()

        logger.debug("Zobrazení analýzy resetováno")

    def get_debug_info(self) -> Dict[str, Any]:
        """
        NOVÁ METODA: Vrací debug informace pro řešení problémů.
        """
        return {
            "prog_tree_exists": self.prog_tree is not None,
            "prog_tree_data_count": len(self.prog_tree_data),
            "treeview_items_count": len(self.prog_tree.get_children()) if self.prog_tree else 0,
        }