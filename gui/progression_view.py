# gui/progression_view.py
"""
gui/progression_view.py - Refaktorované komponenty pro progression player v GUI.
Čistá GUI vrstva pro přehrávání progresí s integrovanou žánrovou podporou.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Callable, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from core.progression_manager import ProgressionManager
    from core.app_state import ApplicationState

logger = logging.getLogger(__name__)


class ProgressionView:
    """
    Refaktorovaná třída pro zpracování progresí v GUI.
    Obsahuje progression player tab s podporou žánrového filtrování.
    """

    def __init__(self, progression_manager: 'ProgressionManager', app_state: 'ApplicationState'):
        """
        Inicializuje ProgressionView s referencemi na progression manager a stav.

        Args:
            progression_manager: Instance ProgressionManager
            app_state: Instance ApplicationState
        """
        self.progression_manager = progression_manager
        self.app_state = app_state

        # GUI komponenty
        self.song_combo: Optional[ttk.Combobox] = None
        self.genre_filter_combo: Optional[ttk.Combobox] = None
        self.prog_chord_frame: Optional[ttk.Frame] = None
        self.current_chord_label: Optional[ttk.Label] = None
        self.progression_info_label: Optional[ttk.Label] = None
        self.prog_chord_buttons: List[ttk.Button] = []

        # Callbacks (nastavuje MainWindow)
        self.on_step_progression: Optional[Callable[[int], None]] = None
        self.on_jump_to_chord: Optional[Callable[[int], None]] = None
        self.on_load_progression: Optional[Callable[[list, str], None]] = None

        # Cache pro rychlejší filtrování
        self._all_songs_cache: List[str] = []
        self._filtered_songs_cache: List[str] = []

        logger.debug("ProgressionView inicializován")

    def create_prog_player_tab(self, parent: ttk.Frame) -> None:
        """
        Vytvoří tab pro progression player.

        Args:
            parent: Rodičovský frame
        """
        parent.rowconfigure(2, weight=1)  # Progression section má weight
        parent.columnconfigure(0, weight=1)

        # Control frame s výběrem písně a filtrem žánrů
        self._create_control_section(parent)

        # Info frame s informacemi o aktuální progresi
        self._create_info_section(parent)

        # Frame pro zobrazení aktuální progrese
        self._create_progression_section(parent)

    def _create_control_section(self, parent: ttk.Frame) -> None:
        """Vytvoří ovládací sekci s výběrem písně a filtrem žánrů."""
        control_frame = ttk.Frame(parent, padding=10)
        control_frame.grid(row=0, column=0, sticky="ew")

        # První řádek - filtr žánrů
        genre_row = ttk.Frame(control_frame)
        genre_row.pack(fill="x", pady=(0, 5))

        ttk.Label(genre_row, text="Filtr žánru:").pack(side=tk.LEFT, padx=5)

        self.genre_filter_combo = ttk.Combobox(genre_row, width=20, state="readonly")
        self.genre_filter_combo.pack(side=tk.LEFT, padx=5)
        self.genre_filter_combo.bind("<<ComboboxSelected>>", self._on_genre_filter_changed)

        ttk.Button(
            genre_row,
            text="Vše",
            command=self._clear_genre_filter
        ).pack(side=tk.LEFT, padx=5)

        # Druhý řádek - výběr písně a akce
        song_row = ttk.Frame(control_frame)
        song_row.pack(fill="x")

        ttk.Label(song_row, text="Vyberte píseň:").pack(side=tk.LEFT, padx=5)

        self.song_combo = ttk.Combobox(song_row, width=40, state="readonly")
        self.song_combo.pack(side=tk.LEFT, padx=5)

        # Tlačítka pro ovládání
        ttk.Button(
            song_row,
            text="Nahrát celou píseň",
            command=self._load_progression_from_combo
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            song_row,
            text="Exportovat progrese",
            command=self._export_progression
        ).pack(side=tk.LEFT, padx=5)

        # Inicializace combo boxů
        self._populate_genre_filter()
        self._populate_songs_combo()

    def _create_info_section(self, parent: ttk.Frame) -> None:
        """Vytvoří informační sekci o aktuální progresi."""
        info_frame = ttk.Labelframe(parent, text="Informace o progresi", padding=5)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(5, 10))

        self.progression_info_label = ttk.Label(
            info_frame,
            text="Žádná progrese není načtena",
            font=("Segoe UI", 9)
        )
        self.progression_info_label.pack(anchor="w")

    def _create_progression_section(self, parent: ttk.Frame) -> None:
        """Vytvoří sekci pro zobrazení aktuální progrese."""
        self.prog_chord_frame = ttk.Labelframe(parent, text="Aktuální progrese", padding=10)
        self.prog_chord_frame.grid(row=2, column=0, sticky="nsew")

        # Placeholder text
        placeholder = ttk.Label(
            self.prog_chord_frame,
            text="Nahrajte progrese pro zobrazení akordů",
            foreground="gray"
        )
        placeholder.pack(expand=True)

    def _populate_genre_filter(self) -> None:
        """Naplní combo box s filtrem žánrů."""
        if not self.genre_filter_combo:
            return

        try:
            genres = self.progression_manager.get_genres()
            genre_titles = [self._format_genre_title(genre) for genre in genres.keys()]
            genre_titles.sort()

            self.genre_filter_combo['values'] = genre_titles
            logger.debug(f"Filtr žánrů naplněn s {len(genre_titles)} žánry")

        except Exception as e:
            logger.error(f"Chyba při naplňování filtru žánrů: {e}")
            self.genre_filter_combo['values'] = []

    def _populate_songs_combo(self, genre_filter: str = None) -> None:
        """
        Naplní combo box s písněmi, volitelně filtrované podle žánru.

        Args:
            genre_filter: Název žánru pro filtrování (None = všechny písně)
        """
        if not self.song_combo:
            return

        try:
            if genre_filter:
                # Filtrované písně podle žánru
                genre_key = self._genre_title_to_key(genre_filter)
                songs = self.progression_manager.get_songs_by_genre(genre_key)
                self._filtered_songs_cache = sorted(songs)
                self.song_combo['values'] = self._filtered_songs_cache
                logger.debug(f"Songs combo filtrován pro žánr '{genre_filter}': {len(songs)} písní")
            else:
                # Všechny písně (jen originální, ne transponované)
                all_songs = []
                for song_name in self.progression_manager.get_all_songs():
                    if not song_name.endswith(('_trans_1', '_trans_2', '_trans_3', '_trans_4',
                                               '_trans_5', '_trans_6', '_trans_7', '_trans_8',
                                               '_trans_9', '_trans_10', '_trans_11')):
                        all_songs.append(song_name)

                self._all_songs_cache = sorted(all_songs)
                self.song_combo['values'] = self._all_songs_cache
                logger.debug(f"Songs combo naplněn se všemi písněmi: {len(all_songs)} písní")

        except Exception as e:
            logger.error(f"Chyba při naplňování songs combo: {e}")
            self.song_combo['values'] = []

    def _format_genre_title(self, genre: str) -> str:
        """Převede název žánru na čitelný titulek."""
        return genre.replace('-', ' ').replace('_', ' ').title()

    def _genre_title_to_key(self, genre_title: str) -> str:
        """Převede titulek žánru zpět na klíč databáze."""
        return genre_title.lower().replace(' ', '-')

    def _on_genre_filter_changed(self, event=None) -> None:
        """Handler pro změnu filtru žánrů."""
        selected_genre = self.genre_filter_combo.get()
        if selected_genre:
            self._populate_songs_combo(selected_genre)
            logger.info(f"Filtr žánru změněn na: {selected_genre}")
        else:
            self._populate_songs_combo()

    def _clear_genre_filter(self) -> None:
        """Vyčistí filtr žánrů a zobrazí všechny písně."""
        if self.genre_filter_combo:
            self.genre_filter_combo.set("")
        self._populate_songs_combo()
        logger.info("Filtr žánrů vyčištěn - zobrazeny všechny písně")

    def _load_progression_from_combo(self) -> None:
        """Nahraje progrese z vybrané písně."""
        song_name = self.song_combo.get()

        if not song_name:
            messagebox.showinfo("Výběr", "Vyberte píseň ze seznamu pro nahrání celé skladby.")
            return

        try:
            song_data = self.progression_manager.get_song_info(song_name)
            if not song_data:
                messagebox.showerror("Chyba", f"Nenalezena data pro píseň: {song_name}")
                return

            # Spojí všechny akordy ze všech progresí
            all_chords = []
            for prog in song_data.get("progressions", []):
                if isinstance(prog, dict) and "chords" in prog:
                    all_chords.extend(prog["chords"])

            if not all_chords:
                messagebox.showinfo("Informace", f"Píseň {song_name} nemá žádné akordy.")
                return

            # Vytvoří popis s informacemi o písni
            composer = song_data.get("composer", "Unknown")
            genre = self._format_genre_title(song_data.get("genre", "unknown"))
            year = song_data.get("year", "Unknown")

            source_description = f"{song_name} - {composer} ({year}) [{genre}]"

            # Callback pro nahrání progrese
            if self.on_load_progression:
                self.on_load_progression(all_chords, source_description)

            logger.info(f"Nahrána progrese: {song_name} ({len(all_chords)} akordů)")

        except Exception as e:
            logger.error(f"Chyba při nahrávání progrese z písně {song_name}: {e}")
            messagebox.showerror("Chyba", f"Nepodařilo se nahrát progrese: {str(e)}")

    def _export_progression(self) -> None:
        """Exportuje aktuální progrese do textového souboru."""
        if not self.app_state.current_progression_chords:
            messagebox.showinfo("Export", "Žádná progrese k exportu.")
            return

        try:
            # Vytvoří obsah s informacemi
            content_lines = []

            # Header s informacemi
            progression_info = self.app_state.get_progression_info()
            if progression_info['source']:
                content_lines.append(f"Zdroj: {progression_info['source']}")
                content_lines.append(f"Počet akordů: {len(progression_info['chords'])}")
                content_lines.append(f"Aktuální pozice: {progression_info['current_index'] + 1}")
                content_lines.append("")

            # Akordy
            content_lines.append("Akordy:")
            for i, chord in enumerate(progression_info['chords']):
                marker = " → " if i == progression_info['current_index'] else "   "
                content_lines.append(f"{i + 1:2d}.{marker}{chord}")

            content = "\n".join(content_lines)

            # Dialog pro uložení
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                title="Exportovat progrese"
            )

            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Export", f"Progrese uložena do: {file_path}")
                self.app_state.log(f"Progrese exportována do: {file_path}")
                logger.info(f"Progrese exportována do: {file_path}")

        except Exception as e:
            logger.error(f"Chyba při exportu progrese: {e}")
            messagebox.showerror("Chyba exportu", f"Nepodařilo se exportovat progrese: {str(e)}")

    def create_progression_buttons(self) -> None:
        """Vytvoří tlačítka pro jednotlivé akordy v progrese."""
        # Vymaže existující obsah
        for widget in self.prog_chord_frame.winfo_children():
            widget.destroy()

        progression_info = self.app_state.get_progression_info()

        if not progression_info['has_progression']:
            # Placeholder
            placeholder = ttk.Label(
                self.prog_chord_frame,
                text="Nahrajte progrese pro zobrazení akordů",
                foreground="gray"
            )
            placeholder.pack(expand=True)
            return

        # Aktualizuje info label
        self._update_progression_info(progression_info)

        # Control frame s navigací
        self._create_navigation_controls()

        # Frame s tlačítky akordů
        self._create_chord_buttons(progression_info['chords'])

    def _update_progression_info(self, progression_info: dict) -> None:
        """Aktualizuje informační label o progresi."""
        if not self.progression_info_label:
            return

        info_text = f"Zdroj: {progression_info['source'] or 'Neznámý'} | "
        info_text += f"Akordů: {progression_info['length']} | "
        info_text += f"Pozice: {progression_info['current_index'] + 1}/{progression_info['length']}"

        self.progression_info_label.config(text=info_text)

    def _create_navigation_controls(self) -> None:
        """Vytvoří navigační ovládání progrese."""
        nav_frame = ttk.Frame(self.prog_chord_frame)
        nav_frame.pack(fill="x", pady=5)

        # Previous button
        ttk.Button(
            nav_frame,
            text="<< Předchozí",
            command=lambda: self._step_progression(-1)
        ).pack(side=tk.LEFT, padx=5)

        # Current chord label
        self.current_chord_label = ttk.Label(
            nav_frame,
            text="-",
            font=("Segoe UI", 14, "bold"),
            width=15,
            anchor="center",
            relief="sunken",
            borderwidth=2
        )
        self.current_chord_label.pack(side=tk.LEFT, expand=True, fill="x", padx=10)

        # Next button
        ttk.Button(
            nav_frame,
            text="Následující >>",
            command=lambda: self._step_progression(1)
        ).pack(side=tk.LEFT, padx=5)

    def _create_chord_buttons(self, chords: List[str]) -> None:
        """Vytvoří grid tlačítek s jednotlivými akordy."""
        buttons_frame = ttk.Frame(self.prog_chord_frame)
        buttons_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.prog_chord_buttons = []

        for i, chord in enumerate(chords):
            btn = ttk.Button(
                buttons_frame,
                text=chord,
                command=lambda idx=i: self._jump_to_chord(idx),
                width=8
            )
            # Rozmístění do gridu (8 sloupců)
            row = i // 8
            col = i % 8
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            self.prog_chord_buttons.append(btn)

        # Konfigurace grid pro responsivní design
        for col in range(8):
            buttons_frame.columnconfigure(col, weight=1)

    def _step_progression(self, step: int) -> None:
        """
        Krok v progrese přes callback.

        Args:
            step: Počet kroků (kladný = dopředu, záporný = dozadu)
        """
        if self.on_step_progression:
            self.on_step_progression(step)

    def _jump_to_chord(self, index: int) -> None:
        """
        Skok na konkrétní akord přes callback.

        Args:
            index: Index akordu v progrese
        """
        if self.on_jump_to_chord:
            self.on_jump_to_chord(index)

    def update_progression_display(self) -> None:
        """Aktualizuje zobrazení aktuální progrese."""
        progression_info = self.app_state.get_progression_info()

        if not progression_info['has_progression']:
            return

        # Vytvoří styl pro zvýrazněný button
        style = ttk.Style()
        style.configure("Active.TButton", foreground="blue", font=('Segoe UI', 9, 'bold'))

        # Aktualizuje styly tlačítek
        current_index = progression_info['current_index']
        for i, btn in enumerate(self.prog_chord_buttons):
            if i == current_index:
                btn.configure(style="Active.TButton")
            else:
                btn.configure(style="TButton")

        # Aktualizuje label s aktuálním akordem
        current_chord = progression_info['current_chord']
        if current_chord and self.current_chord_label:
            self.current_chord_label.config(text=current_chord)

        # Aktualizuje info label
        self._update_progression_info(progression_info)

        logger.debug(f"Aktualizováno zobrazení: akord '{current_chord}' na pozici {current_index}")

    def refresh_songs_list(self) -> None:
        """Obnoví seznam písní (užitečné při změně databáze)."""
        current_genre = self.genre_filter_combo.get() if self.genre_filter_combo else None

        # Obnoví žánry
        self._populate_genre_filter()

        # Obnoví písně
        if current_genre:
            self._populate_songs_combo(current_genre)
        else:
            self._populate_songs_combo()

        logger.info("Seznam písní obnoven")

    def get_selected_song(self) -> str:
        """
        Vrací aktuálně vybranou píseň.

        Returns:
            str: Název vybrané písně
        """
        return self.song_combo.get() if self.song_combo else ""

    def set_selected_song(self, song_name: str) -> None:
        """
        Nastaví vybranou píseň v combo boxu.

        Args:
            song_name: Název písně k vybrání
        """
        if self.song_combo:
            self.song_combo.set(song_name)

    def get_selected_genre_filter(self) -> str:
        """
        Vrací aktuálně vybraný filtr žánru.

        Returns:
            str: Název žánru nebo prázdný string
        """
        return self.genre_filter_combo.get() if self.genre_filter_combo else ""

    def set_genre_filter(self, genre_title: str) -> None:
        """
        Nastaví filtr žánru a aktualizuje seznam písní.

        Args:
            genre_title: Název žánru (formátovaný titulek)
        """
        if self.genre_filter_combo:
            self.genre_filter_combo.set(genre_title)
            self._on_genre_filter_changed()

    def get_progression_stats(self) -> dict:
        """
        Vrací statistiky o aktuální progresi.

        Returns:
            dict: Statistiky progrese
        """
        progression_info = self.app_state.get_progression_info()

        if not progression_info['has_progression']:
            return {"has_progression": False}

        # Analýza akordů v progresi
        unique_chords = list(set(progression_info['chords']))

        # Jednoduché rozbory
        maj_count = len([c for c in unique_chords if 'maj' in c.lower()])
        min_count = len([c for c in unique_chords if
                         any(marker in c.lower() for marker in ['m', 'min']) and 'maj' not in c.lower()])
        dom_count = len([c for c in unique_chords if '7' in c and 'maj7' not in c and 'm7' not in c])

        return {
            "has_progression": True,
            "total_chords": len(progression_info['chords']),
            "unique_chords": len(unique_chords),
            "chord_types": {
                "major": maj_count,
                "minor": min_count,
                "dominant": dom_count,
                "other": len(unique_chords) - maj_count - min_count - dom_count
            },
            "source": progression_info['source'],
            "current_position": f"{progression_info['current_index'] + 1}/{progression_info['length']}"
        }

    def export_progression_analysis(self) -> str:
        """
        Vytvoří detailní textovou analýzu progrese pro export.

        Returns:
            str: Formátovaná analýza progrese
        """
        stats = self.get_progression_stats()

        if not stats['has_progression']:
            return "Žádná progrese není načtena."

        progression_info = self.app_state.get_progression_info()

        lines = []
        lines.append("=== ANALÝZA PROGRESE ===")
        lines.append("")
        lines.append(f"Zdroj: {stats['source']}")
        lines.append(f"Celkem akordů: {stats['total_chords']}")
        lines.append(f"Unikátních akordů: {stats['unique_chords']}")
        lines.append(f"Aktuální pozice: {stats['current_position']}")
        lines.append("")

        lines.append("Rozdělení podle typů:")
        for chord_type, count in stats['chord_types'].items():
            if count > 0:
                percentage = (count / stats['unique_chords']) * 100
                lines.append(f"  {chord_type.capitalize()}: {count} ({percentage:.1f}%)")
        lines.append("")

        lines.append("Sekvence akordů:")
        for i, chord in enumerate(progression_info['chords']):
            marker = " →" if i == progression_info['current_index'] else "  "
            lines.append(f"{i + 1:2d}.{marker} {chord}")

        return "\n".join(lines)

    def reset_display(self) -> None:
        """Resetuje zobrazení progression playeru."""
        if self.current_chord_label:
            self.current_chord_label.config(text="-")

        if self.progression_info_label:
            self.progression_info_label.config(text="Žádná progrese není načtena")

        # Vymaže všechna tlačítka a vytvoří placeholder
        for widget in self.prog_chord_frame.winfo_children():
            widget.destroy()

        placeholder = ttk.Label(
            self.prog_chord_frame,
            text="Nahrajte progrese pro zobrazení akordů",
            foreground="gray"
        )
        placeholder.pack(expand=True)

        self.prog_chord_buttons.clear()
        logger.debug("Zobrazení progression playeru resetováno")

    def show_progression_help(self) -> None:
        """Zobrazí nápovědu pro progression player."""
        help_text = """
