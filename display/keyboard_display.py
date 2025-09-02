# display/keyboard_display.py
"""
display/keyboard_display.py - Vizuální klaviatura s automatickým MIDI přehrávánám.
Kombinuje vykreslení klaviatury s automatickým voláním MIDI playeru.
Může být použita i bez MIDI (jen vizuálně).
"""

import logging
import tkinter as tk
from typing import List, Tuple, Optional, TYPE_CHECKING
from config import MusicalConstants
from core.chord_analyzer import midi_to_key_number

if TYPE_CHECKING:
    from core.app_state import ApplicationState
    from midi.player import MidiPlayer

logger = logging.getLogger(__name__)

DEBUG = False


class PianoKey:
    """Reprezentuje jednu klavesu na klaviatuře s geometrickými vlastnostmi."""

    def __init__(self, key_nr: int):
        """
        Inicializuje klavesu s vypočítanými geometrickými vlastnostmi.

        Args:
            key_nr: Číslo klávesy (0-87 pro 88-klávesovou klaviaturu)
        """
        self.key_nr = key_nr
        self.relative_key_nr = (key_nr + 9) % 12  # A0 je 0, C je 3
        self.octave = (key_nr + 9) // 12
        self.key_desc = MusicalConstants.PIANO_KEYS[self.relative_key_nr]
        self.is_sharp = self.key_desc in MusicalConstants.BLACK_KEYS
        self.fill = "black" if self.is_sharp else "white"
        self.bbox = self._calculate_bbox()

    def _calculate_bbox(self) -> Tuple[int, int, int, int]:
        """Vypočítá pozici a velikost klávesy na plátně."""
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


