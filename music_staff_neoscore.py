# music_staff_neoscore.py
"""
Module for drawing music staff (notová osnova) with notes using neoscore library.
Falls back to Tkinter-based rendering if neoscore is not available.
"""

import tkinter as tk
from typing import List, Optional
import logging
import tempfile
import os
from pathlib import Path as PathlibPath

logger = logging.getLogger(__name__)

# Try to import neoscore
NEOSCORE_AVAILABLE = False
try:
    from neoscore.core import neoscore
    from neoscore.core.units import Mm
    from neoscore.western import staff, clef, chordrest
    NEOSCORE_AVAILABLE = True
    logger.info("Neoscore library loaded successfully")
except ImportError as e:
    logger.warning(f"Neoscore not available, falling back to Tkinter rendering: {e}")
    # Fallback - import original Tkinter-based implementation
    from music_staff import MusicStaffDisplay as TkMusicStaffDisplay


class MusicStaffDisplay:
    """
    Kreslí notovou osnovu s houslový klíčem a notami.
    Používá neoscore pro profesionální rendering, s fallback na Tkinter.
    """

    def __init__(self, canvas: tk.Canvas, width: int = 400, height: int = 200):
        """
        Inicializuje music staff display.

        Args:
            canvas: Tkinter Canvas widget
            width: Šířka canvasu
            height: Výška canvasu
        """
        self.canvas = canvas
        self.width = width
        self.height = height
        self.use_neoscore = NEOSCORE_AVAILABLE

        # Temporary directory for rendered images
        self.temp_dir = PathlibPath(tempfile.gettempdir()) / "pianochord_notation"
        self.temp_dir.mkdir(exist_ok=True)

        # Current image reference (for Tkinter PhotoImage)
        self.current_image = None

        # Fallback to Tkinter implementation if neoscore not available
        if not self.use_neoscore:
            logger.info("Using Tkinter-based staff display (fallback mode)")
            self.tk_display = TkMusicStaffDisplay(canvas, width, height)
        else:
            logger.info("Using neoscore-based staff display")
            self.tk_display = None

    def clear(self):
        """Vyčistí canvas."""
        self.canvas.delete("all")
        self.current_image = None

    def draw_staff(self):
        """
        Nakreslí prázdnou notovou osnovu s houslový klíčem.
        """
        if not self.use_neoscore:
            # Fallback na Tkinter
            self.tk_display.draw_staff()
            return

        # Render using neoscore
        self._render_neoscore([], None)

    def draw_notes(self, midi_notes: List[int], use_sharps: bool = True):
        """
        Nakreslí noty na osnově.

        Args:
            midi_notes: Seznam MIDI note numbers
            use_sharps: True = použít křížky (#), False = použít béčka (b)
        """
        logger.info(f"[MUSIC_STAFF] draw_notes called: {len(midi_notes)} notes, use_neoscore={self.use_neoscore}")

        if not self.use_neoscore:
            # Fallback na Tkinter
            logger.info("[MUSIC_STAFF] Using Tkinter fallback")
            self.tk_display.draw_notes(midi_notes, use_sharps)
            return

        # Render using neoscore
        logger.info("[MUSIC_STAFF] Using neoscore rendering")
        self._render_neoscore(midi_notes, use_sharps)

    def draw_chord_notes(self, chord_name: str, midi_notes: List[int]):
        """
        Nakreslí noty akordu na osnově (noty nad sebou).

        Args:
            chord_name: Název akordu (pro určení předznamenání)
            midi_notes: MIDI note numbers akordu
        """
        logger.info(f"[MUSIC_STAFF] draw_chord_notes called: chord={chord_name}, {len(midi_notes)} notes, use_neoscore={self.use_neoscore}")

        if not self.use_neoscore:
            # Fallback na Tkinter
            logger.info("[MUSIC_STAFF] Using Tkinter fallback for chord")
            self.tk_display.draw_chord_notes(chord_name, midi_notes)
            return

        # Určíme, zda použít křížky nebo béčka podle názvu akordu
        use_sharps = '#' in chord_name or 'sharp' in chord_name.lower()
        logger.info(f"[MUSIC_STAFF] Using neoscore rendering for chord, use_sharps={use_sharps}")

        # Pro akord používáme speciální render jako vertikální seskupení
        self._render_neoscore_chord(midi_notes, use_sharps)

    def draw_single_note_display(self, note_name: str, midi_note: int):
        """
        Nakreslí jednu notu pro Note Training.

        Args:
            note_name: Název noty (např. "F#", "Db")
            midi_note: MIDI note number
        """
        logger.info(f"[MUSIC_STAFF] draw_single_note_display called: note={note_name}, midi={midi_note}, use_neoscore={self.use_neoscore}")

        if not self.use_neoscore:
            # Fallback na Tkinter
            logger.info("[MUSIC_STAFF] Using Tkinter fallback for single note")
            self.tk_display.draw_single_note_display(note_name, midi_note)
            return

        use_sharps = '#' in note_name
        logger.info(f"[MUSIC_STAFF] Using neoscore rendering for single note, use_sharps={use_sharps}")
        self.draw_notes([midi_note], use_sharps)

    def _render_neoscore_chord(self, midi_notes: List[int], use_sharps: bool = True):
        """
        Vykreslí akord pomocí neoscore (všechny noty nad sebou na stejné x pozici).

        Args:
            midi_notes: MIDI note numbers akordu
            use_sharps: True = křížky, False = béčka
        """
        try:
            logger.info(f"Rendering chord with neoscore: {len(midi_notes)} notes")

            # Initialize neoscore document
            neoscore.setup()

            # Create staff with treble clef
            staff_obj = staff.Staff((Mm(10), Mm(20)), None, Mm(156))
            clef.Clef(Mm(0), staff_obj, 'treble')
            logger.info("Staff and clef created")

            if midi_notes:
                # Convert all MIDI notes to pitch strings
                pitch_strings = []
                for midi_note in sorted(midi_notes):
                    pitch_str = self._midi_to_neoscore_pitch(midi_note, use_sharps)
                    pitch_strings.append(pitch_str)
                    logger.info(f"  MIDI {midi_note} -> {pitch_str}")

                # Create single Chordrest with all notes (they will be stacked vertically)
                x_pos = Mm(40)  # Center position for chord
                chordrest.Chordrest(
                    x_pos,
                    staff_obj,
                    pitch_strings,  # All notes in the chord
                    (1, 4)  # Quarter note duration
                )
                logger.info(f"Chord created with {len(pitch_strings)} notes at same position")

            # Render to image file
            output_path = self.temp_dir / "staff_output.png"
            neoscore.render_image(
                rect=None,
                dest=str(output_path),
                dpi=150,
                autocrop=True,
                quality=-1
            )

            # Cleanup neoscore
            neoscore.shutdown()

            # Load image into Tkinter canvas
            self._display_image_on_canvas(output_path)

        except Exception as e:
            logger.error(f"Failed to render chord with neoscore: {e}", exc_info=True)
            self.clear()

    def _render_neoscore(self, midi_notes: List[int], use_sharps: Optional[bool] = True):
        """
        Vykreslí notovou osnovu pomocí neoscore a zobrazí jako obrázek v Tkinter canvas.

        Args:
            midi_notes: MIDI note numbers k vykreslení
            use_sharps: True = křížky, False = béčka, None = prázdná osnova
        """
        try:
            logger.info(f"Rendering with neoscore: {len(midi_notes) if midi_notes else 0} notes")

            # Initialize neoscore document
            neoscore.setup()

            # Create staff with treble clef
            # Staff constructor: (pos, parent, length, clef=None)
            staff_obj = staff.Staff((Mm(10), Mm(20)), None, Mm(156))

            # Add treble clef - create it as a child of the staff at position x=0
            clef.Clef(Mm(0), staff_obj, 'treble')
            logger.info("Staff and clef created")

            # Add notes if provided
            if midi_notes:
                sorted_notes = sorted(midi_notes)

                # Calculate spacing based on number of notes
                available_width = 104  # mm (30% larger)
                if len(sorted_notes) > 1:
                    note_spacing = min(20, available_width / len(sorted_notes))
                else:
                    note_spacing = 13

                # Starting position for notes (after clef)
                start_x = 25

                for i, midi_note in enumerate(sorted_notes):
                    x_pos = Mm(start_x + (i * note_spacing))

                    # Convert MIDI to neoscore pitch string
                    pitch_str = self._midi_to_neoscore_pitch(midi_note, use_sharps)

                    # Create Chordrest (automatically handles noteheads, accidentals, ledger lines)
                    # Chordrest(pos_x, staff, notes, duration)
                    # notes: list of pitch strings, duration: (numerator, denominator) tuple
                    try:
                        chordrest.Chordrest(
                            x_pos,
                            staff_obj,
                            [pitch_str],  # Single note
                            (1, 4)  # Quarter note duration
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add note MIDI {midi_note} (pitch_str={pitch_str}): {e}")
                        continue

            # Render to image file
            output_path = self.temp_dir / "staff_output.png"

            # Use render_image to create PNG
            neoscore.render_image(
                rect=None,  # Auto-determine bounds
                dest=str(output_path),
                dpi=150,
                autocrop=True,
                quality=-1  # Default quality
            )

            # Cleanup neoscore
            neoscore.shutdown()

            # Load image into Tkinter canvas
            self._display_image_on_canvas(output_path)

        except Exception as e:
            logger.error(f"Failed to render with neoscore: {e}", exc_info=True)
            # Don't fallback here - just show empty canvas
            self.clear()

    def _display_image_on_canvas(self, image_path: PathlibPath):
        """
        Zobrazí obrázek na Tkinter canvas.

        Args:
            image_path: Cesta k obrázku
        """
        try:
            from PIL import Image, ImageTk

            logger.info(f"Loading image from: {image_path}")

            # Check if file exists
            if not image_path.exists():
                logger.error(f"Image file does not exist: {image_path}")
                return

            # Load image
            img = Image.open(image_path)
            logger.info(f"Image loaded, size: {img.size}")

            # Resize to fit canvas if needed
            canvas_width = self.width - 20  # Padding
            canvas_height = self.height - 20

            # Calculate scaling
            img_width, img_height = img.size
            scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)

            if scale < 1.0:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Image resized to: {new_width}x{new_height}")

            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(img)

            # Clear canvas
            self.canvas.delete("all")

            # Center the image
            x = self.width // 2
            y = self.height // 2
            self.canvas.create_image(x, y, image=self.current_image, anchor=tk.CENTER)

            logger.info("Image displayed successfully")

        except Exception as e:
            logger.error(f"Failed to display image: {e}", exc_info=True)

    def _midi_to_neoscore_pitch(self, midi_note: int, use_sharps: bool = True) -> str:
        """
        Převede MIDI note number na neoscore pitch string.

        Args:
            midi_note: MIDI note number (0-127)
            use_sharps: True = křížky, False = béčka

        Returns:
            str: Neoscore pitch string (např. "c'", "fs''", "bf")
        """
        # MIDI note 60 = C4 (middle C)
        octave = (midi_note // 12) - 1
        pitch_class = midi_note % 12

        # Mapování pitch class na neoscore pitch notation
        if use_sharps:
            pitch_map = {
                0: 'c', 1: 'cs', 2: 'd', 3: 'ds', 4: 'e', 5: 'f',
                6: 'fs', 7: 'g', 8: 'gs', 9: 'a', 10: 'as', 11: 'b'
            }
        else:
            pitch_map = {
                0: 'c', 1: 'df', 2: 'd', 3: 'ef', 4: 'e', 5: 'f',
                6: 'gf', 7: 'g', 8: 'af', 9: 'a', 10: 'bf', 11: 'b'
            }

        pitch_name = pitch_map[pitch_class]

        # Převod oktávy na neoscore notaci (apostrof/čárka)
        # Neoscore: c = C3, c' = C4, c'' = C5, c, = C2
        if octave < 3:
            commas = ',' * (3 - octave)
            return f"{pitch_name}{commas}"
        elif octave == 3:
            return pitch_name
        else:
            apostrophes = "'" * (octave - 3)
            return f"{pitch_name}{apostrophes}"

    def _midi_to_pitch(self, midi_note: int, use_sharps: bool = True):
        """
        Převede MIDI note number na pitch name, octave a accidental type.

        Args:
            midi_note: MIDI note number (0-127)
            use_sharps: True = křížky, False = béčka

        Returns:
            Tuple[str, int, Optional[str]]: (pitch_name, octave, accidental_type)
            accidental_type může být: 'sharp', 'flat', nebo None
        """
        # MIDI note 60 = C4 (middle C)
        octave = (midi_note // 12) - 1
        pitch_class = midi_note % 12

        # Mapování pitch class
        if use_sharps:
            pitch_map = {
                0: ('c', None), 1: ('c', 'sharp'), 2: ('d', None),
                3: ('d', 'sharp'), 4: ('e', None), 5: ('f', None),
                6: ('f', 'sharp'), 7: ('g', None), 8: ('g', 'sharp'),
                9: ('a', None), 10: ('a', 'sharp'), 11: ('b', None)
            }
        else:
            pitch_map = {
                0: ('c', None), 1: ('d', 'flat'), 2: ('d', None),
                3: ('e', 'flat'), 4: ('e', None), 5: ('f', None),
                6: ('g', 'flat'), 7: ('g', None), 8: ('a', 'flat'),
                9: ('a', None), 10: ('b', 'flat'), 11: ('b', None)
            }

        pitch_name, accidental_type = pitch_map[pitch_class]
        return pitch_name, octave, accidental_type

    def _create_neoscore_pitch(self, pitch_name: str, octave: int) -> str:
        """
        Vytvoří pitch string pro neoscore.

        Neoscore používá notaci:
        - C3 = 'c' (malé c)
        - C4 = "c'" (c s apostrofem)
        - C5 = "c''" (c s dvěma apostrof)
        - C2 = "c," (c s čárkou)

        Args:
            pitch_name: Název noty (lowercase: 'c', 'd', 'e', ...)
            octave: Oktáva (0-9)

        Returns:
            Pitch string pro neoscore
        """
        # Neoscore středová oktáva je C3 (bez apostrofu nebo čárky)
        # C4 = c' (jedna apostrof)
        # C5 = c'' (dvě apostrof)
        # C2 = c, (jedna čárka)

        if octave < 3:
            # Nižší oktávy - použij čárky
            commas = ',' * (3 - octave)
            return f"{pitch_name}{commas}"
        elif octave == 3:
            # Základní oktáva
            return pitch_name
        else:
            # Vyšší oktávy - použij apostrofy
            apostrophes = "'" * (octave - 3)
            return f"{pitch_name}{apostrophes}"

    def __del__(self):
        """Cleanup temporary files."""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir.exists():
                for file in self.temp_dir.glob("*.png"):
                    try:
                        file.unlink()
                    except:
                        pass
        except:
            pass
