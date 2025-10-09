# midi_playback.py
"""
Module for MIDI playback and port management.
"""

import logging
import threading
import time
from typing import List, Callable, Optional

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

        # Output ports (pro přehrávání aplikací)
        self.available_output_ports = []
        self.current_output_port_index = 0
        self.midi_player = self._setup_midi_output()

        # Input ports (pro příjem z MIDI klaviatury)
        self.available_input_ports = []
        self.current_input_port_index = 0
        self.midi_input = None
        self.midi_input_thread = None
        self.input_callback: Optional[Callable] = None
        self.pressed_notes = set()  # Buffer aktuálně stisknutých kláves
        self._setup_midi_input()

    def _setup_midi_output(self):
        # Input: None
        # Description: Sets up MIDI output and returns an open port if available.
        # Output: MIDI output port or None
        # Called by: __init__
        try:
            import mido
            self.available_output_ports = mido.get_output_names()
            if self.available_output_ports:
                outport = mido.open_output(self.available_output_ports[0])
                logger.info(f"MIDI Output port: {self.available_output_ports[0]}")
                return outport
        except ImportError:
            logger.warning("MIDI not available")
        except Exception as e:
            logger.error(f"MIDI output error: {e}")
        return None

    def _setup_midi_input(self):
        # Input: None
        # Description: Detekuje dostupné MIDI input porty (bez otevření).
        # Output: None
        # Called by: __init__
        try:
            import mido
            self.available_input_ports = mido.get_input_names()
            if self.available_input_ports:
                logger.info(f"Found {len(self.available_input_ports)} MIDI input port(s)")
            else:
                logger.warning("No MIDI input ports available")
        except ImportError:
            logger.warning("MIDI not available")
        except Exception as e:
            logger.error(f"MIDI input detection error: {e}")

    def get_available_midi_output_ports(self) -> List[str]:
        # Input: None
        # Description: Returns a list of available MIDI output ports.
        # Output: List of port names.
        # Called by: populate_midi_ports in gui.py
        return self.available_output_ports.copy()

    def get_available_midi_input_ports(self) -> List[str]:
        # Input: None
        # Description: Returns a list of available MIDI input ports.
        # Output: List of port names.
        # Called by: populate_midi_ports in gui.py
        return self.available_input_ports.copy()

    def set_midi_output_port(self, port_name: str) -> bool:
        # Input: port_name (str)
        # Description: Sets the active MIDI output port.
        # Output: Boolean indicating success.
        # Called by: on_midi_port_changed in gui.py
        try:
            import mido
            if self.midi_player:
                self.midi_player.close()

            self.midi_player = mido.open_output(port_name)
            self.current_output_port_index = self.available_output_ports.index(port_name) if port_name in self.available_output_ports else 0
            logger.info(f"MIDI output port changed to: {port_name}")
            return True
        except Exception as e:
            logger.error(f"Error changing MIDI output port: {e}")
            return False

    def set_midi_input_port(self, port_name: str, callback: Optional[Callable] = None) -> bool:
        # Input: port_name (str), callback (Optional[Callable])
        # Description: Sets the active MIDI input port and starts listening.
        # Output: Boolean indicating success.
        # Called by: on_midi_input_port_changed in gui.py
        try:
            import mido

            # Zavřeme starý input port pokud existuje
            if self.midi_input:
                self.midi_input.close()
                self.midi_input = None

            # Otevřeme nový input port s callbackem
            self.midi_input = mido.open_input(port_name)
            self.current_input_port_index = self.available_input_ports.index(port_name) if port_name in self.available_input_ports else 0
            self.input_callback = callback

            # Spustíme listening thread
            self._start_input_listening()

            logger.info(f"MIDI input port changed to: {port_name}")
            return True
        except Exception as e:
            logger.error(f"Error changing MIDI input port: {e}")
            return False

    def get_current_midi_output_port(self) -> str:
        # Input: None
        # Description: Returns the name of the current MIDI output port.
        # Output: Port name string.
        # Called by: populate_midi_ports in gui.py
        if self.available_output_ports and 0 <= self.current_output_port_index < len(self.available_output_ports):
            return self.available_output_ports[self.current_output_port_index]
        return "None"

    def get_current_midi_input_port(self) -> str:
        # Input: None
        # Description: Returns the name of the current MIDI input port.
        # Output: Port name string.
        # Called by: populate_midi_ports in gui.py
        if self.available_input_ports and 0 <= self.current_input_port_index < len(self.available_input_ports):
            return self.available_input_ports[self.current_input_port_index]
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

    def _start_input_listening(self):
        # Input: None
        # Description: Spustí thread pro listening MIDI input zpráv.
        # Output: None
        # Called by: set_midi_input_port
        if self.midi_input_thread and self.midi_input_thread.is_alive():
            return  # Thread již běží

        def listen():
            try:
                while self.midi_input:
                    for message in self.midi_input.iter_pending():
                        self._handle_midi_input_message(message)
                    time.sleep(0.001)  # Krátká pauza pro snížení CPU
            except Exception as e:
                logger.error(f"MIDI input listening error: {e}")

        self.midi_input_thread = threading.Thread(target=listen, daemon=True)
        self.midi_input_thread.start()

    def _handle_midi_input_message(self, message):
        # Input: message (mido.Message)
        # Description: Zpracuje příchozí MIDI zprávu a volá callback.
        # Output: None
        # Called by: _start_input_listening
        try:
            if message.type == 'note_on' and message.velocity > 0:
                # Přehraj notu zpět (instant feedback)
                self._play_note_feedback(message.note, message.velocity)

                # Přidej do bufferu
                self.pressed_notes.add(message.note)

                # Zavolej callback pokud existuje
                if self.input_callback:
                    self.input_callback('note_on', message.note, self.pressed_notes.copy())

            elif message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
                # Odstraň z bufferu
                self.pressed_notes.discard(message.note)

                # Zavolaj callback pokud existuje
                if self.input_callback:
                    self.input_callback('note_off', message.note, self.pressed_notes.copy())

        except Exception as e:
            logger.error(f"Error handling MIDI input message: {e}")

    def _play_note_feedback(self, note: int, velocity: int):
        # Input: note (int), velocity (int)
        # Description: Přehraje jednu notu jako okamžitou zpětnou vazbu.
        # Output: None
        # Called by: _handle_midi_input_message
        if not self.midi_enabled or not self.midi_player:
            return

        try:
            import mido
            msg = mido.Message('note_on', note=note, velocity=velocity)
            self.midi_player.send(msg)
        except Exception as e:
            logger.error(f"Error playing note feedback: {e}")

    def stop_note_feedback(self, note: int):
        # Input: note (int)
        # Description: Zastaví přehrávání noty (pošle note_off).
        # Output: None
        # Called by: external (např. Training Mode)
        if not self.midi_enabled or not self.midi_player:
            return

        try:
            import mido
            msg = mido.Message('note_off', note=note, velocity=0)
            self.midi_player.send(msg)
        except Exception as e:
            logger.error(f"Error stopping note feedback: {e}")

    def get_pressed_notes(self) -> set:
        # Input: None
        # Description: Vrací aktuálně stisknuté noty.
        # Output: Set of MIDI note numbers.
        # Called by: external (např. Training Mode)
        return self.pressed_notes.copy()

    def clear_pressed_notes(self):
        # Input: None
        # Description: Vyčistí buffer stisknutých not.
        # Output: None
        # Called by: external (např. Training Mode)
        self.pressed_notes.clear()

    def is_midi_input_available(self) -> bool:
        # Input: None
        # Description: Kontroluje, zda je dostupný alespoň jeden MIDI input port.
        # Output: Boolean
        # Called by: gui.py (pro enable/disable Training button)
        return len(self.available_input_ports) > 0

    def close_midi(self):
        # Input: None
        # Description: Closes the MIDI player and input, sends all notes off.
        # Output: None
        # Called by: run in gui.py (in finally block)
        # Zavřeme input port
        if self.midi_input:
            try:
                self.midi_input.close()
                self.midi_input = None
            except Exception:
                pass

        # Zavřeme output port
        if self.midi_player:
            try:
                import mido
                msg = mido.Message('control_change', control=123, value=0)
                self.midi_player.send(msg)
                self.midi_player.close()
            except Exception:
                pass