class KeyboardDisplay:
    """
    Hlavní třída pro kreslení klaviatury s automatickým MIDI přehrávánám.
    Při každém vykreslení akordu automaticky spouští MIDI přehrávání (pokud je zapnuto).
    """

    def __init__(self, canvas: tk.Canvas, app_state: 'ApplicationState', midi_player: 'MidiPlayer' = None,
                 nr_of_keys: int = 88):
        """
        Inicializuje klaviaturu s Canvas a připojení na stav aplikace.

        Args:
            canvas: tkinter Canvas pro kreslení
            app_state: Instance ApplicationState pro stav aplikace
            midi_player: Instance MidiPlayer pro přehrávání (volitelné)
            nr_of_keys: Počet kláves (výchozí 88)
        """
        self.canvas = canvas
        self.app_state = app_state
        self.midi_player = midi_player
        self.nr_of_keys = nr_of_keys

        # Vytvoření kláves
        self.keys = [PianoKey(i) for i in range(nr_of_keys)]
        self.highlighted_keys_ids = []

        # Cache pro optimalizaci
        self._last_highlighted_keys = []
        self._last_color = ""

        logger.debug(f"KeyboardDisplay inicializován s {nr_of_keys} klávesami")

    def draw(self, keys_to_highlight: List[int] = None, color: str = "red", auto_midi: bool = True) -> None:
        """
        Nakreslí klaviaturu a volitelně zvýrazní klávesy.
        KLÍČOVÁ METODA: Automaticky spustí MIDI přehrávání při každém vykreslení.

        Args:
            keys_to_highlight: Seznam čísel kláves k zvýraznění (0-87)
            color: Barva pro zvýraznění
            auto_midi: Pokud True, automaticky přehraje MIDI (default True)
        """
        if keys_to_highlight is None:
            keys_to_highlight = []

        # Optimalizace - překreslí pouze pokud se změnilo
        if (keys_to_highlight == self._last_highlighted_keys and
                color == self._last_color and
                not auto_midi):  # Pokud není MIDI, může přeskočit
            logger.debug("Přeskakuji překreslení - beze změny")
            return

        self._last_highlighted_keys = keys_to_highlight.copy()
        self._last_color = color

        logger.debug(f"Kreslím klaviaturu, zvýrazňuji klávesy: {keys_to_highlight} barvou: {color}")

        # Vyčistí Canvas
        self.canvas.delete("all")
        self.highlighted_keys_ids.clear()

        # Nejdřív bílé klávesy (v pozadí)
        for key in self.keys:
            if not key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

        # Pak černé klávesy (v popředí)
        for key in self.keys:
            if key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

        # AUTOMATICKÉ MIDI PŘEHRÁVÁNÍ
        if auto_midi and keys_to_highlight and self.app_state.midi_enabled and self.midi_player:
            self._play_highlighted_keys_midi(keys_to_highlight)

    def draw_chord_by_midi_notes(self, midi_notes: List[int], color: str = "red", auto_midi: bool = True) -> None:
        """
        Nakreslí akord zadaný pomocí MIDI čísel not.
        Automaticky převede MIDI čísla na čísla kláves.

        Args:
            midi_notes: Seznam MIDI čísel not k zobrazení
            color: Barva zvýraznění
            auto_midi: Automatické MIDI přehrávání
        """
        if not midi_notes:
            self.draw([], color, auto_midi)
            return

        # Převod MIDI čísel na čísla kláves
        keys_to_highlight = []
        for midi_note in midi_notes:
            try:
                key_number = midi_to_key_number(midi_note)
                if 0 <= key_number < self.nr_of_keys:
                    keys_to_highlight.append(key_number)
                else:
                    logger.warning(f"MIDI nota {midi_note} je mimo rozsah klaviatury")
            except Exception as e:
                logger.error(f"Chyba při převodu MIDI noty {midi_note}: {e}")

        self.draw(keys_to_highlight, color, auto_midi)

    def draw_chord_by_name(self, chord_name: str, voicing_type: str = None, auto_midi: bool = True) -> None:
        """
        Nakreslí akord zadaný názvem s automatickým voicing výběrem.

        Args:
            chord_name: Název akordu (např. "Cmaj7")
            voicing_type: Typ voicingu (None = použije z app_state)
            auto_midi: Automatické MIDI přehrávání
        """
        try:
            from core.chord_analyzer import ChordAnalyzer
            from core.music_theory import parse_chord_name

            # Parse názvu akordu
            base_note, chord_type = parse_chord_name(chord_name)

            # Získá voicing typ
            if voicing_type is None:
                voicing_type = self.app_state.get_voicing_type()

            # Získá MIDI noty podle voicing typu
            prev_chord_midi = None
            if voicing_type == "smooth":
                prev_chord_midi = self.app_state.get_previous_chord_midi()

            midi_notes = ChordAnalyzer.get_chord_voicing(
                base_note, chord_type, voicing_type, prev_chord_midi
            )

            # Určí barvu podle voicing typu
            color_map = {"root": "red", "smooth": "green", "drop2": "blue"}
            color = color_map.get(voicing_type, "red")

            # Vykreslí s automatickým MIDI
            self.draw_chord_by_midi_notes(midi_notes, color, auto_midi)

            # Aktualizuje stav pro smooth voicing (pokud bylo přehráno)
            if auto_midi and self.app_state.midi_enabled:
                self.app_state.set_chord_played(chord_name, midi_notes)

            logger.info(f"Vykreslen akord {chord_name} ({voicing_type} voicing)")

        except Exception as e:
            logger.error(f"Chyba při vykreslení akordu {chord_name}: {e}")
            self.clear_highlights()

    def _draw_key(self, key: PianoKey, is_highlighted: bool, highlight_color: str) -> None:
        """
        Pomocná metoda pro vykreslení jedné klávesy.

        Args:
            key: Instance PianoKey k vykreslení
            is_highlighted: Zda má být klávesa zvýrazněna
            highlight_color: Barva zvýraznění
        """
        fill = highlight_color if is_highlighted else key.fill
        outline = "black"
        width = 2 if is_highlighted else 1

        rect = self.canvas.create_rectangle(
            key.bbox, fill=fill, outline=outline, width=width, tags="key"
        )

        if is_highlighted:
            self.highlighted_keys_ids.append(rect)

        # Debug informace
        if DEBUG:
            # Přidá text s číslem klávesy na každou klávesu
            center_x = (key.bbox[0] + key.bbox[2]) / 2
            center_y = key.bbox[3] - 10
            self.canvas.create_text(center_x, center_y, text=str(key.key_nr),
                                    font=("Arial", 8), fill="white" if key.is_sharp else "black")

    def _play_highlighted_keys_midi(self, key_numbers: List[int]) -> None:
        """
        Přehraje MIDI pro zvýrazněné klávesy.

        Args:
            key_numbers: Seznam čísel kláves k přehrání
        """
        if not self.midi_player:
            logger.debug("MIDI player není dostupný")
            return

        try:
            # Převede čísla kláves na MIDI noty
            from core.chord_analyzer import key_number_to_midi

            midi_notes = []
            for key_num in key_numbers:
                try:
                    midi_note = key_number_to_midi(key_num)
                    midi_notes.append(midi_note)
                except Exception as e:
                    logger.warning(f"Chyba při převodu klávesy {key_num} na MIDI: {e}")

            if midi_notes:
                # Přehraje MIDI akord
                velocity = self.app_state.midi_velocity
                self.midi_player.set_velocity(velocity)
                success = self.midi_player.play_chord(midi_notes)

                if success:
                    logger.debug(f"MIDI přehrán automaticky: {len(midi_notes)} not, velocity={velocity}")
                else:
                    logger.warning("Automatické MIDI přehrávání selhalo")
            else:
                logger.warning("Žádné platné MIDI noty k přehrání")

        except Exception as e:
            logger.error(f"Chyba při automatickém MIDI přehrávání: {e}")

    def clear_highlights(self) -> None:
        """Odebere zvýraznění ze všech kláves a zastaví MIDI."""
        self.draw([], "red", auto_midi=False)  # Bez MIDI při mazání

        # Volitelně zastaví všechny MIDI noty
        if self.midi_player and self.app_state.midi_enabled:
            self.midi_player.stop_all_notes()

        logger.debug("Zvýraznění klaviatury vyčištěno")

    def set_midi_player(self, midi_player: 'MidiPlayer') -> None:
        """
        Nastaví nebo změní MIDI player.

        Args:
            midi_player: Nová instance MidiPlayer
        """
        self.midi_player = midi_player
        logger.info("MIDI player nastaven pro KeyboardDisplay")

    def get_total_width(self) -> int:
        """
        Vrací celkovou šířku klaviatury pro centrování v GUI.

        Returns:
            int: Šířka klaviatury v pixelech
        """
        return 52 * MusicalConstants.WHITE_KEY_WIDTH  # 52 bílých kláves na 88-klávesové klaviatuře

    def get_key_at_position(self, x: int, y: int) -> Optional[PianoKey]:
        """
        Najde klávesu na dané pozici (pro interaktivitu).

        Args:
            x: X souřadnice na Canvas
            y: Y souřadnice na Canvas

        Returns:
            Optional[PianoKey]: Klávesa na pozici nebo None
        """
        # Nejdřív testuje černé klávesy (jsou v popředí)
        for key in self.keys:
            if key.is_sharp and self._point_in_bbox(x, y, key.bbox):
                return key

        # Pak bílé klávesy
        for key in self.keys:
            if not key.is_sharp and self._point_in_bbox(x, y, key.bbox):
                return key

        return None

    def _point_in_bbox(self, x: int, y: int, bbox: Tuple[int, int, int, int]) -> bool:
        """
        Testuje, zda je bod uvnitř bounding boxu.

        Args:
            x, y: Souřadnice bodu
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            bool: True pokud je bod uvnitř
        """
        x1, y1, x2, y2 = bbox
        return x1 <= x <= x2 and y1 <= y <= y2

    def setup_interactivity(self, on_key_click: callable = None) -> None:
        """
        Nastaví interaktivitu klaviatury (klikání na klávesy).

        Args:
            on_key_click: Callback funkce volaná při kliknutí (key: PianoKey) -> None
        """

        def handle_click(event):
            key = self.get_key_at_position(event.x, event.y)
            if key and on_key_click:
                try:
                    on_key_click(key)
                except Exception as e:
                    logger.error(f"Chyba v callback pro klik na klávesu: {e}")

        self.canvas.bind("<Button-1>", handle_click)
        logger.info("Interaktivita klaviatury nastavena")

    def get_debug_info(self) -> dict:
        """
        Vrací debug informace pro troubleshooting.

        Returns:
            dict: Debug informace o klaviatuře
        """
        return {
            "canvas_configured": self.canvas is not None,
            "keys_count": len(self.keys),
            "highlighted_keys_count": len(self.highlighted_keys_ids),
            "last_highlighted": self._last_highlighted_keys.copy(),
            "last_color": self._last_color,
            "midi_player_available": self.midi_player is not None,
            "midi_enabled": self.app_state.midi_enabled if self.app_state else False,
            "total_width": self.get_total_width()
        }


