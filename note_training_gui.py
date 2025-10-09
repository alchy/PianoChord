# note_training_gui.py
"""
Module for Note Training Mode GUI window.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional

import config
from midi_playback import MidiPlayback
from note_training import NoteTrainingSession
from music_analytics import MusicAnalytics
from gui import KeyboardDisplay

logger = logging.getLogger(__name__)


class NoteTrainingWindow:
    """
    Samostatné okno pro Note Training Mode - single note recognition training.
    """

    def __init__(self, parent_root: tk.Tk, music_analytics: MusicAnalytics,
                 midi_playback: MidiPlayback):
        # Input: parent_root (tk.Tk), music_analytics, midi_playback
        # Description: Initializes Note Training Mode window.
        # Output: None
        # Called by: start_note_training_mode in gui.py
        self.parent_root = parent_root
        self.music_analytics = music_analytics
        self.midi_playback = midi_playback

        # Training session
        self.session = NoteTrainingSession()

        # GUI state
        self.current_status = "Waiting for input..."
        self.show_hint = False

        # Create window
        self.window = tk.Toplevel(parent_root)
        self.window.title("Training Mode - Note Recognition")
        self.window.geometry("1000x700")
        self.window.minsize(800, 600)

        # Keyboard display
        self.keyboard_display: Optional[KeyboardDisplay] = None

        # Labels
        self.target_note_label: Optional[tk.Label] = None
        self.status_label: Optional[tk.Label] = None
        self.score_label: Optional[tk.Label] = None
        self.level_label: Optional[tk.Label] = None

        # Setup GUI
        self._setup_gui()

        # Register MIDI input callback
        self.midi_playback.input_callback = self._on_midi_input

        # Start first challenge
        self._start_new_challenge()

        logger.info("Note Training Window opened")

    def _setup_gui(self):
        """
        Nastaví GUI podobně jako Chord Training.
        """
        # Main frame
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Keyboard section
        keyboard_frame = ttk.LabelFrame(main_frame, text="Piano Keyboard", padding=10)
        keyboard_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        canvas = tk.Canvas(keyboard_frame, width=config.KEYBOARD_WIDTH,
                          height=config.KEYBOARD_HEIGHT, bg=config.KEYBOARD_BG_COLOR)
        canvas.pack()

        self.keyboard_display = KeyboardDisplay(canvas, self.music_analytics)
        self.keyboard_display._draw_empty_keyboard()

        # Target note display (velké zobrazení)
        target_frame = ttk.Frame(main_frame)
        target_frame.pack(fill=tk.X, pady=10)

        ttk.Label(target_frame, text="Target Note:",
                 font=("Arial", 14)).pack(side=tk.LEFT, padx=10)

        self.target_note_label = tk.Label(target_frame, text="---",
                                          font=("Arial", 32, "bold"),
                                          foreground="blue")
        self.target_note_label.pack(side=tk.LEFT, padx=10)

        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)

        ttk.Label(status_frame, text="Status:",
                 font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(status_frame, text="Play the note!",
                                     font=("Arial", 14),
                                     foreground="black")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Score and level display
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)

        self.score_label = ttk.Label(info_frame, text="Score: 0/0 (0%)",
                                     font=("Arial", 12))
        self.score_label.pack(side=tk.LEFT, padx=10)

        self.level_label = ttk.Label(info_frame,
                                     text=f"Current Level: {self.session.get_current_level_name()}",
                                     font=("Arial", 12))
        self.level_label.pack(side=tk.LEFT, padx=20)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Next Note",
                  command=self._next_note).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Skip",
                  command=self._skip_note).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Show Answer",
                  command=self._show_answer).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Exit",
                  command=self._exit_training).pack(side=tk.LEFT, padx=20)

        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self._exit_training)

    def _on_midi_input(self, event_type: str, note: int, pressed_notes: set):
        """
        Callback pro MIDI input zprávy.

        Args:
            event_type: 'note_on' nebo 'note_off'
            note: MIDI note number
            pressed_notes: Set aktuálně stisknutých not
        """
        if event_type == 'note_on':
            # Aktualizuj vizualizaci
            self._draw_played_note(note)

            # Zkontroluj notu
            is_correct, message = self.session.check_note(note)

            if is_correct:
                # Správně!
                self._display_status(message, "green")
                self.session.record_attempt(correct=True)
                self._update_score()

                # Automaticky přejdi na další notu po 1 sekundě
                self.window.after(1000, self._next_note)
            else:
                # Nesprávně
                if self.session.attempt_count == 1:
                    self._display_status(message, "orange")
                elif self.session.attempt_count >= 2:
                    self._display_status(message, "red")
                    self._show_answer()

        elif event_type == 'note_off':
            # Vyčisti vizualizaci
            if not pressed_notes:  # Pokud nejsou žádné stisknuté noty
                self._draw_empty_or_hint()

    def _draw_played_note(self, midi_note: int):
        """
        Vykreslí zahranou notu (zeleně).
        """
        self.keyboard_display._draw_midi_notes([midi_note])

        # Překresli s barvou zelená (playing)
        self.keyboard_display.canvas.delete("all")
        self.keyboard_display.highlighted_keys_ids.clear()

        key_number = midi_note - 21
        keys_to_highlight = [key_number] if 0 <= key_number < 88 else []

        for key in self.keyboard_display.keys:
            if not key.is_sharp:
                color = "green" if key.key_nr in keys_to_highlight else key.fill
                self.keyboard_display._draw_key(key, key.key_nr in keys_to_highlight, color)

        for key in self.keyboard_display.keys:
            if key.is_sharp:
                color = "green" if key.key_nr in keys_to_highlight else key.fill
                self.keyboard_display._draw_key(key, key.key_nr in keys_to_highlight, color)

    def _draw_empty_or_hint(self):
        """
        Vykreslí prázdnou klaviaturu nebo nápovědu (pokud je aktivní).
        """
        if self.show_hint and self.session.target_midi_note:
            # Zobraz nápovědu (žlutě)
            target_note = self.session.target_midi_note
            self.keyboard_display._draw_midi_notes([target_note])

            # Překresli s žlutou barvou
            self.keyboard_display.canvas.delete("all")
            self.keyboard_display.highlighted_keys_ids.clear()

            key_number = target_note - 21
            keys_to_highlight = [key_number] if 0 <= key_number < 88 else []

            for key in self.keyboard_display.keys:
                if not key.is_sharp:
                    color = "yellow" if key.key_nr in keys_to_highlight else key.fill
                    self.keyboard_display._draw_key(key, key.key_nr in keys_to_highlight, color)

            for key in self.keyboard_display.keys:
                if key.is_sharp:
                    color = "yellow" if key.key_nr in keys_to_highlight else key.fill
                    self.keyboard_display._draw_key(key, key.key_nr in keys_to_highlight, color)
        else:
            # Prázdná klaviatura
            self.keyboard_display._draw_empty_keyboard()

    def _start_new_challenge(self):
        """
        Zahájí novou challenge s novou cílovou notou.
        """
        target_note, target_midi = self.session.start_new_challenge()
        self.show_hint = False

        # Aktualizuj GUI
        self.target_note_label.config(text=target_note)
        self._display_status("Play the note!", "black")
        self._update_score()

        # Vyčisti buffer stisknutých not
        self.midi_playback.clear_pressed_notes()

        # Vyčisti klaviaturu
        self.keyboard_display._draw_empty_keyboard()

    def _next_note(self):
        """
        Přejde na další notu.
        """
        self._start_new_challenge()

    def _skip_note(self):
        """
        Přeskočí aktuální notu.
        """
        self.session.skip_current_note()
        self._update_score()
        self._next_note()

    def _show_answer(self):
        """
        Zobrazí nápovědu (žlutá klávesa).
        """
        self.show_hint = True
        self._display_status("Showing answer...", "orange")
        self._draw_empty_or_hint()

    def _display_status(self, message: str, color: str):
        """
        Zobrazí status zprávu s danou barvou.
        """
        self.status_label.config(text=message, foreground=color)

    def _update_score(self):
        """
        Aktualizuje zobrazení skóre a levelu.
        """
        stats = self.session.get_statistics()
        score_text = f"Score: {stats['correct']}/{stats['total_notes']} ({stats['percentage']:.0f}%)"
        self.score_label.config(text=score_text)

        level_text = f"Current Level: {stats['level_name']}"
        self.level_label.config(text=level_text)

    def _exit_training(self):
        """
        Ukončí Note Training Mode a zobrazí statistiky.
        """
        # Odstraň callback
        self.midi_playback.input_callback = None

        # Zobraz statistiky
        stats = self.session.get_statistics()
        duration_minutes = stats['duration'] / 60

        stats_message = (
            f"Note Training Session Complete!\n\n"
            f"Total Notes: {stats['total_notes']}\n"
            f"Correct: {stats['correct']}\n"
            f"Accuracy: {stats['percentage']:.1f}%\n"
            f"Final Level: {stats['level_name']}\n"
            f"Duration: {duration_minutes:.1f} minutes"
        )

        messagebox.showinfo("Training Statistics", stats_message)

        # Zavři okno
        self.window.destroy()
        logger.info("Note Training Window closed")
