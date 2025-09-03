# midi_playback.py
"""
Module for MIDI playback and port management.
"""

import logging
import threading
import time
from typing import List

import config

logger = logging.getLogger(__name__)


class MidiPlayback:
    """
    Handles MIDI setup, port management, and playback.
    """

    def __init__(self):
        # Input: None
        # Description: Initializes MIDI playback with default velocity and enabled state, sets up MIDI.
        # Output: None
        # Called by: PianoChordAnalyzer in gui.py
        self.midi_enabled = config.DEFAULT_MIDI_ENABLED
        self.midi_velocity = config.DEFAULT_MIDI_VELOCITY

        self.available_ports = []
        self.current_port_index = 0
        self.midi_player = self._setup_midi()

    def _setup_midi(self):
        # Input: None
        # Description: Sets up MIDI output and returns an open port if available.
        # Output: MIDI output port or None
        # Called by: __init__
        try:
            import mido
            self.available_ports = mido.get_output_names()
            if self.available_ports:
                outport = mido.open_output(self.available_ports[0])
                logger.info(f"MIDI port: {self.available_ports[0]}")
                return outport
        except ImportError:
            logger.warning("MIDI not available")
        except Exception as e:
            logger.error(f"MIDI error: {e}")
        return None

    def get_available_midi_ports(self) -> List[str]:
        # Input: None
        # Description: Returns a list of available MIDI ports.
        # Output: List of port names.
        # Called by: populate_midi_ports in gui.py
        return self.available_ports.copy()

    def set_midi_port(self, port_name: str) -> bool:
        # Input: port_name (str)
        # Description: Sets the active MIDI port.
        # Output: Boolean indicating success.
        # Called by: on_midi_port_changed in gui.py
        try:
            import mido
            if self.midi_player:
                self.midi_player.close()

            self.midi_player = mido.open_output(port_name)
            self.current_port_index = self.available_ports.index(port_name) if port_name in self.available_ports else 0
            logger.info(f"MIDI port changed to: {port_name}")
            return True
        except Exception as e:
            logger.error(f"Error changing MIDI port: {e}")
            return False

    def get_current_midi_port(self) -> str:
        # Input: None
        # Description: Returns the name of the current MIDI port.
        # Output: Port name string.
        # Called by: populate_midi_ports in gui.py
        if self.available_ports and 0 <= self.current_port_index < len(self.available_ports):
            return self.available_ports[self.current_port_index]
        return "None"

    def play_chord_midi(self, midi_notes: List[int]):
        # Input: midi_notes (List[int])
        # Description: Plays the MIDI notes of a chord in a separate thread.
        # Output: None
        # Called by: draw_chord in gui.py (via KeyboardDisplay)
        if not self.midi_enabled or not self.midi_player or not midi_notes:
            return

        def play():
            try:
                import mido
                for note in midi_notes:
                    msg = mido.Message('note_on', note=note, velocity=self.midi_velocity)
                    self.midi_player.send(msg)

                time.sleep(config.CHORD_PLAY_DURATION)

                for note in midi_notes:
                    msg = mido.Message('note_off', note=note, velocity=0)
                    self.midi_player.send(msg)
            except Exception as e:
                logger.error(f"MIDI error: {e}")

        thread = threading.Thread(target=play, daemon=True)
        thread.start()

    def close_midi(self):
        # Input: None
        # Description: Closes the MIDI player and sends all notes off.
        # Output: None
        # Called by: run in gui.py (in finally block)
        if self.midi_player:
            try:
                import mido
                msg = mido.Message('control_change', control=123, value=0)
                self.midi_player.send(msg)
                self.midi_player.close()
            except Exception:
                pass