if __name__ == "__main__":
    # Jednoduché testování KeyboardDisplay
    print("=== Test KeyboardDisplay ===")

    # Test bez GUI (simulace)
    print("\n1. Test PianoKey:")
    key = PianoKey(39)  # C4
    print(f"Klávesa {key.key_nr}: {key.key_desc} (oktáva {key.octave})")
    print(f"Je černá: {key.is_sharp}")
    print(f"Bounding box: {key.bbox}")

    # Test více kláves
    print("\n2. Test více kláves:")
    test_keys = [21, 39, 60, 87]  # A0, C4, C5, C8
    for key_nr in test_keys:
        if key_nr < 88:
            key = PianoKey(key_nr)
            print(f"Klávesa {key_nr}: {key.key_desc}{key.octave} ({'černá' if key.is_sharp else 'bílá'})")

    # Simulace bez GUI
    print("\n3. Test bez Canvas (simulace):")
    from core.app_state import ApplicationState


    # Vytvoření mock objektů
    class MockCanvas:
        def delete(self, *args): pass

        def create_rectangle(self, *args, **kwargs): return 1

        def create_text(self, *args, **kwargs): return 2

        def bind(self, *args, **kwargs): pass


    mock_canvas = MockCanvas()
    app_state = ApplicationState()

    # Test KeyboardDisplay bez MIDI
    keyboard = KeyboardDisplay(mock_canvas, app_state, midi_player=None)
    print(f"Klaviatura má {len(keyboard.keys)} kláves")
    print(f"Celková šířka: {keyboard.get_total_width()} pixelů")

    # Test debug informací
    debug_info = keyboard.get_debug_info()
    print(f"Debug info: {debug_info}")

    # Test vykreslení akordů (simulace)
    print("\n4. Test vykreslení akordů:")

    # Test MIDI not
    test_midi_notes = [60, 64, 67, 71]  # Cmaj7
    print(f"Test MIDI not: {test_midi_notes}")
    keyboard.draw_chord_by_midi_notes(test_midi_notes, "red", auto_midi=False)
    print("MIDI noty vykresleny (simulace)")

    # Test převodu MIDI na klávesy
    from core.chord_analyzer import midi_to_key_number

    keys_for_chord = [midi_to_key_number(note) for note in test_midi_notes]
    print(f"MIDI {test_midi_notes} -> klávesy {keys_for_chord}")

    # Test hledání klávesy na pozici
    print("\n5. Test pozice kláves:")
    test_key = keyboard.get_key_at_position(100, 50)
    if test_key:
        print(f"Na pozici (100, 50) je klávesa: {test_key.key_desc}")
    else:
        print("Na pozici (100, 50) není žádná klávesa")

    print("\n=== Test dokončen ===")
    print("POZNÁMKA: Pro plnou funkcionalitu potřebujete skutečný tkinter Canvas a MIDI player")
