# music_staff.py
"""
Module for drawing music staff (notová osnova) with notes.
"""

import tkinter as tk
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class MusicStaffDisplay:
    """
    Kreslí notovou osnovu s houslový klíčem a notami.
    """

    def __init__(self, canvas: tk.Canvas, width: int = 400, height: int = 200):
        # Input: canvas (tk.Canvas), width (int), height (int)
        # Description: Inicializuje music staff display
        # Output: None
        # Called by: TrainingWindow
        self.canvas = canvas
        self.width = width
        self.height = height

        # Parametry osnovy
        self.staff_left = 50
        self.staff_right = width - 50
        self.staff_center_y = height // 2
        self.line_spacing = 12  # Mezera mezi linkami

        # Noty - mapování MIDI note na pozici na osnově (v půl-tónech od C4)
        self.note_positions = self._create_note_positions()

    def _create_note_positions(self) -> dict:
        """
        Vytvoří mapování MIDI note numbers na pozice na osnově.
        C4 (middle C, MIDI 60) = první pomocná linka pod osnovou

        Returns:
            dict: {midi_note: (line_position, accidental)}
        """
        # Pozice v půl-linkách od spodní linky osnovy (E4 = 0)
        # Negativní = pod osnovou, pozitivní = nad osnovou
        # C dur stupnice pozice (bez předznamenání):
        # C=0, D=1, E=2(linka), F=3, G=4(linka), A=5, B=6(linka), C=7, D=8(linka), E=9, F=10(linka)

        base_notes = {
            'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6
        }

        positions = {}

        # Generuj pro rozsah MIDI 21-108 (celá klaviatura)
        for midi in range(21, 109):
            octave = (midi - 12) // 12
            pitch_class = midi % 12

            # Mapování pitch class na notu a accidental
            note_map = {
                0: ('C', ''), 1: ('C', '#'), 2: ('D', ''),
                3: ('D', '#'), 4: ('E', ''), 5: ('F', ''),
                6: ('F', '#'), 7: ('G', ''), 8: ('G', '#'),
                9: ('A', ''), 10: ('A', '#'), 11: ('B', '')
            }

            note_name, accidental = note_map[pitch_class]

            # Pozice relativní k E4 (MIDI 64)
            # E4 je spodní linka osnovy (pozice 0)
            base_position = base_notes[note_name]
            octave_offset = (octave - 4) * 7  # 7 pozic = 1 oktáva

            line_position = base_position + octave_offset

            positions[midi] = (line_position, accidental)

        return positions

    def clear(self):
        """Vyčistí canvas."""
        self.canvas.delete("all")

    def _draw_treble_clef(self):
        """
        Nakreslí houslový klíč (G-clef) graficky.
        """
        clef_x = self.staff_left + 15
        center_y = self.staff_center_y

        # Zjednodušená verze houslového klíče pomocí křivek
        # Začíná na G lince (druhá linka zdola)
        g_line_y = center_y - self.line_spacing

        # Spodní smyčka
        self.canvas.create_oval(
            clef_x - 8, g_line_y - 8,
            clef_x + 8, g_line_y + 8,
            outline="black", width=2, tags="clef"
        )

        # Vertikální linie nahoru
        self.canvas.create_line(
            clef_x + 6, g_line_y,
            clef_x + 4, g_line_y - 40,
            width=3, smooth=True, tags="clef"
        )

        # Horní smyčka
        self.canvas.create_arc(
            clef_x - 5, g_line_y - 50,
            clef_x + 10, g_line_y - 30,
            start=0, extent=270,
            outline="black", width=2, style="arc", tags="clef"
        )

        # Dolní spirála
        self.canvas.create_arc(
            clef_x - 10, g_line_y + 5,
            clef_x + 5, g_line_y + 25,
            start=180, extent=180,
            outline="black", width=2, style="arc", tags="clef"
        )

    def draw_staff(self):
        """
        Nakreslí prázdnou notovou osnovu s houslový klíčem.
        """
        self.clear()

        # 5 linek osnovy (E, G, B, D, F od spodu)
        for i in range(5):
            y = self.staff_center_y - (2 * self.line_spacing) + (i * self.line_spacing)
            self.canvas.create_line(
                self.staff_left, y,
                self.staff_right, y,
                fill="black", width=1, tags="staff"
            )

        # Houslový klíč (grafická verze)
        self._draw_treble_clef()

    def draw_notes(self, midi_notes: List[int], use_sharps: bool = True):
        """
        Nakreslí noty na osnově.

        Args:
            midi_notes: Seznam MIDI note numbers
            use_sharps: True = použít křížky (#), False = použít béčka (b)
        """
        self.draw_staff()

        if not midi_notes:
            return

        # Seřaď noty od nejnižší
        sorted_notes = sorted(midi_notes)

        # Pozice X pro noty (rozložené vedle sebe)
        note_x_start = self.staff_left + 100
        note_spacing = min(50, (self.staff_right - note_x_start - 50) / max(len(sorted_notes), 1))

        for i, midi_note in enumerate(sorted_notes):
            x = note_x_start + (i * note_spacing)
            self._draw_single_note(midi_note, x, use_sharps)

    def _draw_single_note(self, midi_note: int, x: float, use_sharps: bool = True):
        """
        Nakreslí jednu notu.

        Args:
            midi_note: MIDI note number
            x: X pozice
            use_sharps: Použít křížky nebo béčka
        """
        if midi_note not in self.note_positions:
            logger.warning(f"MIDI note {midi_note} out of range")
            return

        line_position, accidental = self.note_positions[midi_note]

        # Vypočítej Y pozici (spodní linka osnovy = E4 = pozice 0)
        # Každá pozice = půl mezery mezi linkami (6px)
        base_y = self.staff_center_y + (2 * self.line_spacing)  # E4 = spodní linka
        y = base_y - (line_position * (self.line_spacing / 2))

        # Pomocné linky (ledger lines) pokud je nota mimo osnovu
        # Krátké čárky jen kolem noty
        ledger_length = 18  # Délka pomocné linky

        if line_position < 0:  # Pod osnovou
            # Kreslíme ledger lines pro sudé pozice (na linkách)
            for ledger_pos in range(0, line_position - 1, -2):
                ledger_y = base_y - (ledger_pos * (self.line_spacing / 2))
                self.canvas.create_line(
                    x - ledger_length, ledger_y,
                    x + ledger_length, ledger_y,
                    fill="black", width=1.5, tags="ledger"
                )
        elif line_position > 8:  # Nad osnovou (F5 = pozice 8, top line)
            # Kreslíme ledger lines pro sudé pozice (na linkách)
            for ledger_pos in range(10, line_position + 1, 2):
                ledger_y = base_y - (ledger_pos * (self.line_spacing / 2))
                self.canvas.create_line(
                    x - ledger_length, ledger_y,
                    x + ledger_length, ledger_y,
                    fill="black", width=1.5, tags="ledger"
                )

        # Nota (ovál)
        note_radius = 8
        self.canvas.create_oval(
            x - note_radius, y - note_radius,
            x + note_radius, y + note_radius,
            fill="black", outline="black", width=2, tags="note"
        )

        # Předznamenání (accidental) - grafické vykreslení
        if accidental:
            self._draw_accidental(x - 22, y, accidental, use_sharps)

    def _draw_accidental(self, x: float, y: float, accidental: str, use_sharps: bool):
        """
        Graficky vykreslí předznamenání (křížek nebo béčko).

        Args:
            x: X pozice
            y: Y pozice (střed noty)
            accidental: '#' nebo 'b'
            use_sharps: Preferovat křížky
        """
        if accidental == '#' or (accidental and use_sharps):
            # Křížek (#) - dvě vertikální a dvě horizontální čáry
            # Vertikální čáry
            self.canvas.create_line(
                x - 4, y - 8,
                x - 4, y + 8,
                fill="black", width=2, tags="accidental"
            )
            self.canvas.create_line(
                x + 4, y - 8,
                x + 4, y + 8,
                fill="black", width=2, tags="accidental"
            )
            # Horizontální čáry (trochu šikmé)
            self.canvas.create_line(
                x - 6, y - 3,
                x + 6, y - 5,
                fill="black", width=2, tags="accidental"
            )
            self.canvas.create_line(
                x - 6, y + 3,
                x + 6, y + 1,
                fill="black", width=2, tags="accidental"
            )
        else:
            # Béčko (b) - vertikální čára a ovál
            # Vertikální čára
            self.canvas.create_line(
                x, y - 10,
                x, y + 5,
                fill="black", width=2, tags="accidental"
            )
            # Dolní ovál
            self.canvas.create_oval(
                x - 5, y - 2,
                x + 5, y + 8,
                outline="black", width=1.5, tags="accidental"
            )

    def draw_chord_notes(self, chord_name: str, midi_notes: List[int]):
        """
        Nakreslí noty akordu na osnově.

        Args:
            chord_name: Název akordu (pro určení předznamenání)
            midi_notes: MIDI note numbers akordu
        """
        # Určíme, zda použít křížky nebo béčka podle názvu akordu
        use_sharps = '#' in chord_name or 'sharp' in chord_name.lower()

        self.draw_notes(midi_notes, use_sharps)

    def draw_single_note_display(self, note_name: str, midi_note: int):
        """
        Nakreslí jednu notu pro Note Training.

        Args:
            note_name: Název noty (např. "F#", "Db")
            midi_note: MIDI note number
        """
        use_sharps = '#' in note_name
        self.draw_notes([midi_note], use_sharps)
