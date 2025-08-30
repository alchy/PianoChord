# gui_keyboard.py
"""
gui_keyboard.py - Vizuální komponenta klaviatury pro GUI.
Obsahuje třídy pro kreslení kláves a klaviatury.
"""

import tkinter as tk
from typing import List, Tuple

from constants import MusicalConstants

# DEBUG importováno z constants.py (pokud potřeba, ale zde vypnuto pro méně spamu)
DEBUG = False


class PianoKey:
    """Reprezentuje jednu klavesu na klaviature."""

    def __init__(self, key_nr: int):
        self.key_nr = key_nr
        self.relative_key_nr = (key_nr + 9) % 12  # A0 je 0, C je 3
        self.octave = (key_nr + 9) // 12
        self.key_desc = MusicalConstants.PIANO_KEYS[self.relative_key_nr]
        self.is_sharp = self.key_desc in MusicalConstants.BLACK_KEYS
        self.fill = "black" if self.is_sharp else "white"
        self.bbox = self._calculate_bbox()

    def _calculate_bbox(self) -> Tuple[int, int, int, int]:
        """Vypocita pozici a velikost klavesy na platne."""
        white_key_map = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]

        white_key_index = self.octave * 7 + white_key_map[self.relative_key_nr]
        x_pos = white_key_index * MusicalConstants.WHITE_KEY_WIDTH

        if self.is_sharp:
            x_pos += MusicalConstants.WHITE_KEY_WIDTH - (MusicalConstants.BLACK_KEY_WIDTH / 2)
            width = MusicalConstants.BLACK_KEY_WIDTH
            height = MusicalConstants.BLACK_KEY_HEIGHT
        else:
            width = MusicalConstants.WHITE_KEY_WIDTH
            height = MusicalConstants.WHITE_KEY_HEIGHT

        return (x_pos, 0, x_pos + width, height)


class ArchetypeKeyboard:
    """Hlavni trida pro kresleni a ovladani klaviatury v GUI."""

    def __init__(self, canvas: tk.Canvas, nr_of_keys: int):
        self.canvas = canvas
        self.nr_of_keys = nr_of_keys
        self.keys = [PianoKey(i) for i in range(nr_of_keys)]
        self.highlighted_keys_ids = []

    def draw(self, keys_to_highlight: List[int] = None, color: str = "red"):
        """Nakresli klaviaturu a volitelne zvyrazni klavesy."""
        if keys_to_highlight is None:
            keys_to_highlight = []

        self.canvas.delete("all")
        self.highlighted_keys_ids.clear()

        if DEBUG:
            print(f"Kreslím klaviaturu, zvýrazňuji klávesy: {keys_to_highlight} barvou: {color}")

        # Nejdriv bile klavesy
        for key in self.keys:
            if not key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

        # Pak cerne klavesy (aby prekryvaly bile)
        for key in self.keys:
            if key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

    def _draw_key(self, key: PianoKey, is_highlighted: bool, highlight_color: str):
        """Pomocna metoda pro vykresleni jedne klavesy."""
        fill = highlight_color if is_highlighted else key.fill
        outline = "black"
        width = 2 if is_highlighted else 1

        rect = self.canvas.create_rectangle(
            key.bbox, fill=fill, outline=outline, width=width, tags="key"
        )
        if is_highlighted:
            self.highlighted_keys_ids.append(rect)

    def clear_highlights(self):
        """Odebere zvyrazneni ze vsech klaves."""
        self.draw()

    @property
    def total_width(self) -> int:
        """Vrati celkovou sirku klaviatury pro centrovani v GUI."""
        return 52 * MusicalConstants.WHITE_KEY_WIDTH  # 52 bílých kláves na 88-klávesové klaviatuře