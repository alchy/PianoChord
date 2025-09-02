# gui/main_window.py
"""
gui/main_window.py - Refaktorované hlavní GUI okno.
Koordinuje všechny GUI komponenty a propojuje je s core logikou.
Čistě GUI vrstva - veškerá hudební logika je v core modulech.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Optional

from config import AppConfig, MusicalConstants
from core import ApplicationState, ProgressionManager, ChordAnalyzer
from midi import MidiPlayer
from display import KeyboardDisplay
from gui.controls_view import ControlsView
from gui.analysis_view import AnalysisView
from gui.progression_view import ProgressionView

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Refaktorované hlavní GUI okno.
    Koordinuje všechny GUI komponenty a funguje jako controller v MVC pattern.
    """

    def __init__(self):
        """Inicializuje hlavní okno s všemi komponentami."""
        logger.info("Inicializuji MainWindow...")

        # Vytvoření základních komponent
        self.root = tk.Tk()

        # Core komponenty
        self.app_state = ApplicationState()
        self.progression_manager = ProgressionManager()
        self.midi_player = MidiPlayer()
        self.chord_analyzer = ChordAnalyzer()

        # GUI komponenty
        self.canvas: Optional[tk.Canvas] = None
        self.keyboard_display: Optional[KeyboardDisplay] = None
        self.controls_view: Optional[ControlsView] = None
        self.analysis_view: Optional[AnalysisView] = None
        self.progression_view: Optional[ProgressionView] = None

        # Inicializace
        self._setup_window()
        self._initialize_core_components()
        self._create_gui_components()
        self._create_gui_layout()
        self._setup_callbacks()
        self._setup_keyboard_shortcuts()
        self._initialize_data()

        logger.info("MainWindow úspěšně inicializován")

    def _setup_window(self) -> None:
        """Nastaví základní vlastnosti hlavního okna."""
        self.root.title(AppConfig.WINDOW_TITLE)
        self.root.geometry(AppConfig.WINDOW_SIZE)
        self.root.minsize(800, 600)

        # Konfigurace gridu pro responsivní design
        self.root.rowconfigure(0, weight=2)  # Klaviatura
        self.root.rowconfigure(1, weight=0)  # Input sekce
        self.root.rowconfigure(2, weight=0)  # MIDI sekce
        self.root.rowconfigure(3, weight=3)  # Output notebook
        self.root.columnconfigure(0, weight=1)

        logger.debug("Základní window nastavení dokončeno")

    def _initialize_core_components(self) -> None:
        """Inicializuje core komponenty."""
        logger.info("Inicializuji core komponenty...")

        # Načte databázi
        database_success = self.progression_manager.load_database()
        if database_success:
            stats = self.progression_manager.get_database_statistics()
            logger.info(f"Databáze: {stats['original_songs_count']} písní, "
                        f"{stats['genres_count']} žánrů")
        else:
            logger.warning("Databáze načtena s problémy")

        # Inicializuje MIDI
        midi_success = self.midi_player.initialize()
        if midi_success:
            logger.info(f"MIDI port: {self.midi_player.current_port_name}")
            self.app_state.set_midi_enabled(True)
        else:
            logger.warning("MIDI systém není dostupný")
            self.app_state.set_midi_enabled(False)

        logger.info("Core komponenty inicializovány")

    def _create_gui_components(self) -> None:
        """Vytvoří GUI komponenty."""
        logger.info("Vytvářím GUI komponenty...")

        # Controls view
        self.controls_view = ControlsView(self.app_state, self.midi_player)

        # Analysis view
        self.analysis_view = AnalysisView(self.progression_manager, self.app_state)

        # Progression view
        self.progression_view = ProgressionView(self.progression_manager, self.app_state)

        logger.info("GUI komponenty vytvořeny")

    def _create_gui_layout(self) -> None:
        """Vytvoří rozložení GUI."""
        logger.info("Vytvářím GUI layout...")

        # Klaviatura sekce
        self._create_keyboard_section()

        # Input a MIDI sekce
        self.controls_view.create_input_section(self.root, row=1)
        self.controls_view.create_midi_section(self.root, row=2)

        # Output sekce s notebookem
        self._create_output_section()

        logger.info("GUI layout vytvořen")

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

        # Vytvoření KeyboardDisplay s automatickým MIDI
        self.keyboard_display = KeyboardDisplay(
            canvas=self.canvas,
            app_state=self.app_state,
            midi_player=self.midi_player,
            nr_of_keys=MusicalConstants.ARCHETYPE_SIZE
        )

        # Vykreslí prázdnou klaviaturu
        self.keyboard_display.draw()

        logger.debug("Klaviatura sekce vytvořena")

    def _create_output_section(self) -> None:
        """Vytvoří výstupní sekci s notebookem."""
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=3, column=0, sticky="nsew", pady=10)

        # Analysis tab s žánrovými záložkami
        analysis_tab = ttk.Frame(notebook)
        notebook.add(analysis_tab, text="Analýza akordu")
        self.analysis_view.create_analysis_tab(analysis_tab)

        # Progression player tab
        prog_player_tab = ttk.Frame(notebook)
        notebook.add(prog_player_tab, text="Progression Player")
        self.progression_view.create_prog_player_tab(prog_player_tab)

        # Log tab
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="Log")
        self.controls_view.create_log_tab(log_tab)

        logger.debug("Output sekce vytvořena")

    def _setup_callbacks(self) -> None:
        """Nastaví callback funkce mezi GUI komponentami."""
        logger.debug("Nastavuji callbacks...")

        # Controls view callbacks
        self.controls_view.on_analyze_chord = self._handle_analyze_chord
        self.controls_view.on_voicing_changed = self._handle_voicing_changed
        self.controls_view.on_midi_settings_changed = self._handle_midi_settings_changed

        # Analysis view callbacks
        self.analysis_view.on_progression_selected = self._handle_progression_selected
        self.analysis_view.on_progression_preview = self._handle_progression_preview

        # Progression view callbacks
        self.progression_view.on_step_progression = self._handle_step_progression
        self.progression_view.on_jump_to_chord = self._handle_jump_to_chord
        self.progression_view.on_load_progression = self._handle_load_progression

        # App state callbacks
        self.app_state.on_state_changed = self._handle_state_changed
        self.app_state.on_chord_changed = self._handle_chord_changed
        self.app_state.on_progression_changed = self._handle_progression_changed

        # MIDI callbacks
        self.midi_player.on_error = self._handle_midi_error
        self.midi_player.on_success = self._handle_midi_success

        logger.debug("Callbacks nastaveny")

    def _setup_keyboard_shortcuts(self) -> None:
        """Nastaví klávesové zkratky."""
        shortcuts_callbacks = {
            'prev_chord': lambda: self._handle_step_progression(-1),
            'next_chord': lambda: self._handle_step_progression(1)
        }

        self.controls_view.setup_keyboard_shortcuts(self.root, shortcuts_callbacks)
        logger.debug("Klávesové zkratky nastaveny")

    def _initialize_data(self) -> None:
        """Inicializuje data pro GUI komponenty."""
        logger.info("Inicializuji data pro GUI...")

        # Inicializuje MIDI GUI
        self.controls_view.initialize_midi_gui()

        # Aktualizuje log display
        self.controls_view.update_log_display()

        # Zaměří chord input
        self.controls_view.focus_chord_input()

        logger.info("Data pro GUI inicializována")

    # Callback handlers
    def _handle_analyze_chord(self, chord_name: str) -> None:
        """
        Handler pro analýzu akordu.

        Args:
            chord_name: Název akordu k analýze
        """
        try:
            logger.info(f"Analyzuji akord: {chord_name}")

            # Analýza přes ChordAnalyzer s databází
            analysis = self.chord_analyzer.analyze_chord_name(chord_name, self.progression_manager)

            # Uložení do app state
            self.app_state.set_current_chord_analysis(analysis)

            # Zobrazení v analysis view
            self.analysis_view.display_analysis_results(analysis)

            # Zobrazení na klaviatuře s automatickým MIDI
            self.keyboard_display.draw_chord_by_name(chord_name)

            logger.info(f"Analýza akordu {chord_name} dokončena")

        except Exception as e:
            logger.error(f"Chyba při analýze akordu {chord_name}: {e}")
            messagebox.showerror("Chyba analýzy", str(e))

    def _handle_voicing_changed(self, new_voicing: str) -> None:
        """
        Handler pro změnu voicingu.

        Args:
            new_voicing: Nový typ voicingu
        """
        logger.info(f"Voicing změněn na: {new_voicing}")

        # Resetuje smooth voicing stav
        if new_voicing != "smooth":
            self.app_state.reset_voicing_state()

        # Překreslí aktuální akord s novým voicingem
        current_chord = self.app_state.last_displayed_chord
        if current_chord and self.keyboard_display:
            self.keyboard_display.draw_chord_by_name(current_chord, new_voicing, auto_midi=False)

    def _handle_midi_settings_changed(self) -> None:
        """Handler pro změny MIDI nastavení."""
        logger.debug("MIDI nastavení změněna")
        # Další logika pokud potřebná

    def _handle_progression_selected(self, chords: List[str], source_name: str) -> None:
        """
        Handler pro výběr progrese z analýzy (single-click).

        Args:
            chords: Seznam akordů v progrese
            source_name: Název zdroje
        """
        logger.info(f"Vybrána progrese: {source_name} ({len(chords)} akordů)")
        # Momentálně jen loguje, další akce lze přidat

    def _handle_progression_preview(self, chords: List[str], source_name: str) -> None:
        """
        Handler pro náhled progrese (double-click).
        Nahraje progrese bez MIDI přehrávání prvního akordu.

        Args:
            chords: Seznam akordů v progrese
            source_name: Název zdroje
        """
        logger.info(f"Náhled progrese: {source_name}")

        # Nahraje progrese
        self.app_state.load_progression(chords, source_name)

        # Aktualizuje progression view
        self.progression_view.create_progression_buttons()
        self.progression_view.update_progression_display()

        # Zobrazí první akord POUZE vizuálně (bez MIDI)
        if chords:
            self.keyboard_display.draw_chord_by_name(chords[0], auto_midi=False)

    def _handle_load_progression(self, chords: List[str], source_name: str) -> None:
        """
        Handler pro nahrání kompletní progrese z progression playeru.

        Args:
            chords: Seznam akordů v progrese
            source_name: Název zdroje
        """
        logger.info(f"Nahrávám progrese: {source_name} ({len(chords)} akordů)")

        # Nahraje progrese
        self.app_state.load_progression(chords, source_name)

        # Aktualizuje progression view
        self.progression_view.create_progression_buttons()
        self.progression_view.update_progression_display()

        # Zobrazí první akord S MIDI (v progression playeru je to žádoucí)
        if chords:
            self.keyboard_display.draw_chord_by_name(chords[0], auto_midi=True)

    def _handle_step_progression(self, step: int) -> None:
        """
        Handler pro krok v progrese.

        Args:
            step: Počet kroků (kladný = dopředu, záporný = dozadu)
        """
        success = self.app_state.step_progression(step)
        if success:
            # Aktualizuje GUI
            self.progression_view.update_progression_display()

            # Zobrazí aktuální akord S MIDI
            current_chord = self.app_state.get_current_chord()
            if current_chord:
                self.keyboard_display.draw_chord_by_name(current_chord, auto_midi=True)

    def _handle_jump_to_chord(self, index: int) -> None:
        """
        Handler pro skok na konkrétní akord.

        Args:
            index: Index akordu v progrese
        """
        success = self.app_state.jump_to_chord_index(index)
        if success:
            # Aktualizuje GUI
            self.progression_view.update_progression_display()

            # Zobrazí akord S MIDI
            current_chord = self.app_state.get_current_chord()
            if current_chord:
                self.keyboard_display.draw_chord_by_name(current_chord, auto_midi=True)

    def _handle_state_changed(self, property_name: str, old_value, new_value) -> None:
        """
        Handler pro změny stavu aplikace.

        Args:
            property_name: Název změněné vlastnosti
            old_value: Stará hodnota
            new_value: Nová hodnota
        """
        logger.debug(f"Stav změněn: {property_name} = {new_value}")

        # Aktualizuje log display při každé změně
        self.controls_view.update_log_display()

    def _handle_chord_changed(self, old_analysis, new_analysis) -> None:
        """
        Handler pro změny aktuálního akordu.

        Args:
            old_analysis: Stará analýza
            new_analysis: Nová analýza
        """
        chord_name = new_analysis.get('chord_name', 'Unknown')
        logger.debug(f"Aktuální akord změněn na: {chord_name}")

    def _handle_progression_changed(self, change_info: dict) -> None:
        """
        Handler pro změny progrese.

        Args:
            change_info: Informace o změně
        """
        action = change_info.get('action', 'unknown')
        logger.debug(f"Progrese změněna: {action}")

        # Aktualizuje GUI podle typu změny
        if action in ['loaded', 'stepped', 'jumped']:
            self.progression_view.update_progression_display()

    def _handle_midi_error(self, error_message: str) -> None:
        """Handler pro MIDI chyby."""
        self.app_state.log(f"MIDI CHYBA: {error_message}")

    def _handle_midi_success(self, success_message: str) -> None:
        """Handler pro MIDI úspěchy."""
        self.app_state.log(success_message)

    # Public API
    def run(self) -> None:
        """
        Spustí hlavní smyčku aplikace.
        """
        try:
            # Úvodní zpráva
            self.app_state.log(f"Piano Chord Analyzer spuštěn s {self.app_state.get_voicing_type()} voicingem")
            self.app_state.log("=== Aplikace připravena k použití ===")

            logger.info("Spouštím GUI main loop...")

            # Spustí GUI
            self.root.mainloop()

        except Exception as e:
            logger.error(f"Chyba v main loop: {e}", exc_info=True)
            messagebox.showerror("Kritická chyba", f"Neočekávaná chyba: {e}")

        finally:
            # Cleanup při ukončení
            self._cleanup()

    def _cleanup(self) -> None:
        """Vyčistí zdroje při ukončení aplikace."""
        try:
            logger.info("Čištění zdrojů...")

            # Cleanup MIDI
            if self.midi_player:
                self.midi_player.cleanup()

            # Uložení uživatelských nastavení (volitelné)
            settings = self.app_state.get_settings_dict()
            logger.debug(f"Uživatelská nastavení při ukončení: {settings}")

            self.app_state.log("Aplikace ukončena")

        except Exception as e:
            logger.error(f"Chyba při cleanup: {e}")

    def show_about_dialog(self) -> None:
        """Zobrazí dialog 'O aplikaci'."""
        about_text = """
Piano Chord Analyzer v2.0.0

Refaktorovaná verze s modulární architekturou:
• Nezávislé core komponenty
• Automatické MIDI přehrávání
• Žánrové kategorizace progresí
• 3 typy voicingů (Root, Smooth, Drop 2)
• 80+ jazzových standardů s transpozicemi

Vývoj: Python + tkinter
Hudební teorie: Jazzové harmonie a progrese
MIDI: mido + python-rtmidi

Architektura:
• core/ - Nezávislá hudební logika
• midi/ - MIDI přehrávání s threading
• display/ - Klaviatura s automatickým MIDI
• gui/ - Uživatelské rozhraní

© 2024 Piano Chord Analyzer
        """

        messagebox.showinfo("O aplikaci", about_text.strip())

    def show_keyboard_shortcuts(self) -> None:
        """Zobrazí dialog s klávesovými zkratkami."""
        shortcuts_text = """
KLÁVESOVÉ ZKRATKY:

Enter             - Analyzovat akord
←                - Předchozí akord v progresi  
→                - Následující akord v progresi

OVLÁDÁNÍ PROGRESÍ:
Klik na akord     - Skok na konkrétní akord
Double-click      - Náhled progrese (bez MIDI)

VOICING TYPY:
Root              - Základní pozice akordu (červená)
Smooth            - Plynulé přechody (zelená) 
Drop 2            - Jazzový otevřený voicing (modrá)

MIDI:
Automatické       - Při každém vykreslení akordu
Stop MIDI         - Zastaví všechny hrající noty
Velocity          - Nastavení síly úderu (0-127)

ŽÁNROVÉ ZÁLOŽKY:
Jazz Standard     - Klasické jazzové standardy
Latin Jazz        - Bossa nova a latin rytmy
Modern Jazz       - Bill Evans, Michel Petrucciani
Bebop            - Rychlé, technicky náročné
Jazz Progressions - Cvičné progrese ii-V-I
Blues            - Bluesové progrese
        """

        messagebox.showinfo("Klávesové zkratky", shortcuts_text.strip())

    def get_system_info(self) -> dict:
        """
        Vrací informace o systému pro debugging.

        Returns:
            dict: Systémové informace
        """
        import sys
        import platform

        return {
            "python_version": sys.version,
            "platform": platform.system(),
            "platform_version": platform.version(),
            "app_state": self.app_state.get_state_summary(),
            "midi_status": self.midi_player.get_status() if self.midi_player else None,
            "database_stats": self.progression_manager.get_database_statistics(),
            "gui_components": {
                "controls_view": self.controls_view.get_debug_info() if self.controls_view else None,
                "analysis_view": self.analysis_view.get_debug_info() if self.analysis_view else None,
                "progression_view": self.progression_view.get_debug_info() if self.progression_view else None,
                "keyboard_display": self.keyboard_display.get_debug_info() if self.keyboard_display else None
            }
        }

    def show_system_info(self) -> None:
        """Zobrazí dialog se systémovými informacemi."""
        try:
            info = self.get_system_info()

            # Vytvoří nové okno
            info_window = tk.Toplevel(self.root)
            info_window.title("Systémové informace")
            info_window.geometry("700x500")

            # Text widget s scroll barem
            text_frame = ttk.Frame(info_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)

            text_widget = tk.Text(text_frame, wrap="word", font=("Consolas", 9))
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)

            text_widget.configure(yscrollcommand=scrollbar.set)
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Formátování informací
            info_text = self._format_system_info(info)
            text_widget.insert("1.0", info_text)
            text_widget.config(state="disabled")

            # Tlačítka
            button_frame = ttk.Frame(info_window)
            button_frame.pack(fill="x", padx=10, pady=5)

            ttk.Button(
                button_frame,
                text="Kopírovat do schránky",
                command=lambda: self._copy_to_clipboard(info_text)
            ).pack(side="left", padx=5)

            ttk.Button(button_frame, text="Zavřít", command=info_window.destroy).pack(side="right", padx=5)

        except Exception as e:
            logger.error(f"Chyba při zobrazení systémových informací: {e}")
            messagebox.showerror("Chyba", f"Nelze zobrazit systémové informace: {e}")

    def _format_system_info(self, info: dict) -> str:
        """
        Formátuje systémové informace do čitelného textu.

        Args:
            info: Slovník se systémovými informacemi

        Returns:
            str: Formátovaný text
        """
        import json

        lines = []
        lines.append("=== PIANO CHORD ANALYZER - SYSTÉMOVÉ INFORMACE ===")
        lines.append("")

        # Základní info
        lines.append(f"Python verze: {info['python_version'].split()[0]}")
        lines.append(f"Platforma: {info['platform']} {info['platform_version']}")
        lines.append("")

        # App state
        app_state = info.get('app_state', {})
        lines.append("STAV APLIKACE:")
        lines.append(f"  Voicing typ: {app_state.get('voicing_type', 'N/A')}")
        lines.append(f"  MIDI zapnuto: {app_state.get('midi_enabled', 'N/A')}")
        lines.append(f"  Aktuální akord: {app_state.get('current_chord', 'N/A')}")
        lines.append(f"  Progrese: {app_state.get('progression_length', 0)} akordů")
        lines.append("")

        # MIDI status
        midi_status = info.get('midi_status')
        if midi_status:
            lines.append("MIDI STATUS:")
            lines.append(f"  Dostupné: {midi_status.get('midi_available', 'N/A')}")
            lines.append(f"  Zapnuto: {midi_status.get('is_enabled', 'N/A')}")
            lines.append(f"  Aktuální port: {midi_status.get('current_port', 'N/A')}")
            lines.append(f"  Dostupné porty: {len(midi_status.get('available_ports', []))}")
            lines.append("")

        # Database stats
        db_stats = info.get('database_stats', {})
        lines.append("DATABÁZE:")
        lines.append(f"  Originální písně: {db_stats.get('original_songs_count', 'N/A')}")
        lines.append(f"  Transponované: {db_stats.get('transposed_songs_count', 'N/A')}")
        lines.append(f"  Žánry: {db_stats.get('genres_count', 'N/A')}")
        if db_stats.get('genres'):
            lines.append(f"  Seznam žánrů: {', '.join(db_stats['genres'])}")
        lines.append("")

        # GUI komponenty
        gui_components = info.get('gui_components', {})
        lines.append("GUI KOMPONENTY:")
        for component, component_info in gui_components.items():
            if component_info:
                lines.append(f"  {component}: Inicializován")
            else:
                lines.append(f"  {component}: Nedostupný")

        return "\n".join(lines)

    def _copy_to_clipboard(self, text: str) -> None:
        """Zkopíruje text do schránky."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Kopírování", "Systémové informace zkopírovány do schránky")
        except Exception as e:
            logger.error(f"Chyba při kopírování do schránky: {e}")
            messagebox.showerror("Chyba", f"Nelze kopírovat do schránky: {e}")

    def refresh_all_data(self) -> None:
        """Obnoví všechna data v aplikaci (užitečné při změnách v databázi)."""
        try:
            logger.info("Obnovuji všechna data...")

            # Reload databáze
            self.progression_manager.reload_database()

            # Refresh GUI komponent
            self.analysis_view.refresh_genre_tabs()
            self.progression_view.refresh_songs_list()

            # Aktualizuje log
            self.controls_view.update_log_display()

            self.app_state.log("Všechna data obnovena")

            messagebox.showinfo("Obnovení dat", "Všechna data byla úspěšně obnovena")

        except Exception as e:
            logger.error(f"Chyba při obnovení dat: {e}")
            messagebox.showerror("Chyba", f"Chyba při obnovení dat: {e}")

    # Utility metody pro testování
    def analyze_chord_programmatically(self, chord_name: str) -> dict:
        """
        Analyzuje akord programaticky (užitečné pro testování).

        Args:
            chord_name: Název akordu

        Returns:
            dict: Výsledky analýzy
        """
        try:
            # Nastaví chord input
            self.controls_view.set_chord_input(chord_name)

            # Spustí analýzu
            self._handle_analyze_chord(chord_name)

            # Vrátí výsledky
            return self.app_state.current_analysis

        except Exception as e:
            logger.error(f"Chyba při programatické analýze: {e}")
            return {"error": str(e)}

    def load_progression_programmatically(self, chords: List[str], source: str = "Programmatic") -> bool:
        """
        Nahraje progrese programaticky (užitečné pro testování).

        Args:
            chords: Seznam akordů
            source: Název zdroje

        Returns:
            bool: True při úspěchu
        """
        try:
            self._handle_load_progression(chords, source)
            return True
        except Exception as e:
            logger.error(f"Chyba při programatickém načtení progrese: {e}")
            return False

    def get_current_display_state(self) -> dict:
        """
        Vrací aktuální stav zobrazení pro debugging.

        Returns:
            dict: Stav zobrazení
        """
        return {
            "keyboard_display": self.keyboard_display.get_debug_info() if self.keyboard_display else None,
            "controls_view": self.controls_view.get_debug_info() if self.controls_view else None,
            "analysis_view": self.analysis_view.get_debug_info() if self.analysis_view else None,
            "progression_view": self.progression_view.get_debug_info() if self.progression_view else None,
            "app_state_summary": self.app_state.get_state_summary()
        }


if __name__ == "__main__":
    # Přímé spuštění pro testování
    print("=== Piano Chord Analyzer - Main Window Test ===")

    try:
        # Import configu pro logování
        from config import LoggingConfig

        LoggingConfig.setup_logging()

        logger = logging.getLogger(__name__)
        logger.info("Spouštím MainWindow test...")

        # Vytvoření a spuštění aplikace
        app = MainWindow()

        # Test programatické analýzy
        logger.info("Test programatické analýzy...")
        result = app.analyze_chord_programmatically("Cmaj7")
        if "error" not in result:
            logger.info(f"Test analýzy úspěšný: {result.get('chord_name')}")

        # Test programatického načtení progrese
        logger.info("Test programatického načtení progrese...")
        test_chords = ["Cmaj7", "Am7", "Dm7", "G7"]
        success = app.load_progression_programmatically(test_chords, "Test Progrese")
        if success:
            logger.info("Test progrese úspěšný")

        # Spuštění GUI
        logger.info("Spouštím GUI...")
        app.run()

    except KeyboardInterrupt:
        logger.info("Test ukončen uživatelem")
    except Exception as e:
        logger.error(f"Test selhal: {e}", exc_info=True)
        print(f"CHYBA: {e}")
    finally:
        print("Test dokončen")
