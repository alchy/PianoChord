# gui/analysis_view.py
"""
gui/analysis_view.py - Refaktorovaný komponenty pro analýzu akordů v GUI.
KLÍČOVÁ NOVINKA: Dynamické žánrové záložky místo jednoho seznamu progresí.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from core.progression_manager import ProgressionManager
    from core.app_state import ApplicationState

logger = logging.getLogger(__name__)


class AnalysisView:
    """
    Refaktorovaná třída pro zpracování analýzy v GUI.
    NOVINKA: Vytváří dynamické žánrové záložky podle obsahu databáze.
    """

    def __init__(self, progression_manager: 'ProgressionManager', app_state: 'ApplicationState'):
        """
        Inicializuje AnalysisView s referencemi na progression manager a stav.

        Args:
            progression_manager: Instance ProgressionManager
            app_state: Instance ApplicationState
        """
        self.progression_manager = progression_manager
        self.app_state = app_state

        # GUI komponenty
        self.chord_name_label: Optional[tk.Label] = None
        self.chord_notes_label: Optional[tk.Label] = None
        self.genre_notebook: Optional[ttk.Notebook] = None

        # Data pro genre treeviews
        self.genre_trees: Dict[str, ttk.Treeview] = {}
        self.genre_tree_data: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Callbacks (nastavuje MainWindow)
        self.on_progression_selected: Optional[Callable[[list, str], None]] = None
        self.on_progression_preview: Optional[Callable[[list, str], None]] = None

        logger.debug("AnalysisView inicializován")

    def create_analysis_tab(self, parent: ttk.Frame) -> None:
        """
        Vytvoří tab pro analýzu akordů s žánrovými záložkami.

        Args:
            parent: Rodičovský frame pro celý tab
        """
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        # Sekce s informacemi o akordu
        self._create_chord_info_section(parent)

        # NOVINKA: Sekce s žánrovými záložkami místo jednoho seznamu
        self._create_genres_section(parent)

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

    def _create_genres_section(self, parent: ttk.Frame) -> None:
        """
        KLÍČOVÁ NOVINKA: Vytvoří sekci s dynamickými žánrovými záložkami.
        Místo jednoho TreeView vytvoří Notebook s záložkami podle žánrů.
        """
        genres_frame = ttk.Labelframe(
            parent,
            text="Reálné progrese podle žánrů - Klik pro výběr, Double-click pro náhled",
            padding=10
        )
        genres_frame.grid(row=1, column=0, sticky="nsew")
        genres_frame.rowconfigure(0, weight=1)
        genres_frame.columnconfigure(0, weight=1)

        # Notebook pro žánrové záložky
        self.genre_notebook = ttk.Notebook(genres_frame)
        self.genre_notebook.grid(row=0, column=0, sticky="nsew")

        # Vytvoří záložky podle žánrů v databázi
        self._create_genre_tabs()

    def _create_genre_tabs(self) -> None:
        """
        Dynamicky vytvoří záložky podle žánrů nalezených v databázi.
        """
        if not self.genre_notebook:
            return

        try:
            # Získá žánry z databáze
            genres = self.progression_manager.get_genres()
            logger.info(f"Vytvářím {len(genres)} žánrových záložek: {list(genres.keys())}")

            for genre, songs in genres.items():
                # Vytvoří frame pro tento žánr
                genre_frame = ttk.Frame(self.genre_notebook)

                # Převede název žánru na čitelný titulek
                tab_title = self._format_genre_title(genre)

                # Přidá záložku
                self.genre_notebook.add(genre_frame, text=f"{tab_title} ({len(songs)})")

                # Vytvoří TreeView pro tento žánr
                self._create_genre_treeview(genre_frame, genre)

            logger.info("Žánrové záložky úspěšně vytvořeny")

        except Exception as e:
            logger.error(f"Chyba při vytváření žánrových záložek: {e}")
            # Fallback - vytvoří jednu záložku "Všechny"
            self._create_fallback_tab()

    def _format_genre_title(self, genre: str) -> str:
        """
        Převede název žánru na čitelný titulek pro záložku.

        Args:
            genre: Název žánru z databáze (např. "jazz-standard")

        Returns:
            str: Formátovaný titulek (např. "Jazz Standard")
        """
        return genre.replace('-', ' ').replace('_', ' ').title()

    def _create_genre_treeview(self, parent: ttk.Frame, genre: str) -> None:
        """
        Vytvoří TreeView pro konkrétní žánr.

        Args:
            parent: Rodičovský frame
            genre: Název žánru
        """
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        # Sloupce pro TreeView
        columns = ("Progrese", "Popis", "Píseň", "Transpozice")
        tree = ttk.Treeview(parent, columns=columns, show="headings")

        # Nastavení sloupců
        column_widths = {"Progrese": 200, "Popis": 250, "Píseň": 150, "Transpozice": 100}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths.get(col, 150), anchor="w")

        tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)

        # Event handlers
        tree.bind("<<TreeviewSelect>>", lambda e: self._on_progression_select(tree, genre))
        tree.bind("<Double-1>", lambda e: self._on_progression_double_click(tree, genre))

        # Uloží referenci na tree
        self.genre_trees[genre] = tree
        self.genre_tree_data[genre] = {}

        logger.debug(f"TreeView vytvořen pro žánr: {genre}")

    def _create_fallback_tab(self) -> None:
        """Vytvoří fallback záložku pokud selže načtení žánrů."""
        if not self.genre_notebook:
            return

        fallback_frame = ttk.Frame(self.genre_notebook)
        self.genre_notebook.add(fallback_frame, text="Všechny progrese")

        # Vytvoří jednoduché TreeView
        self._create_genre_treeview(fallback_frame, "all")

        logger.warning("Vytvořena fallback záložka pro všechny progrese")

    def display_analysis_results(self, analysis: Dict[str, Any]) -> None:
        """
        Zobrazí výsledky analýzy akordu v GUI s rozdělením do žánrových záložek.

        Args:
            analysis: Slovník s výsledky analýzy akordu
        """
        # Aktualizace informací o akordu
        chord_name = analysis.get('chord_name', 'Unknown')
        chord_notes = analysis.get('chord_notes', [])

        if self.chord_name_label:
            self.chord_name_label.config(text=f"Akord: {chord_name}")
        if self.chord_notes_label:
            self.chord_notes_label.config(text=f"Noty: {', '.join(chord_notes)}")

        # Vymazání předchozích progresí ze všech žánrů
        self._clear_all_progressions()

        # Rozdělení progresí podle žánrů
        real_progressions = analysis.get("real_progressions", [])
        logger.debug(f"Zpracovávám {len(real_progressions)} progresí pro akord {chord_name}")

        if real_progressions:
            self._populate_progressions_by_genre(real_progressions)
            logger.info(f"Zobrazeno {len(real_progressions)} progresí pro akord {chord_name}")
        else:
            logger.info(f"Žádné progrese nenalezeny pro akord {chord_name}")

    def _clear_all_progressions(self) -> None:
        """Vymaže všechny progrese ze všech žánrových TreeViews."""
        for genre, tree in self.genre_trees.items():
            for item in tree.get_children():
                tree.delete(item)
            if genre in self.genre_tree_data:
                self.genre_tree_data[genre].clear()
        logger.debug("Všechny progrese vymazány ze všech žánrů")

    def _populate_progressions_by_genre(self, progressions: list) -> None:
        """
        KLÍČOVÁ FUNKCE: Rozdělí progrese podle žánrů do příslušných záložek.

        Args:
            progressions: Seznam všech progresí nalezených pro akord
        """
        logger.debug(f"Rozdělují {len(progressions)} progresí podle žánrů")

        # Seskupí progrese podle žánrů
        progressions_by_genre = {}
        unknown_genre_progressions = []

        for prog in progressions:
            genre = prog.get('genre', 'unknown')
            if genre not in progressions_by_genre:
                progressions_by_genre[genre] = []
            progressions_by_genre[genre].append(prog)

        # Naplní každý žánr jeho progresemi
        for genre, genre_progressions in progressions_by_genre.items():
            if genre in self.genre_trees:
                self._populate_genre_treeview(genre, genre_progressions)
            else:
                logger.warning(f"Žánr '{genre}' nemá svou záložku, progrese budou přidány do 'unknown'")
                unknown_genre_progressions.extend(genre_progressions)

        # Pokud existují progrese neznámého žánru, zkusí je přidat do 'all' nebo 'unknown' záložky
        if unknown_genre_progressions:
            if 'all' in self.genre_trees:
                self._populate_genre_treeview('all', unknown_genre_progressions)
            elif 'unknown' in self.genre_trees:
                self._populate_genre_treeview('unknown', unknown_genre_progressions)

        logger.info(f"Progrese rozděleny do {len(progressions_by_genre)} žánrů")

    def _populate_genre_treeview(self, genre: str, progressions: list) -> None:
        """
        Naplní konkrétní žánrový TreeView progresemi.

        Args:
            genre: Název žánru
            progressions: Seznam progresí pro tento žánr
        """
        tree = self.genre_trees.get(genre)
        if not tree:
            logger.warning(f"TreeView pro žánr '{genre}' neexistuje")
            return

        logger.debug(f"Naplňuji TreeView pro žánr '{genre}' s {len(progressions)} progresemi")

        for i, prog in enumerate(progressions):
            try:
                # Formátování dat pro zobrazení
                chords_str = " → ".join(prog.get("chords", []))
                description = prog.get("description", "")
                song = prog.get("song", "Unknown")
                transposed_str = self._format_transposition_info(prog)

                values = (chords_str, description, song, transposed_str)

                # Vložení do TreeView
                item_id = tree.insert("", "end", values=values)

                # Uložení dat pro event handling
                if genre not in self.genre_tree_data:
                    self.genre_tree_data[genre] = {}
                self.genre_tree_data[genre][item_id] = prog

                logger.debug(f"Vložena progrese {i + 1} do žánru {genre}: {song} - {chords_str}")

            except Exception as e:
                logger.error(f"Chyba při vkládání progrese {i} do žánru {genre}: {e}")
                continue

        logger.debug(f"TreeView pro žánr '{genre}' naplněn s {len(progressions)} progresemi")

    def _format_transposition_info(self, prog: Dict[str, Any]) -> str:
        """Formátuje informaci o transpozici."""
        transposed_by = prog.get('transposed_by', 0)
        if transposed_by > 0:
            original_key = prog.get('original_key', '')
            transposed_key = prog.get('transposed_key', '')
            return f"+{transposed_by} půltónů ({original_key} → {transposed_key})"
        else:
            return "Originál"

    def _on_progression_select(self, tree: ttk.Treeview, genre: str) -> None:
        """
        Handler pro výběr progrese (single-click).

        Args:
            tree: TreeView ze kterého byla progrese vybrána
            genre: Název žánru
        """
        selected_items = tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        prog_data = self.genre_tree_data.get(genre, {}).get(item_id)

        if prog_data:
            song_name = prog_data.get('song', 'Unknown')
            chords_str = " → ".join(prog_data.get('chords', []))
            logger.debug(f"Vybrána progrese ze žánru '{genre}': {song_name} - {chords_str}")

            # Callback pro výběr progrese
            if self.on_progression_selected:
                chords = prog_data.get('chords', [])
                source_name = f"{song_name} ({genre})"
                self.on_progression_selected(chords, source_name)

    def _on_progression_double_click(self, tree: ttk.Treeview, genre: str) -> None:
        """
        Handler pro double-click na progrese.
        Načte progrese pro náhled (bez MIDI přehrávání).

        Args:
            tree: TreeView ze kterého byla progrese vybrána
            genre: Název žánru
        """
        selected_items = tree.selection()
        if not selected_items:
            logger.debug("Double-click na progrese, ale žádná položka není vybrána")
            return

        item_id = selected_items[0]
        prog_data = self.genre_tree_data.get(genre, {}).get(item_id)

        if not prog_data:
            logger.warning("Nenalezena data pro vybranou progrese")
            return

        chords = prog_data.get('chords', [])
        if not chords:
            self.app_state.log("Vybraná progrese nemá akordy - nelze nahrát")
            return

        # Vytvoří popis zdroje
        song_name = prog_data.get('song', 'Unknown')
        genre_title = self._format_genre_title(genre)

        transposed_info = ""
        if prog_data.get('transposed_by', 0) > 0:
            transposed_info = f" (transpozice +{prog_data['transposed_by']})"

        source_description = f"{song_name} - {genre_title}{transposed_info} (náhled z analýzy)"

        # Callback pro náhled progrese
        if self.on_progression_preview:
            self.on_progression_preview(chords, source_description)

        # Informační zpráva pro uživatele
        self.app_state.log(
            f"Náhled progrese: {song_name} ze žánru {genre_title} "
            f"(pro přehrávání přejděte na Progression Player)"
        )

        logger.info(f"Nahrána progrese pro náhled ze žánru {genre}: {song_name} - {len(chords)} akordů")

    def get_active_genre_stats(self) -> Dict[str, int]:
        """
        Vrací statistiky o progresích v aktivních záložkách.

        Returns:
            Dict[str, int]: Počty progresí podle žánrů
        """
        stats = {}
        for genre, tree in self.genre_trees.items():
            count = len(tree.get_children())
            if count > 0:
                stats[genre] = count
        return stats

    def switch_to_genre(self, genre: str) -> bool:
        """
        Přepne na záložku konkrétního žánru.

        Args:
            genre: Název žánru

        Returns:
            bool: True pokud byl přepne úspěšný
        """
        if not self.genre_notebook:
            return False

        # Najde index záložky podle názvu žánru
        for i in range(self.genre_notebook.index("end")):
            tab_text = self.genre_notebook.tab(i, "text")
            if genre in tab_text.lower():
                self.genre_notebook.select(i)
                logger.debug(f"Přepnuto na záložku žánru: {genre}")
                return True

        logger.warning(f"Záložka pro žánr '{genre}' nenalezena")
        return False

    def get_current_genre(self) -> Optional[str]:
        """
        Vrací název aktuálně aktivního žánru.

        Returns:
            Optional[str]: Název žánru nebo None
        """
        if not self.genre_notebook:
            return None

        try:
            current_tab = self.genre_notebook.select()
            tab_text = self.genre_notebook.tab(current_tab, "text")

            # Extrahuje název žánru z textu záložky (před závorkou s počtem)
            genre_title = tab_text.split(" (")[0].strip()

            # Převede zpět na formát databáze
            return genre_title.lower().replace(' ', '-')

        except Exception as e:
            logger.error(f"Chyba při zjišťování aktuálního žánru: {e}")
            return None

    def reset_display(self) -> None:
        """Resetuje zobrazení analýzy do výchozího stavu."""
        if self.chord_name_label:
            self.chord_name_label.config(text="Akord: -")

        if self.chord_notes_label:
            self.chord_notes_label.config(text="Noty: -")

        self._clear_all_progressions()

        logger.debug("Zobrazení analýzy resetováno")

    def refresh_genre_tabs(self) -> None:
        """
        Obnoví žánrové záložky (užitečné při změně databáze).
        """
        if not self.genre_notebook:
            return

        # Vymaže všechny současné záložky
        for tab_id in self.genre_notebook.tabs():
            self.genre_notebook.forget(tab_id)

        # Vyčistí data
        self.genre_trees.clear()
        self.genre_tree_data.clear()

        # Vytvoří nové záložky
        self._create_genre_tabs()

        logger.info("Žánrové záložky obnoveny")

    def get_debug_info(self) -> Dict[str, Any]:
        """
        Vrací debug informace pro řešení problémů.

        Returns:
            Dict[str, Any]: Debug informace o AnalysisView
        """
        return {
            "genre_notebook_exists": self.genre_notebook is not None,
            "genre_trees_count": len(self.genre_trees),
            "genre_trees": list(self.genre_trees.keys()),
            "current_genre": self.get_current_genre(),
            "genre_stats": self.get_active_genre_stats(),
            "callbacks_set": {
                "progression_selected": self.on_progression_selected is not None,
                "progression_preview": self.on_progression_preview is not None
            }
        }
