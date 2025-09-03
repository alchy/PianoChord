# main_app.py
"""
Vyvážené zjednodušení Piano Chord Analyzer:
- Zachovává kvalitní GUI a vykreslování
- Zjednodušuje pouze logiku a propojení komponent
- Méně souborů, ale zachovává funkcionalnost
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import json
import threading
import time
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ENHARMONIC_MAP = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}
BLACK_KEYS = {"C#", "D#", "F#", "G#", "A#"}

WHITE_KEY_WIDTH = 18
WHITE_KEY_HEIGHT = 80
BLACK_KEY_WIDTH = 12
BLACK_KEY_HEIGHT = 50

CHORD_TYPES = {
    "": [0, 4, 7], "maj": [0, 4, 7], "maj7": [0, 4, 7, 11], "maj9": [0, 4, 7, 11, 14],
    "m": [0, 3, 7], "m7": [0, 3, 7, 10], "m9": [0, 3, 7, 10, 14], "m6": [0, 3, 7, 9],
    "7": [0, 4, 7, 10], "9": [0, 4, 7, 10, 14], "13": [0, 4, 7, 10, 14, 21],
    "dim": [0, 3, 6], "dim7": [0, 3, 6, 9], "aug": [0, 4, 8],
    "sus2": [0, 2, 7], "sus4": [0, 5, 7], "m7b5": [0, 3, 6, 10],
    "6": [0, 4, 7, 9], "7b9": [0, 4, 7, 10, 13], "7b5": [0, 4, 6, 10]
}


class MusicCore:
    """
    Zjednodušená ale plně funkční hudební logika.
    Kombinuje původní ChordAnalyzer + ProgressionManager + ApplicationState.
    """

    def __init__(self):
        self.voicing_type = "root"
        self.midi_enabled = True
        self.midi_velocity = 64
        self.previous_chord_midi = []

        self.current_progression = []
        self.current_index = 0
        self.progression_source = ""

        self.database = self._load_database()
        self.transposed_database = self._create_transposed_database()
        self.genres_cache = self._build_genres_cache()

        self.midi_player = self._setup_midi()

        logger.info("MusicCore inicializován")

    def _load_database(self) -> Dict:
        """Načte databázi akordových progresí z JSON souboru."""
        try:
            with open('database.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Chyba při načítání databáze: {e}")
            return self._get_fallback_database()

    def _get_fallback_database(self) -> Dict:
        """Vrací fallback databázi v případě chyby načítání."""
        return {
            "ii-V-I Dur": {
                "genre": "jazz-progressions",
                "key": "C",
                "progressions": [{"chords": ["Dm7", "G7", "Cmaj7"], "description": "Základní ii-V-I"}]
            }
        }

    def _create_transposed_database(self) -> Dict:
        """Vytvoří transponované verze všech písní pro větší výběr akordů."""
        transposed = {}

        for song_name, song_data in self.database.items():
            original_key = song_data.get("key", "C")

            for semitones in range(1, 12):
                try:
                    transposed_key = self._transpose_note(original_key, semitones)

                    transposed_progressions = []
                    for prog in song_data.get("progressions", []):
                        transposed_chords = []
                        for chord in prog.get("chords", []):
                            transposed_chord = self._transpose_chord(chord, semitones)
                            transposed_chords.append(transposed_chord)

                        transposed_prog = prog.copy()
                        transposed_prog["chords"] = transposed_chords
                        transposed_progressions.append(transposed_prog)

                    transposed_song = song_data.copy()
                    transposed_song["key"] = transposed_key
                    transposed_song["progressions"] = transposed_progressions
                    transposed_song["original_key"] = original_key
                    transposed_song["transposed_by"] = semitones

                    transposed_name = f"{song_name}_trans_{semitones}"
                    transposed[transposed_name] = transposed_song

                except Exception as e:
                    logger.warning(f"Chyba při transpozici {song_name} o {semitones}: {e}")
                    continue

        logger.info(f"Vytvořeno {len(transposed)} transponovaných písní")
        return transposed

    def _transpose_note(self, note: str, semitones: int) -> str:
        """Transponuje notu o daný počet půltónů."""
        if len(note) > 1 and note[1] in {'#', 'b'}:
            base_note = note[:2]
            chord_part = note[2:]
        else:
            base_note = note[0]
            chord_part = note[1:]

        base_note = ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())
        index = PIANO_KEYS.index(base_note)
        new_index = (index + semitones) % 12
        return PIANO_KEYS[new_index] + chord_part

    def _transpose_chord(self, chord: str, semitones: int) -> str:
        """Transponuje celý akord o daný počet půltónů."""
        try:
            base_note, chord_type = self.parse_chord(chord)
            new_base_note = self._transpose_note(base_note, semitones)
            return f"{new_base_note}{chord_type}"
        except Exception as e:
            logger.warning(f"Chyba při transpozici akordu {chord}: {e}")
            return chord

    def _build_genres_cache(self) -> Dict[str, List[str]]:
        """Vytvoří cache žánrů pro rychlejší přístup."""
        genres = {}
        for song_name, song_data in self.database.items():
            genre = song_data.get("genre", "unknown")
            if genre not in genres:
                genres[genre] = []
            genres[genre].append(song_name)
        return genres

    def _setup_midi(self):
        """Nastaví MIDI výstup a vrací otevřený port."""
        self.available_ports = []
        self.current_port_index = 0

        try:
            import mido
            self.available_ports = mido.get_output_names()
            if self.available_ports:
                outport = mido.open_output(self.available_ports[0])
                logger.info(f"MIDI port: {self.available_ports[0]}")
                return outport
        except ImportError:
            logger.warning("MIDI není dostupné")
        except Exception as e:
            logger.error(f"MIDI chyba: {e}")
        return None

    def get_available_midi_ports(self) -> List[str]:
        """Vrací seznam dostupných MIDI portů."""
        return self.available_ports.copy()

    def set_midi_port(self, port_name: str) -> bool:
        """Nastaví aktivní MIDI port."""
        try:
            import mido
            if self.midi_player:
                self.midi_player.close()

            self.midi_player = mido.open_output(port_name)
            self.current_port_index = self.available_ports.index(port_name) if port_name in self.available_ports else 0
            logger.info(f"MIDI port změněn na: {port_name}")
            return True
        except Exception as e:
            logger.error(f"Chyba při změně MIDI portu: {e}")
            return False

    def get_current_midi_port(self) -> str:
        """Vrací název aktuálního MIDI portu."""
        if self.available_ports and 0 <= self.current_port_index < len(self.available_ports):
            return self.available_ports[self.current_port_index]
        return "Žádný"

    def parse_chord(self, chord_name: str) -> Tuple[str, str]:
        """Rozdělí název akordu na základní notu a typ akordu."""
        chord = chord_name.strip()
        if len(chord) > 1 and chord[1] in {'#', 'b'}:
            base_note = chord[:2]
            chord_type = chord[2:]
        else:
            base_note = chord[0]
            chord_type = chord[1:]

        base_note = ENHARMONIC_MAP.get(base_note.upper(), base_note.upper())
        if base_note not in PIANO_KEYS:
            raise ValueError(f"Neplatná nota: {base_note}")

        return base_note, chord_type

    def get_chord_midi(self, base_note: str, chord_type: str, octave: int = 4) -> List[int]:
        """Vrací MIDI noty pro daný akord."""
        intervals = CHORD_TYPES.get(chord_type, CHORD_TYPES["maj"])
        base_idx = PIANO_KEYS.index(base_note)
        base_midi = 12 * octave + base_idx
        return [base_midi + interval for interval in intervals]

    def get_voicing(self, chord_name: str) -> List[int]:
        """
        Vrací MIDI noty akordu podle vybraného typu voicingu.
        """
        try:
            base_note, chord_type = self.parse_chord(chord_name)
            root_midi = self.get_chord_midi(base_note, chord_type)

            if self.voicing_type == "smooth" and self.previous_chord_midi:
                return self._get_smooth_voicing(root_midi)
            elif self.voicing_type == "drop2":
                return self._get_drop2_voicing(root_midi)
            else:
                return root_midi
        except Exception as e:
            logger.error(f"Chyba při získávání voicingu: {e}")
            return []

    def _get_smooth_voicing(self, root_voicing: List[int]) -> List[int]:
        """Vrací smooth voicing pro minimalizaci pohybu mezi akordy."""
        best_voicing = root_voicing
        min_distance = float('inf')
        avg_prev = sum(self.previous_chord_midi) / len(self.previous_chord_midi)

        for octave_shift in range(-2, 3):
            for inversion in range(len(root_voicing)):
                inverted_notes = root_voicing[inversion:] + [note + 12 for note in root_voicing[:inversion]]
                current_voicing = [note + octave_shift * 12 for note in inverted_notes]
                avg_current = sum(current_voicing) / len(current_voicing)
                distance = abs(avg_current - avg_prev)

                if distance < min_distance:
                    min_distance = distance
                    best_voicing = current_voicing

        return best_voicing

    def _get_drop2_voicing(self, root_voicing: List[int]) -> List[int]:
        """Vrací drop-2 voicing pro akord."""
        if len(root_voicing) < 4:
            return root_voicing

        drop2_voicing = root_voicing.copy()
        sorted_notes = sorted(drop2_voicing)
        second_highest = sorted_notes[-2]
        second_highest_index = drop2_voicing.index(second_highest)
        drop2_voicing[second_highest_index] = second_highest - 12
        return sorted(drop2_voicing)

    def play_chord_midi(self, midi_notes: List[int]):
        """Přehraje MIDI noty akordu v samostatném vlákně."""
        if not self.midi_enabled or not self.midi_player or not midi_notes:
            return

        def play():
            try:
                import mido
                for note in midi_notes:
                    msg = mido.Message('note_on', note=note, velocity=self.midi_velocity)
                    self.midi_player.send(msg)

                time.sleep(1.0)

                for note in midi_notes:
                    msg = mido.Message('note_off', note=note, velocity=0)
                    self.midi_player.send(msg)
            except Exception as e:
                logger.error(f"MIDI chyba: {e}")

        thread = threading.Thread(target=play, daemon=True)
        thread.start()

    def analyze_chord(self, chord_name: str) -> Dict:
        """Provádí kompletní analýzu zadaného akordu včetně hledání progresí."""
        try:
            base_note, chord_type = self.parse_chord(chord_name)
            progressions = self.find_progressions(chord_name)

            return {
                'chord_name': chord_name,
                'base_note': base_note,
                'chord_type': chord_type,
                'progressions': progressions,
                'success': True
            }
        except Exception as e:
            return {'chord_name': chord_name, 'error': str(e), 'success': False}

    def find_progressions(self, chord_name: str) -> List[Dict]:
        """Hledá progrese obsahující zadaný akord v databázi i transponovaných verzích."""
        results = []

        for song_name, song_data in self.database.items():
            for prog in song_data.get("progressions", []):
                if chord_name in prog.get("chords", []):
                    results.append({
                        'song': song_name,
                        'chords': prog['chords'],
                        'description': prog.get('description', ''),
                        'genre': song_data.get('genre', 'unknown'),
                        'transposed_by': 0,
                        'original_key': song_data.get('key', 'Unknown')
                    })

        for song_name, song_data in self.transposed_database.items():
            for prog in song_data.get("progressions", []):
                if chord_name in prog.get("chords", []):
                    original_name = song_name.split("_trans_")[0]
                    results.append({
                        'song': original_name,
                        'chords': prog['chords'],
                        'description': prog.get('description', ''),
                        'genre': song_data.get('genre', 'unknown'),
                        'transposed_by': song_data.get('transposed_by', 0),
                        'original_key': song_data.get('original_key', 'Unknown')
                    })

        return results


class PianoKey:
    """Reprezentuje jednu klávesu na klaviatuře."""

    def __init__(self, key_nr: int):
        self.key_nr = key_nr
        self.relative_key_nr = (key_nr + 9) % 12
        self.octave = (key_nr + 9) // 12
        self.key_desc = PIANO_KEYS[self.relative_key_nr]
        self.is_sharp = self.key_desc in BLACK_KEYS
        self.fill = "black" if self.is_sharp else "white"
        self.bbox = self._calculate_bbox()

    def _calculate_bbox(self) -> Tuple[int, int, int, int]:
        """Vypočítá hranice klávesy pro vykreslení."""
        white_key_map = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
        white_key_index = self.octave * 7 + white_key_map[self.relative_key_nr]
        x_pos = white_key_index * WHITE_KEY_WIDTH

        if self.is_sharp:
            x_pos += WHITE_KEY_WIDTH - (BLACK_KEY_WIDTH / 2)
            width = BLACK_KEY_WIDTH
            height = BLACK_KEY_HEIGHT
        else:
            width = WHITE_KEY_WIDTH
            height = WHITE_KEY_HEIGHT

        return (x_pos, 0, x_pos + width, height)


class KeyboardDisplay:
    """Zpracovává vykreslování klaviatury a akordů."""

    def __init__(self, canvas: tk.Canvas, music_core: MusicCore):
        self.canvas = canvas
        self.music_core = music_core
        self.keys = [PianoKey(i) for i in range(88)]
        self.highlighted_keys_ids = []

    def _draw_empty_keyboard(self):
        """Vykreslí prázdnou klaviaturu."""
        self.canvas.delete("all")
        self.highlighted_keys_ids.clear()

        for key in self.keys:
            if not key.is_sharp:
                self._draw_key(key, False, "white")

        for key in self.keys:
            if key.is_sharp:
                self._draw_key(key, False, "black")

    def draw_chord(self, chord_name: str, auto_midi: bool = True):
        """Vykreslí akord na klaviatuře a volitelně přehraje MIDI."""
        midi_notes = self.music_core.get_voicing(chord_name)

        if midi_notes:
            self.music_core.previous_chord_midi = midi_notes.copy()

            self._draw_midi_notes(midi_notes)

            if auto_midi and self.music_core.midi_enabled:
                self.music_core.play_chord_midi(midi_notes)

        return midi_notes

    def _draw_midi_notes(self, midi_notes: List[int]):
        """Vykreslí zadané MIDI noty na klaviatuře."""
        self.canvas.delete("all")
        self.highlighted_keys_ids.clear()

        keys_to_highlight = []
        for midi_note in midi_notes:
            key_number = midi_note - 21
            if 0 <= key_number < 88:
                keys_to_highlight.append(key_number)

        colors = {"root": "red", "smooth": "green", "drop2": "blue"}
        color = colors.get(self.music_core.voicing_type, "red")

        for key in self.keys:
            if not key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

        for key in self.keys:
            if key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

    def _draw_key(self, key: PianoKey, is_highlighted: bool, highlight_color: str):
        """Vykreslí jednu klávesu."""
        fill = highlight_color if is_highlighted else key.fill
        outline = "black"
        width = 2 if is_highlighted else 1

        rect = self.canvas.create_rectangle(
            key.bbox, fill=fill, outline=outline, width=width, tags="key"
        )

        if is_highlighted:
            self.highlighted_keys_ids.append(rect)


class PianoChordAnalyzer:
    """
    Hlavní aplikace pro analýzu a přehrávání piano akordů.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.music_core = MusicCore()

        self.chord_entry = None
        self.keyboard_display = None
        self.analysis_tree = None
        self.progression_tree = None
        self.current_chord_label = None

        self.setup_gui()
        logger.info("Aplikace inicializována")

    def setup_gui(self):
        """Nastaví hlavní GUI aplikace."""
        self.root.title("Piano Chord Analyzer")
        self.root.geometry("1000x750")
        self.root.minsize(800, 600)

        self.root.rowconfigure(0, weight=2)
        self.root.rowconfigure(1, weight=0)
        self.root.rowconfigure(2, weight=3)
        self.root.columnconfigure(0, weight=1)

        self.create_keyboard_section()
        self.create_controls_section()
        self.create_output_section()

        self.root.bind('<Return>', self._handle_enter_key)
        self.root.bind('<Left>', lambda e: self.prev_chord())
        self.root.bind('<Right>', lambda e: self.next_chord())
        self.root.bind('<Up>', lambda e: self.prev_chord_silent())
        self.root.bind('<Down>', lambda e: self.next_chord_silent())

    def _handle_enter_key(self, event):
        """Zpracuje stisk Enter klávesy podle kontextu."""
        if self.root.focus_get() == self.chord_entry:
            self.analyze_chord()
        elif self.music_core.current_progression:
            current_chord = self.music_core.current_progression[self.music_core.current_index]
            self.keyboard_display.draw_chord(current_chord, auto_midi=self.midi_enabled_var.get())
            self.update_current_chord_display(current_chord)
            logger.info(f"Přehrán a vykreslen aktuální akord z progrese: {current_chord}")
        else:
            self.analyze_chord()

    def create_keyboard_section(self):
        """Vytvoří sekci s klaviaturou."""
        keyboard_frame = ttk.Frame(self.root, padding=10)
        keyboard_frame.grid(row=0, column=0, sticky="ew")
        keyboard_frame.columnconfigure(0, weight=1)

        keyboard_width = 52 * WHITE_KEY_WIDTH
        canvas = tk.Canvas(keyboard_frame, width=keyboard_width, height=100, bg="lightgray")
        canvas.grid(row=0, column=0, pady=10)

        self.keyboard_display = KeyboardDisplay(canvas, self.music_core)
        self.keyboard_display._draw_empty_keyboard()

    def create_controls_section(self):
        """Vytvoří sekci s ovládacími prvky."""
        controls_frame = ttk.Frame(self.root, padding=10)
        controls_frame.grid(row=1, column=0, sticky="ew")

        input_frame = ttk.LabelFrame(controls_frame, text="Analýza akordu", padding=10)
        input_frame.pack(fill="x", pady=5)

        ttk.Label(input_frame, text="Akord:").pack(side=tk.LEFT, padx=5)

        self.chord_entry = ttk.Entry(input_frame, width=20)
        self.chord_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(input_frame, text="Analyzovat", command=self.analyze_chord).pack(side=tk.LEFT, padx=5)

        voicing_frame = ttk.LabelFrame(input_frame, text="Voicing", padding=5)
        voicing_frame.pack(side=tk.LEFT, padx=10)

        self.voicing_var = tk.StringVar(value="root")
        for text, value in [("Root", "root"), ("Smooth", "smooth"), ("Drop2", "drop2")]:
            ttk.Radiobutton(voicing_frame, text=text, variable=self.voicing_var,
                            value=value, command=self.on_voicing_changed).pack(side=tk.LEFT, padx=2)

        midi_frame = ttk.LabelFrame(controls_frame, text="MIDI", padding=10)
        midi_frame.pack(fill="x", pady=5)

        self.midi_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(midi_frame, text="Přehrát MIDI", variable=self.midi_enabled_var,
                        command=self.on_midi_changed).pack(side=tk.LEFT, padx=5)

        ttk.Label(midi_frame, text="Velocity:").pack(side=tk.LEFT, padx=5)

        self.velocity_var = tk.DoubleVar(value=64)
        velocity_slider = ttk.Scale(midi_frame, from_=0, to=127, orient=tk.HORIZONTAL,
                                    variable=self.velocity_var, length=100,
                                    command=self.on_velocity_changed)
        velocity_slider.pack(side=tk.LEFT, padx=5)

        ttk.Label(midi_frame, text="MIDI Port:").pack(side=tk.LEFT, padx=(20, 5))

        self.midi_port_var = tk.StringVar()
        self.midi_port_combo = ttk.Combobox(midi_frame, textvariable=self.midi_port_var,
                                            width=25, state="readonly")
        self.midi_port_combo.pack(side=tk.LEFT, padx=5)
        self.midi_port_combo.bind("<<ComboboxSelected>>", self.on_midi_port_changed)

        self.populate_midi_ports()

    def create_output_section(self):
        """Vytvoří sekci s výstupem."""
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=2, column=0, sticky="nsew", pady=10)

        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="Analýza akordu")
        self.create_analysis_tab(analysis_frame)

        progression_frame = ttk.Frame(notebook)
        notebook.add(progression_frame, text="Progression Player")
        self.create_progression_tab(progression_frame)

    def create_analysis_tab(self, parent):
        """Vytvoří záložku pro analýzu akordů."""
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        columns = ("Píseň", "Progrese", "Popis", "Žánr")
        self.analysis_tree = ttk.Treeview(parent, columns=columns, show="headings")

        for col in columns:
            self.analysis_tree.heading(col, text=col)
            self.analysis_tree.column(col, width=200)

        self.analysis_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.analysis_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.analysis_tree.configure(yscrollcommand=scrollbar.set)

        self.analysis_tree.bind("<Double-1>", self.on_progression_double_click)

    def create_progression_tab(self, parent):
        """Vytvoří záložku pro přehrávání progresí."""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        nav_frame = ttk.Frame(parent, padding=10)
        nav_frame.grid(row=0, column=0, sticky="ew")

        ttk.Button(nav_frame, text="<< Předchozí", command=self.prev_chord).pack(side=tk.LEFT, padx=5)

        self.current_chord_label = ttk.Label(nav_frame, text="- žádný akord -",
                                             font=("Arial", 14, "bold"))
        self.current_chord_label.pack(side=tk.LEFT, expand=True, fill="x", padx=20)

        ttk.Button(nav_frame, text="Následující >>", command=self.next_chord).pack(side=tk.LEFT, padx=5)

        prog_frame = ttk.Frame(parent)
        prog_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        prog_frame.rowconfigure(0, weight=1)
        prog_frame.columnconfigure(0, weight=1)

        self.progression_tree = ttk.Treeview(prog_frame, columns=("Index", "Akord"), show="headings")
        self.progression_tree.heading("Index", text="#")
        self.progression_tree.heading("Akord", text="Akord")
        self.progression_tree.column("Index", width=50)
        self.progression_tree.column("Akord", width=150)

        self.progression_tree.grid(row=0, column=0, sticky="nsew")
        self.progression_tree.bind("<Double-1>", self.on_chord_double_click)

    def populate_midi_ports(self):
        """Naplní combobox dostupnými MIDI porty."""
        try:
            available_ports = self.music_core.get_available_midi_ports()
            self.midi_port_combo['values'] = available_ports

            if available_ports:
                current_port = self.music_core.get_current_midi_port()
                self.midi_port_var.set(current_port)
            else:
                self.midi_port_var.set("Žádné MIDI porty")

        except Exception as e:
            logger.error(f"Chyba při načítání MIDI portů: {e}")
            self.midi_port_var.set("MIDI nedostupné")

    def on_midi_port_changed(self, event=None):
        """Zpracuje změnu MIDI portu."""
        selected_port = self.midi_port_var.get()
        if selected_port and selected_port != "Žádné MIDI porty":
            success = self.music_core.set_midi_port(selected_port)
            if not success:
                messagebox.showerror("MIDI Chyba", f"Nelze nastavit MIDI port: {selected_port}")
                current_port = self.music_core.get_current_midi_port()
                self.midi_port_var.set(current_port)

    def analyze_chord(self):
        """Analyzuje zadaný akord a zobrazí výsledky."""
        chord_name = self.chord_entry.get().strip()
        if not chord_name:
            messagebox.showwarning("Vstup", "Zadejte název akordu")
            return

        try:
            analysis = self.music_core.analyze_chord(chord_name)

            if not analysis.get('success'):
                messagebox.showerror("Chyba", f"Nelze analyzovat: {analysis.get('error')}")
                return

            self.keyboard_display.draw_chord(chord_name, auto_midi=self.midi_enabled_var.get())

            self.display_progressions(analysis.get('progressions', []))

            logger.info(f"Akord {chord_name} analyzován")

        except Exception as e:
            logger.error(f"Chyba při analýze: {e}")
            messagebox.showerror("Chyba", str(e))

    def display_progressions(self, progressions: List):
        """Zobrazí nalezené progrese v TreeView."""
        for item in self.analysis_tree.get_children():
            self.analysis_tree.delete(item)

        for prog in progressions:
            chords_str = " → ".join(prog.get('chords', []))

            transposed_by = prog.get('transposed_by', 0)
            if transposed_by > 0:
                song_display = f"{prog.get('song', 'Unknown')} (+{transposed_by})"
                description = f"{prog.get('description', '')} [Trans: {prog.get('original_key', '')}]"
            else:
                song_display = prog.get('song', 'Unknown')
                description = prog.get('description', '')

            values = (
                song_display,
                chords_str,
                description,
                prog.get('genre', 'unknown')
            )
            self.analysis_tree.insert("", "end", values=values)

    def on_progression_double_click(self, event):
        """Zpracuje dvojklik na progrese a načte ji."""
        selection = self.analysis_tree.selection()
        if not selection:
            return

        item = self.analysis_tree.item(selection[0])
        progression_text = item['values'][1]
        song_name = item['values'][0]

        chords = [chord.strip() for chord in progression_text.split("→")]

        self.music_core.current_progression = chords
        self.music_core.current_index = 0
        self.music_core.progression_source = song_name

        self.update_progression_display()

        if chords:
            self.keyboard_display.draw_chord(chords[0], auto_midi=self.midi_enabled_var.get())

        logger.info(f"Načtena progrese z {song_name}: {len(chords)} akordů")

    def on_voicing_changed(self):
        """Zpracuje změnu typu voicingu."""
        self.music_core.voicing_type = self.voicing_var.get()

        current_chord = self.music_core.current_progression[
            self.music_core.current_index] if self.music_core.current_progression else None
        if current_chord:
            self.keyboard_display.draw_chord(current_chord, auto_midi=False)

    def on_midi_changed(self):
        """Zpracuje změnu MIDI nastavení."""
        self.music_core.midi_enabled = self.midi_enabled_var.get()

    def on_velocity_changed(self, value):
        """Zpracuje změnu MIDI velocity."""
        self.music_core.midi_velocity = int(float(value))

    def prev_chord(self):
        """Přejde na předchozí akord v progresi a přehraje ho."""
        if (self.music_core.current_progression and
                self.music_core.current_index > 0):
            self.music_core.current_index -= 1
            current_chord = self.music_core.current_progression[self.music_core.current_index]
            self.keyboard_display.draw_chord(current_chord, auto_midi=self.midi_enabled_var.get())
            self.update_current_chord_display(current_chord)
            logger.info(f"Předchozí akord: {current_chord}")
        else:
            logger.info("Dosažen začátek progrese")

    def next_chord(self):
        """Přejde na následující akord v progresi a přehraje ho."""
        if (self.music_core.current_progression and
                self.music_core.current_index < len(self.music_core.current_progression) - 1):
            self.music_core.current_index += 1
            current_chord = self.music_core.current_progression[self.music_core.current_index]
            self.keyboard_display.draw_chord(current_chord, auto_midi=self.midi_enabled_var.get())
            self.update_current_chord_display(current_chord)
            logger.info(f"Následující akord: {current_chord}")
        else:
            logger.info("Dosažen konec progrese")

    def on_chord_double_click(self, event):
        """Zpracuje dvojklik na akord v progresi."""
        selection = self.progression_tree.selection()
        if not selection:
            return

        item = self.progression_tree.item(selection[0])
        index = int(item['values'][0]) - 1

        self.music_core.current_index = index
        chord = self.music_core.current_progression[index]

        self.keyboard_display.draw_chord(chord, auto_midi=self.midi_enabled_var.get())
        self.update_current_chord_display(chord)

        logger.info(f"Skok na akord #{index + 1}: {chord}")

    def update_progression_display(self):
        """Aktualizuje zobrazení aktuální progrese."""
        for item in self.progression_tree.get_children():
            self.progression_tree.delete(item)

        for i, chord in enumerate(self.music_core.current_progression):
            values = (str(i + 1), chord)
            item = self.progression_tree.insert("", "end", values=values)

            if i == self.music_core.current_index:
                self.progression_tree.selection_set(item)
                self.progression_tree.see(item)

        if self.music_core.current_progression:
            current_chord = self.music_core.current_progression[self.music_core.current_index]
            self.update_current_chord_display(current_chord)

    def prev_chord_silent(self):
        """Přejde na předchozí akord v progresi bez přehrání MIDI."""
        if (self.music_core.current_progression and
                self.music_core.current_index > 0):
            self.music_core.current_index -= 1
            current_chord = self.music_core.current_progression[self.music_core.current_index]
            self.keyboard_display.draw_chord(current_chord, auto_midi=False)
            self.update_current_chord_display(current_chord)
            logger.info(f"Tichá navigace na předchozí akord: {current_chord}")
        else:
            logger.info("Dosažen začátek progrese (tichá navigace)")

    def next_chord_silent(self):
        """Přejde na následující akord v progresi bez přehrání MIDI."""
        if (self.music_core.current_progression and
                self.music_core.current_index < len(self.music_core.current_progression) - 1):
            self.music_core.current_index += 1
            current_chord = self.music_core.current_progression[self.music_core.current_index]
            self.keyboard_display.draw_chord(current_chord, auto_midi=False)
            self.update_current_chord_display(current_chord)
            logger.info(f"Tichá navigace na následující akord: {current_chord}")
        else:
            logger.info("Dosažen konec progrese (tichá navigace)")

    def update_current_chord_display(self, chord_name: str):
        """Aktualizuje zobrazení aktuálního akordu a zvýrazní ho v seznamu."""
        if self.current_chord_label:
            self.current_chord_label.config(text=chord_name)

        for item in self.progression_tree.get_children():
            item_data = self.progression_tree.item(item)
            if item_data['values'][1] == chord_name:
                self.progression_tree.selection_set(item)
                self.progression_tree.see(item)
                break

    def run(self):
        """Spustí hlavní smyčku aplikace."""
        try:
            logger.info("Piano Chord Analyzer spuštěn")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Aplikace ukončena uživatelem")
        except Exception as e:
            logger.error(f"Neočekávaná chyba: {e}", exc_info=True)
        finally:
            if self.music_core.midi_player:
                try:
                    import mido
                    msg = mido.Message('control_change', control=123, value=0)
                    self.music_core.midi_player.send(msg)
                except:
                    pass
            logger.info("Aplikace ukončena")


def main():
    """Hlavní vstupní bod aplikace."""

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('piano_analyzer.log', encoding='utf-8')
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=== Piano Chord Analyzer - Vyvážená verze ===")

    try:
        import tkinter as tk

        try:
            import mido
            logger.info("MIDI podpora: OK")
        except ImportError:
            logger.warning("MIDI podpora: NEDOSTUPNÁ")

        app = PianoChordAnalyzer()
        app.run()

    except ImportError as e:
        logger.error(f"Import chyba: {e}")
        print(f"CHYBA: {e}")
    except Exception as e:
        logger.error(f"Kritická chyba: {e}", exc_info=True)
        print(f"CHYBA: {e}")


if __name__ == '__main__':
    main()