# gui.py
"""
Module for GUI components, including keyboard display and application interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Tuple

import config
from music_analytics import MusicAnalytics
from midi_playback import MidiPlayback

logger = logging.getLogger(__name__)


class PianoKey:
    """
    Represents a single key on the piano keyboard.
    """

    def __init__(self, key_nr: int):
        # Input: key_nr (int) - Key number (0-87 for 88 keys)
        # Description: Initializes a piano key with its description, type, and bounding box.
        # Output: None
        # Called by: KeyboardDisplay
        self.key_nr = key_nr
        self.relative_key_nr = (key_nr + 9) % 12
        self.octave = (key_nr + 9) // 12
        self.key_desc = config.PIANO_KEYS[self.relative_key_nr]
        self.is_sharp = self.key_desc in config.BLACK_KEYS
        self.fill = config.BLACK_KEY_FILL if self.is_sharp else config.WHITE_KEY_FILL
        self.bbox = self._calculate_bbox()

    def _calculate_bbox(self) -> Tuple[int, int, int, int]:
        # Input: None
        # Description: Calculates the bounding box for drawing the key.
        # Output: Tuple (x1, y1, x2, y2)
        # Called by: __init__
        white_key_map = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
        white_key_index = self.octave * 7 + white_key_map[self.relative_key_nr]
        x_pos = white_key_index * config.WHITE_KEY_WIDTH

        if self.is_sharp:
            x_pos += config.WHITE_KEY_WIDTH - (config.BLACK_KEY_WIDTH / 2)
            width = config.BLACK_KEY_WIDTH
            height = config.BLACK_KEY_HEIGHT
        else:
            width = config.WHITE_KEY_WIDTH
            height = config.WHITE_KEY_HEIGHT

        return (x_pos, 0, x_pos + width, height)


class KeyboardDisplay:
    """
    Handles drawing the keyboard and chords.
    """

    def __init__(self, canvas: tk.Canvas, music_analytics: MusicAnalytics):
        # Input: canvas (tk.Canvas), music_analytics (MusicAnalytics)
        # Description: Initializes the keyboard display with keys.
        # Output: None
        # Called by: create_keyboard_section in PianoChordAnalyzer
        self.canvas = canvas
        self.music_analytics = music_analytics
        self.keys = [PianoKey(i) for i in range(88)]
        self.highlighted_keys_ids = []

    def _draw_empty_keyboard(self):
        # Input: None
        # Description: Draws an empty keyboard.
        # Output: None
        # Called by: create_keyboard_section in PianoChordAnalyzer
        self.canvas.delete("all")
        self.highlighted_keys_ids.clear()

        for key in self.keys:
            if not key.is_sharp:
                self._draw_key(key, False, config.WHITE_KEY_FILL)

        for key in self.keys:
            if key.is_sharp:
                self._draw_key(key, False, config.BLACK_KEY_FILL)

    def draw_chord(self, chord_name: str, midi_playback: MidiPlayback, auto_midi: bool = True):
        # Input: chord_name (str), midi_playback (MidiPlayback), auto_midi (bool, optional)
        # Description: Draws the chord on the keyboard and optionally plays MIDI.
        # Output: List of MIDI notes
        # Called by: analyze_chord, on_progression_double_click, prev_chord, next_chord, etc. in PianoChordAnalyzer
        midi_notes = self.music_analytics.get_voicing(chord_name)

        if midi_notes:
            self.music_analytics.previous_chord_midi = midi_notes.copy()

            self._draw_midi_notes(midi_notes)

            if auto_midi and midi_playback.midi_enabled:
                midi_playback.play_chord_midi(midi_notes)

        return midi_notes

    def _draw_midi_notes(self, midi_notes: List[int]):
        # Input: midi_notes (List[int])
        # Description: Draws the specified MIDI notes on the keyboard.
        # Output: None
        # Called by: draw_chord
        self.canvas.delete("all")
        self.highlighted_keys_ids.clear()

        keys_to_highlight = []
        for midi_note in midi_notes:
            key_number = midi_note - 21
            if 0 <= key_number < 88:
                keys_to_highlight.append(key_number)

        color = config.VOICING_COLORS.get(self.music_analytics.voicing_type, "red")

        for key in self.keys:
            if not key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

        for key in self.keys:
            if key.is_sharp:
                self._draw_key(key, key.key_nr in keys_to_highlight, color)

    def _draw_key(self, key: PianoKey, is_highlighted: bool, highlight_color: str):
        # Input: key (PianoKey), is_highlighted (bool), highlight_color (str)
        # Description: Draws a single key.
        # Output: None
        # Called by: _draw_empty_keyboard, _draw_midi_notes
        fill = highlight_color if is_highlighted else key.fill
        outline = config.KEY_OUTLINE_COLOR
        width = config.DEFAULT_HIGHLIGHT_WIDTH if is_highlighted else config.DEFAULT_KEY_WIDTH

        rect = self.canvas.create_rectangle(
            key.bbox, fill=fill, outline=outline, width=width, tags="key"
        )

        if is_highlighted:
            self.highlighted_keys_ids.append(rect)


class PianoChordAnalyzer:
    """
    Main application for analyzing and playing piano chords.
    """

    def __init__(self, music_analytics: MusicAnalytics, midi_playback: MidiPlayback):
        # Input: music_analytics (MusicAnalytics), midi_playback (MidiPlayback)
        # Description: Initializes the GUI application.
        # Output: None
        # Called by: main in main.py
        self.root = tk.Tk()
        self.music_analytics = music_analytics
        self.midi_playback = midi_playback

        self.chord_entry = None
        self.keyboard_display = None
        self.analysis_tree = None
        self.progression_tree = None
        self.current_chord_label = None

        self.setup_gui()
        logger.info("Application initialized")

    def setup_gui(self):
        # Input: None
        # Description: Sets up the main GUI of the application.
        # Output: None
        # Called by: __init__
        self.root.title(config.APP_TITLE)
        self.root.geometry(config.APP_GEOMETRY)
        self.root.minsize(*config.APP_MINSIZE)

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
        # Input: event (tk.Event)
        # Description: Handles the Enter key press based on context.
        # Output: None
        # Called by: Key binding in setup_gui
        if self.root.focus_get() == self.chord_entry:
            self.analyze_chord()
        elif self.music_analytics.current_progression:
            current_chord = self.music_analytics.current_progression[self.music_analytics.current_index]
            self.keyboard_display.draw_chord(current_chord, self.midi_playback, auto_midi=self.midi_enabled_var.get())
            self.update_current_chord_display(current_chord)
            logger.info(f"Played and drawn current chord from progression: {current_chord}")
        else:
            self.analyze_chord()

    def create_keyboard_section(self):
        # Input: None
        # Description: Creates the keyboard section in the GUI.
        # Output: None
        # Called by: setup_gui
        keyboard_frame = ttk.Frame(self.root, padding=10)
        keyboard_frame.grid(row=0, column=0, sticky="ew")
        keyboard_frame.columnconfigure(0, weight=1)

        canvas = tk.Canvas(keyboard_frame, width=config.KEYBOARD_WIDTH, height=config.KEYBOARD_HEIGHT, bg=config.KEYBOARD_BG_COLOR)
        canvas.grid(row=0, column=0, pady=10)

        self.keyboard_display = KeyboardDisplay(canvas, self.music_analytics)
        self.keyboard_display._draw_empty_keyboard()

    def create_controls_section(self):
        # Input: None
        # Description: Creates the controls section with input, voicing, and MIDI options.
        # Output: None
        # Called by: setup_gui
        controls_frame = ttk.Frame(self.root, padding=10)
        controls_frame.grid(row=1, column=0, sticky="ew")

        input_frame = ttk.LabelFrame(controls_frame, text="Chord Analysis", padding=10)
        input_frame.pack(fill="x", pady=5)

        ttk.Label(input_frame, text="Chord:").pack(side=tk.LEFT, padx=5)

        self.chord_entry = ttk.Entry(input_frame, width=20)
        self.chord_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(input_frame, text="Analyze", command=self.analyze_chord).pack(side=tk.LEFT, padx=5)

        voicing_frame = ttk.LabelFrame(input_frame, text="Voicing", padding=5)
        voicing_frame.pack(side=tk.LEFT, padx=10)

        self.voicing_var = tk.StringVar(value="root")
        for text, value in [("Root", "root"), ("Smooth", "smooth"), ("Drop2", "drop2")]:
            ttk.Radiobutton(voicing_frame, text=text, variable=self.voicing_var,
                            value=value, command=self.on_voicing_changed).pack(side=tk.LEFT, padx=2)

        midi_frame = ttk.LabelFrame(controls_frame, text="MIDI", padding=10)
        midi_frame.pack(fill="x", pady=5)

        self.midi_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(midi_frame, text="Play MIDI", variable=self.midi_enabled_var,
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
        # Input: None
        # Description: Creates the output section with tabs for analysis and progression.
        # Output: None
        # Called by: setup_gui
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=2, column=0, sticky="nsew", pady=10)

        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="Chord Analysis")
        self.create_analysis_tab(analysis_frame)

        progression_frame = ttk.Frame(notebook)
        notebook.add(progression_frame, text="Progression Player")
        self.create_progression_tab(progression_frame)

    def create_analysis_tab(self, parent):
        # Input: parent (ttk.Frame)
        # Description: Creates the analysis tab with Treeview for progressions.
        # Output: None
        # Called by: create_output_section
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        columns = ("Song", "Progression", "Annotations", "Description", "Genre")
        self.analysis_tree = ttk.Treeview(parent, columns=columns, show="headings")

        for col in columns:
            self.analysis_tree.heading(col, text=col)
            self.analysis_tree.column(col, width=config.TREEVIEW_COLUMN_WIDTHS["analysis"])

        self.analysis_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.analysis_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.analysis_tree.configure(yscrollcommand=scrollbar.set)

        self.analysis_tree.bind("<Double-1>", self.on_progression_double_click)

    def create_progression_tab(self, parent):
        # Input: parent (ttk.Frame)
        # Description: Creates the progression tab with navigation and Treeview.
        # Output: None
        # Called by: create_output_section
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        nav_frame = ttk.Frame(parent, padding=10)
        nav_frame.grid(row=0, column=0, sticky="ew")

        ttk.Button(nav_frame, text="<< Previous", command=self.prev_chord).pack(side=tk.LEFT, padx=5)

        self.current_chord_label = ttk.Label(nav_frame, text=config.CURRENT_CHORD_DEFAULT_TEXT,
                                             font=config.CURRENT_CHORD_FONT)
        self.current_chord_label.pack(side=tk.LEFT, expand=True, fill="x", padx=20)

        ttk.Button(nav_frame, text="Next >>", command=self.next_chord).pack(side=tk.LEFT, padx=5)

        ttk.Button(nav_frame, text="Play Sec Dom", command=self.play_secondary_dominant).pack(side=tk.LEFT, padx=5)

        prog_frame = ttk.Frame(parent)
        prog_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        prog_frame.rowconfigure(0, weight=1)
        prog_frame.columnconfigure(0, weight=1)

        columns = ("Index", "Chord", "Annotation")
        self.progression_tree = ttk.Treeview(prog_frame, columns=columns, show="headings")
        self.progression_tree.heading("Index", text="#")
        self.progression_tree.heading("Chord", text="Chord")
        self.progression_tree.heading("Annotation", text="Function")
        self.progression_tree.column("Index", width=config.TREEVIEW_COLUMN_WIDTHS["progression_index"])
        self.progression_tree.column("Chord", width=config.TREEVIEW_COLUMN_WIDTHS["progression_chord"])
        self.progression_tree.column("Annotation", width=150)

        self.progression_tree.grid(row=0, column=0, sticky="nsew")
        self.progression_tree.bind("<Double-1>", self.on_chord_double_click)

    def populate_midi_ports(self):
        # Input: None
        # Description: Populates the MIDI ports combobox.
        # Output: None
        # Called by: create_controls_section
        try:
            available_ports = self.midi_playback.get_available_midi_ports()
            self.midi_port_combo['values'] = available_ports

            if available_ports:
                current_port = self.midi_playback.get_current_midi_port()
                self.midi_port_var.set(current_port)
            else:
                self.midi_port_var.set("No MIDI ports")

        except Exception as e:
            logger.error(f"Error loading MIDI ports: {e}")
            self.midi_port_var.set("MIDI unavailable")

    def on_midi_port_changed(self, event=None):
        # Input: event (tk.Event, optional)
        # Description: Handles MIDI port change.
        # Output: None
        # Called by: Combobox binding in create_controls_section
        selected_port = self.midi_port_var.get()
        if selected_port and selected_port != "No MIDI ports":
            success = self.midi_playback.set_midi_port(selected_port)
            if not success:
                messagebox.showerror("MIDI Error", f"Cannot set MIDI port: {selected_port}")
                current_port = self.midi_playback.get_current_midi_port()
                self.midi_port_var.set(current_port)

    def analyze_chord(self):
        # Input: None
        # Description: Analyzes the entered chord and displays results.
        # Output: None
        # Called by: Button in create_controls_section, _handle_enter_key
        chord_name = self.chord_entry.get().strip()
        if not chord_name:
            messagebox.showwarning("Input", "Enter a chord name")
            return

        try:
            analysis = self.music_analytics.analyze_chord(chord_name)

            if not analysis.get('success'):
                messagebox.showerror("Error", f"Cannot analyze: {analysis.get('error')}")
                return

            self.keyboard_display.draw_chord(chord_name, self.midi_playback, auto_midi=self.midi_enabled_var.get())

            self.display_progressions(analysis.get('progressions', []))

            logger.info(f"Chord {chord_name} analyzed")

        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            messagebox.showerror("Error", str(e))

    def display_progressions(self, progressions: List):
        # Input: progressions (List[Dict])
        # Description: Displays found progressions in the analysis Treeview.
        # Output: None
        # Called by: analyze_chord
        for item in self.analysis_tree.get_children():
            self.analysis_tree.delete(item)

        for prog in progressions:
            chords_str = " → ".join(prog.get('chords', []))
            annotations_str = " → ".join(prog.get('annotations', [""] * len(prog['chords'])))

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
                annotations_str,
                description,
                prog.get('genre', 'unknown')
            )
            self.analysis_tree.insert("", "end", values=values)

    def on_progression_double_click(self, event):
        # Input: event (tk.Event)
        # Description: Handles double-click on a progression to load it.
        # Output: None
        # Called by: Treeview binding in create_analysis_tab
        selection = self.analysis_tree.selection()
        if not selection:
            return

        item = self.analysis_tree.item(selection[0])
        progression_text = item['values'][1]
        song_name = item['values'][0]
        annotations_text = item['values'][2]

        chords = [chord.strip() for chord in progression_text.split("→")]
        annotations = [anno.strip() for anno in annotations_text.split("→")]

        # Fallback to detect if annotations not present
        if all(a == "" for a in annotations):
            original_key = [p for p in progressions if p['song'] == song_name][0].get('original_key', 'C')
            annotations = self.music_analytics.detect_secondary_dominants(chords, original_key)

        self.music_analytics.current_progression = chords
        self.music_analytics.current_annotations = annotations
        self.music_analytics.current_index = 0
        self.music_analytics.progression_source = song_name

        self.update_progression_display()

        if chords:
            self.keyboard_display.draw_chord(chords[0], self.midi_playback, auto_midi=self.midi_enabled_var.get())

        logger.info(f"Loaded progression from {song_name}: {len(chords)} chords")

    def on_voicing_changed(self):
        # Input: None
        # Description: Handles change in voicing type.
        # Output: None
        # Called by: Radiobutton in create_controls_section
        self.music_analytics.voicing_type = self.voicing_var.get()

        current_chord = self.music_analytics.current_progression[
            self.music_analytics.current_index] if self.music_analytics.current_progression else None
        if current_chord:
            self.keyboard_display.draw_chord(current_chord, self.midi_playback, auto_midi=False)

    def on_midi_changed(self):
        # Input: None
        # Description: Handles change in MIDI enabled state.
        # Output: None
        # Called by: Checkbutton in create_controls_section
        self.midi_playback.midi_enabled = self.midi_enabled_var.get()

    def on_velocity_changed(self, value):
        # Input: value (str or float) - Slider value
        # Description: Handles change in MIDI velocity.
        # Output: None
        # Called by: Scale in create_controls_section
        self.midi_playback.midi_velocity = int(float(value))

    def prev_chord(self):
        # Input: None
        # Description: Moves to the previous chord in the progression and plays it.
        # Output: None
        # Called by: Button in create_progression_tab, key binding
        if (self.music_analytics.current_progression and
                self.music_analytics.current_index > 0):
            self.music_analytics.current_index -= 1
            current_chord = self.music_analytics.current_progression[self.music_analytics.current_index]
            self.keyboard_display.draw_chord(current_chord, self.midi_playback, auto_midi=self.midi_enabled_var.get())
            self.update_current_chord_display(current_chord)
            logger.info(f"Previous chord: {current_chord}")
        else:
            logger.info("Reached start of progression")

    def next_chord(self):
        # Input: None
        # Description: Moves to the next chord in the progression and plays it.
        # Output: None
        # Called by: Button in create_progression_tab, key binding
        if (self.music_analytics.current_progression and
                self.music_analytics.current_index < len(self.music_analytics.current_progression) - 1):
            self.music_analytics.current_index += 1
            current_chord = self.music_analytics.current_progression[self.music_analytics.current_index]
            self.keyboard_display.draw_chord(current_chord, self.midi_playback, auto_midi=self.midi_enabled_var.get())
            self.update_current_chord_display(current_chord)
            logger.info(f"Next chord: {current_chord}")
        else:
            logger.info("Reached end of progression")

    def on_chord_double_click(self, event):
        # Input: event (tk.Event)
        # Description: Handles double-click on a chord in the progression.
        # Output: None
        # Called by: Treeview binding in create_progression_tab
        selection = self.progression_tree.selection()
        if not selection:
            return

        item = self.progression_tree.item(selection[0])
        index = int(item['values'][0]) - 1

        self.music_analytics.current_index = index
        chord = self.music_analytics.current_progression[index]

        self.keyboard_display.draw_chord(chord, self.midi_playback, auto_midi=self.midi_enabled_var.get())
        self.update_current_chord_display(chord)

        logger.info(f"Jump to chord #{index + 1}: {chord}")

    def update_progression_display(self):
        # Input: None
        # Description: Updates the display of the current progression.
        # Output: None
        # Called by: on_progression_double_click, prev_chord, next_chord, etc.
        for item in self.progression_tree.get_children():
            self.progression_tree.delete(item)

        for i, chord in enumerate(self.music_analytics.current_progression):
            annotation = self.music_analytics.current_annotations[i] if i < len(self.music_analytics.current_annotations) else ""
            values = (str(i + 1), chord, annotation)
            item = self.progression_tree.insert("", "end", values=values)

            if "V/" in annotation:
                self.progression_tree.item(item, tags=("secondary",))
            self.progression_tree.tag_configure("secondary", foreground="red")

            if i == self.music_analytics.current_index:
                self.progression_tree.selection_set(item)
                self.progression_tree.see(item)

        if self.music_analytics.current_progression:
            current_chord = self.music_analytics.current_progression[self.music_analytics.current_index]
            self.update_current_chord_display(current_chord)

    def prev_chord_silent(self):
        # Input: None
        # Description: Moves to the previous chord without playing MIDI.
        # Output: None
        # Called by: Key binding
        if (self.music_analytics.current_progression and
                self.music_analytics.current_index > 0):
            self.music_analytics.current_index -= 1
            current_chord = self.music_analytics.current_progression[self.music_analytics.current_index]
            self.keyboard_display.draw_chord(current_chord, self.midi_playback, auto_midi=False)
            self.update_current_chord_display(current_chord)
            logger.info(f"Silent navigation to previous chord: {current_chord}")
        else:
            logger.info("Reached start of progression (silent)")

    def next_chord_silent(self):
        # Input: None
        # Description: Moves to the next chord without playing MIDI.
        # Output: None
        # Called by: Key binding
        if (self.music_analytics.current_progression and
                self.music_analytics.current_index < len(self.music_analytics.current_progression) - 1):
            self.music_analytics.current_index += 1
            current_chord = self.music_analytics.current_progression[self.music_analytics.current_index]
            self.keyboard_display.draw_chord(current_chord, self.midi_playback, auto_midi=False)
            self.update_current_chord_display(current_chord)
            logger.info(f"Silent navigation to next chord: {current_chord}")
        else:
            logger.info("Reached end of progression (silent)")

    def update_current_chord_display(self, chord_name: str):
        # Input: chord_name (str)
        # Description: Updates the current chord label and highlights it in the list.
        # Output: None
        # Called by: prev_chord, next_chord, on_chord_double_click, etc.
        if self.current_chord_label:
            self.current_chord_label.config(text=chord_name)

        for item in self.progression_tree.get_children():
            item_data = self.progression_tree.item(item)
            if item_data['values'][1] == chord_name:
                self.progression_tree.selection_set(item)
                self.progression_tree.see(item)
                break

    def play_secondary_dominant(self):
        # Input: None
        # Description: Generates and plays the secondary dominant for the current chord.
        # Output: None
        # Called by: Button in create_progression_tab
        if not self.music_analytics.current_progression:
            return
        current_chord = self.music_analytics.current_progression[self.music_analytics.current_index]
        sec_dom = self.music_analytics.generate_secondary_dominant(current_chord)
        midi_notes = self.music_analytics.get_voicing(sec_dom)
        self.midi_playback.play_chord_midi(midi_notes)  # Play sec dom
        # Optional: time.sleep(1); play current chord
        logger.info(f"Played secondary dominant: {sec_dom} for {current_chord}")

    def run(self):
        # Input: None
        # Description: Runs the main application loop.
        # Output: None
        # Called by: main in main.py
        try:
            logger.info("Piano Chord Analyzer started")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.midi_playback.close_midi()
            logger.info("Application ended")