PROGRESSION PLAYER - NÁPOVĚDA

NAČÍTÁNÍ PROGRESÍ:
• Vyberte žánr z filtru (nebo nechte "Vše")
• Vyberte píseň ze seznamu
• Klikněte "Nahrát celou píseň"

NAVIGACE V PROGRESI:
• Tlačítka "<< Předchozí" / "Následující >>" pro postupný průchod
• Kliknutí na konkrétní akord pro přeskok
• Klávesy ← a → pro rychlou navigace

AUTOMATICKÉ MIDI:
• Každý akord se automaticky přehraje při zobrazení
• Zapněte/vypněte MIDI v ovládacím panelu
• Nastavte velocity podle preference

EXPORT:
• "Exportovat progrese" - uloží aktuální progrese do .txt souboru
• Obsahuje akordy, pozici a základní statistiky

ŽÁNROVÉ FILTROVÁNÍ:
• Jazz Standard - klasické jazzové standardy
• Latin Jazz - bossa nova a latin rytmy  
• Modern Jazz - Bill Evans, Michel Petrucciani
• Bebop - rychlé, technicky náročné progrese
• Jazz Progressions - cvičné progrese a ii-V-I
• Blues - bluesové progrese
• Folk - lidové písně

TIPY:
• Progrese z analýzy akordů se načtou pro náhled
• Pro plné MIDI přehrávání přejděte sem z analýzy
• Kombinujte s různými voicing typy (Root/Smooth/Drop 2)
        """

        # Vytvoří nové okno s nápovědou
        help_window = tk.Toplevel()
        help_window.title("Nápověda - Progression Player")
        help_window.geometry("600x500")

        # Text widget s scroll barem
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget = tk.Text(text_frame, wrap="word", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)

        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        text_widget.insert("1.0", help_text.strip())
        text_widget.config(state="disabled")

        # Tlačítko pro zavření
        ttk.Button(help_window, text="Zavřít", command=help_window.destroy).pack(pady=10)

    def get_debug_info(self) -> dict:
        """
        Vrací debug informace pro troubleshooting.

        Returns:
            dict: Debug informace o ProgressionView
        """
        return {
            "song_combo_configured": self.song_combo is not None,
            "genre_filter_configured": self.genre_filter_combo is not None,
            "progression_frame_configured": self.prog_chord_frame is not None,
            "current_chord_label_configured": self.current_chord_label is not None,
            "chord_buttons_count": len(self.prog_chord_buttons),
            "selected_song": self.get_selected_song(),
            "selected_genre_filter": self.get_selected_genre_filter(),
            "all_songs_cache_size": len(self._all_songs_cache),
            "filtered_songs_cache_size": len(self._filtered_songs_cache),
            "callbacks_set": {
                "step_progression": self.on_step_progression is not None,
                "jump_to_chord": self.on_jump_to_chord is not None,
                "load_progression": self.on_load_progression is not None
            },
            "progression_stats": self.get_progression_stats()
        }
