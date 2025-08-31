# gui_progression.py
"""
gui_progression.py - Refaktorované komponenty pro progression player v GUI.
OPRAVA: Aktualizováno pro novou architekturu s main_window.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, TYPE_CHECKING
import logging

from jazz_database import JazzStandardsDatabase

if TYPE_CHECKING:
    from main_window import MainWindow

logger = logging.getLogger(__name__)


class ProgressionHandler:
    """
    Refaktorovaná třída pro zpracování progresí v GUI.
    Zodpovídá za progression player tab a ovládání progresí.
    """

    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window

        # GUI komponenty
        self.song_combo: ttk.Combobox = None
        self.prog_chord_frame: ttk.Frame = None
        self.current_chord_label: ttk.Label = None
        self.prog_chord_buttons: List[ttk.Button] = []

    def create_prog_player_tab(self, parent: ttk.Frame) -> None:
        """Vytvoří tab pro progression player."""
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        # Control frame s výběrem písní
        self._create_control_section(parent)

        # Frame pro zobrazení aktuální progrese
        self._create_progression_section(parent)

    def _create_control_section(self, parent: ttk.Frame) -> None:
        """Vytvoří ovládací sekci s výběrem písní."""
        control_frame = ttk.Frame(parent, padding=10)
        control_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(control_frame, text="Vyberte píseň:").pack(side=tk.LEFT, padx=5)

        # Combo box s písněmi
        try:
            songs = JazzStandardsDatabase.get_all_songs()
            self.song_combo = ttk.Combobox(control_frame, values=sorted(songs), width=30)
            self.song_combo.pack(side=tk.LEFT, padx=5)
        except Exception as e:
            logger.error(f"Chyba při načítání seznamu písní: {e}")
            self.song_combo = ttk.Combobox(control_frame, values=[], width=30)
            self.song_combo.pack(side=tk.LEFT, padx=5)

        # Tlačítka pro ovládání
        ttk.Button(
            control_frame,
            text="Nahrát celou píseň",
            command=self._load_progression_from_combo
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Exportovat progrese",
            command=self._export_progression
        ).pack(side=tk.LEFT, padx=5)

    def _create_progression_section(self, parent: ttk.Frame) -> None:
        """Vytvoří sekci pro zobrazení aktuální progrese."""
        self.prog_chord_frame = ttk.Labelframe(parent, text="Aktuální progrese", padding=10)
        self.prog_chord_frame.grid(row=1, column=0, sticky="nsew")

    def _load_progression_from_combo(self) -> None:
        """Nahraje progrese z vybrané písně."""
        song_name = self.song_combo.get()

        if not song_name or song_name.startswith("Nahráno:"):
            messagebox.showinfo("Výběr", "Vyberte píseň ze seznamu pro nahrání celé skladby.")
            return

        try:
            song_data = JazzStandardsDatabase.get_song_info(song_name)
            if not song_data:
                messagebox.showerror("Chyba", f"Nenalezena data pro píseň: {song_name}")
                return

            # Spojí všechny akordy ze všech progresí
            all_chords = []
            for prog in song_data["progressions"]:
                all_chords.extend(prog["chords"])

            if not all_chords:
                messagebox.showinfo("Informace", f"Píseň {song_name} nemá žádné akordy.")
                return

            # Nahraje progrese do aplikace
            self.main_window.load_progression(all_chords, song_name)
            logger.info(f"Nahraná progrese z písně: {song_name} ({len(all_chords)} akordů)")

        except Exception as e:
            logger.error(f"Chyba při nahrávání progrese z písně {song_name}: {e}")
            messagebox.showerror("Chyba", f"Nepodařilo se nahrát progrese: {str(e)}")

    def _export_progression(self) -> None:
        """Exportuje aktuální progrese do textového souboru."""
        if not self.main_window.app_state.current_progression_chords:
            messagebox.showinfo("Export", "Žádná progrese k exportu.")
            return

        try:
            content = "\n".join(self.main_window.app_state.current_progression_chords)

            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")]
            )

            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Export", f"Progrese uložena do: {file_path}")
                logger.info(f"Progrese exportována do: {file_path}")

        except Exception as e:
            logger.error(f"Chyba při exportu progrese: {e}")
            messagebox.showerror("Chyba exportu", f"Nepodařilo se exportovat progrese: {str(e)}")

    def create_progression_buttons(self) -> None:
        """Vytvoří tlačítka pro jednotlivé akordy v prgresi."""
        # Vymaže existující obsah
        for widget in self.prog_chord_frame.winfo_children():
            widget.destroy()

        if not self.main_window.app_state.current_progression_chords:
            return

        # Control frame s navigací
        self._create_navigation_controls()

        # Frame s tlačítky akordů
        self._create_chord_buttons()

    def _create_navigation_controls(self) -> None:
        """Vytvoří navigační ovládání progrese."""
        control_frame = ttk.Frame(self.prog_chord_frame)
        control_frame.pack(fill="x", pady=5)

        # Previous button
        ttk.Button(
            control_frame,
            text="<< Prev",
            command=lambda: self.main_window._step_progression(-1)
        ).pack(side=tk.LEFT, padx=5)

        # Current chord label
        self.current_chord_label = ttk.Label(
            control_frame,
            text="-",
            font=("Segoe UI", 12, "bold"),
            width=15,
            anchor="center"
        )
        self.current_chord_label.pack(side=tk.LEFT, expand=True, fill="x")

        # Next button
        ttk.Button(
            control_frame,
            text="Next >>",
            command=lambda: self.main_window._step_progression(1)
        ).pack(side=tk.LEFT, padx=5)

    def _create_chord_buttons(self) -> None:
        """Vytvoří grid tlačítek s jednotlivými akordy."""
        buttons_frame = ttk.Frame(self.prog_chord_frame)
        buttons_frame.pack(fill="both", expand=True)

        self.prog_chord_buttons = []
        chords = self.main_window.app_state.current_progression_chords

        for i, chord in enumerate(chords):
            btn = ttk.Button(
                buttons_frame,
                text=chord,
                command=lambda idx=i: self._handle_chord_click(idx)
            )
            # Rozmístění do gridu (8 sloupců)
            btn.grid(row=i // 8, column=i % 8, padx=2, pady=2, sticky="ew")
            self.prog_chord_buttons.append(btn)

        # Konfigurace grid pro responsivní design
        for col in range(8):
            buttons_frame.columnconfigure(col, weight=1)

    def _handle_chord_click(self, index: int) -> None:
        """
        Obsluhuje klik na tlačítko akordu.
        Skočí na daný akord v prgresi.
        """
        self.main_window.jump_to_chord(index)
        logger.debug(f"Skok na akord na pozici {index}")

    def update_progression_display(self) -> None:
        """Aktualizuje zobrazení aktuální progrese."""
        if not self.main_window.app_state.current_progression_chords:
            return

        # Vytvoří styl pro zvýrazněný button
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="blue", font=('Segoe UI', 9, 'bold'))

        # Aktualizuje styly tlačítek
        current_index = self.main_window.app_state.current_progression_index
        for i, btn in enumerate(self.prog_chord_buttons):
            if i == current_index:
                btn.configure(style="Accent.TButton")
            else:
                btn.configure(style="TButton")

        # Aktualizuje label s aktuálním akordem
        current_chord = self.main_window.app_state.get_current_chord()
        if current_chord and self.current_chord_label:
            self.current_chord_label.config(text=current_chord)

        logger.debug(f"Zobrazen akord: {current_chord} na pozici {current_index}")

    def reset_display(self) -> None:
        """Resetuje zobrazení progression playeru."""
        if self.current_chord_label:
            self.current_chord_label.config(text="-")

        # Vymaže všechna tlačítka
        for widget in self.prog_chord_frame.winfo_children():
            widget.destroy()

        self.prog_chord_buttons.clear()
        logger.debug("Zobrazení progression playeru resetováno")
