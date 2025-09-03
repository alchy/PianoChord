# midi_manager.py
"""
MIDI management for Piano Chord Analyzer.
Handles MIDI port discovery, connection, and playback operations.
"""

import logging
import threading
import time
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from errors import MidiError, handle_error, safe_execute, log_and_suppress

logger = logging.getLogger(__name__)

# MIDI constants
DEFAULT_VELOCITY = 64
DEFAULT_DURATION = 1.0
NOTE_ON = 'note_on'
NOTE_OFF = 'note_off'
CONTROL_CHANGE = 'control_change'
ALL_NOTES_OFF = 123


class MidiPortManager:
    """
    Manages MIDI port discovery and connection.
    """

    def __init__(self):
        """Initialize MIDI port manager."""
        self.available_ports = []
        self.current_port = None
        self.current_port_name = ""
        self._refresh_ports()
        logger.info("MidiPortManager initialized")

    @handle_error
    def _refresh_ports(self):
        """
        Refresh the list of available MIDI ports.

        Raises:
            MidiError: If MIDI system is not available
        """
        try:
            import mido
            self.available_ports = mido.get_output_names()
            logger.info(f"Found {len(self.available_ports)} MIDI output ports")
        except ImportError:
            logger.warning("MIDI library (mido) not available")
            self.available_ports = []
            raise MidiError("MIDI library not installed. Install python-rtmidi and mido.")
        except Exception as e:
            logger.error(f"Error refreshing MIDI ports: {e}")
            self.available_ports = []
            raise MidiError(f"Cannot access MIDI system: {e}")

    def get_available_ports(self) -> List[str]:
        """
        Get list of available MIDI output ports.

        Returns:
            List of port names
        """
        # Refresh ports to get current state
        safe_execute(self._refresh_ports, default_value=None,
                     error_message="Failed to refresh MIDI ports")
        return self.available_ports.copy()

    @handle_error
    def open_port(self, port_name: str) -> bool:
        """
        Open a MIDI output port.

        Args:
            port_name: Name of port to open

        Returns:
            True if port opened successfully, False otherwise

        Raises:
            MidiError: If port cannot be opened
        """
        try:
            import mido

            # Close current port if open
            if self.current_port:
                self.close_port()

            # Validate port name
            if port_name not in self.available_ports:
                self._refresh_ports()  # Try refreshing in case ports changed
                if port_name not in self.available_ports:
                    available = ", ".join(self.available_ports) if self.available_ports else "None"
                    raise MidiError(f"Port '{port_name}' not available. Available ports: {available}")

            # Open the port
            self.current_port = mido.open_output(port_name)
            self.current_port_name = port_name
            logger.info(f"MIDI port opened: {port_name}")
            return True

        except ImportError:
            raise MidiError("MIDI library not available")
        except Exception as e:
            logger.error(f"Cannot open MIDI port '{port_name}': {e}")
            raise MidiError(f"Cannot open MIDI port '{port_name}': {e}")

    def close_port(self):
        """Close the current MIDI port safely."""
        if self.current_port:
            try:
                # Send all notes off before closing
                self._send_all_notes_off()
                self.current_port.close()
                logger.info(f"MIDI port closed: {self.current_port_name}")
            except Exception as e:
                logger.warning(f"Error closing MIDI port: {e}")
            finally:
                self.current_port = None
                self.current_port_name = ""

    def _send_all_notes_off(self):
        """Send all notes off control message."""
        if self.current_port:
            try:
                import mido
                msg = mido.Message(CONTROL_CHANGE, control=ALL_NOTES_OFF, value=0)
                self.current_port.send(msg)
            except Exception as e:
                logger.debug(f"Could not send all notes off: {e}")

    def get_current_port_name(self) -> str:
        """
        Get name of currently open port.

        Returns:
            Current port name or empty string if no port open
        """
        return self.current_port_name

    def is_port_open(self) -> bool:
        """
        Check if a MIDI port is currently open.

        Returns:
            True if port is open, False otherwise
        """
        return self.current_port is not None

    @contextmanager
    def port_context(self, port_name: str):
        """
        Context manager for temporarily opening a MIDI port.

        Args:
            port_name: Name of port to open

        Yields:
            The opened port

        Raises:
            MidiError: If port cannot be opened
        """
        original_port = self.current_port_name
        try:
            self.open_port(port_name)
            yield self.current_port
        finally:
            self.close_port()
            if original_port:
                safe_execute(lambda: self.open_port(original_port),
                             error_message=f"Could not restore original port {original_port}")


class MidiPlaybackEngine:
    """
    Handles MIDI note playback and timing.
    """

    def __init__(self, port_manager: MidiPortManager):
        """
        Initialize MIDI playback engine.

        Args:
            port_manager: MidiPortManager instance
        """
        self.port_manager = port_manager
        self.is_enabled = True
        self.default_velocity = DEFAULT_VELOCITY
        self.default_duration = DEFAULT_DURATION
        self._active_threads = []
        logger.info("MidiPlaybackEngine initialized")

    def set_enabled(self, enabled: bool):
        """
        Enable or disable MIDI playback.

        Args:
            enabled: True to enable playback, False to disable
        """
        self.is_enabled = enabled
        logger.info(f"MIDI playback {'enabled' if enabled else 'disabled'}")

    def set_default_velocity(self, velocity: int):
        """
        Set default MIDI velocity.

        Args:
            velocity: MIDI velocity (0-127)
        """
        if 0 <= velocity <= 127:
            self.default_velocity = velocity
            logger.debug(f"Default MIDI velocity set to {velocity}")
        else:
            logger.warning(f"Invalid MIDI velocity {velocity}, must be 0-127")

    def set_default_duration(self, duration: float):
        """
        Set default note duration.

        Args:
            duration: Duration in seconds
        """
        if duration > 0:
            self.default_duration = duration
            logger.debug(f"Default note duration set to {duration}s")
        else:
            logger.warning(f"Invalid duration {duration}, must be positive")

    @handle_error
    def play_notes_sync(self, midi_notes: List[int], velocity: Optional[int] = None, duration: Optional[float] = None):
        """
        Play MIDI notes synchronously (blocking).

        Args:
            midi_notes: List of MIDI note numbers
            velocity: MIDI velocity (defaults to default_velocity)
            duration: Note duration in seconds (defaults to default_duration)

        Raises:
            MidiError: If playback fails
        """
        if not self.is_enabled:
            logger.debug("MIDI playback disabled, skipping")
            return

        if not midi_notes:
            logger.debug("No MIDI notes to play")
            return

        if not self.port_manager.is_port_open():
            raise MidiError("No MIDI port is open")

        velocity = velocity or self.default_velocity
        duration = duration or self.default_duration

        try:
            import mido
            port = self.port_manager.current_port

            # Send note on messages
            for note in midi_notes:
                if 0 <= note <= 127:
                    msg = mido.Message(NOTE_ON, note=note, velocity=velocity)
                    port.send(msg)
                else:
                    logger.warning(f"Invalid MIDI note {note}, skipping")

            # Wait for duration
            time.sleep(duration)

            # Send note off messages
            for note in midi_notes:
                if 0 <= note <= 127:
                    msg = mido.Message(NOTE_OFF, note=note, velocity=0)
                    port.send(msg)

            logger.debug(f"Played {len(midi_notes)} MIDI notes")

        except ImportError:
            raise MidiError("MIDI library not available")
        except Exception as e:
            logger.error(f"Error playing MIDI notes: {e}")
            raise MidiError(f"MIDI playback failed: {e}")

    def play_notes_async(self, midi_notes: List[int], velocity: Optional[int] = None, duration: Optional[float] = None):
        """
        Play MIDI notes asynchronously (non-blocking).

        Args:
            midi_notes: List of MIDI note numbers
            velocity: MIDI velocity (defaults to default_velocity)
            duration: Note duration in seconds (defaults to default_duration)
        """
        if not self.is_enabled or not midi_notes:
            return

        def play_thread():
            try:
                self.play_notes_sync(midi_notes, velocity, duration)
            except MidiError as e:
                logger.warning(f"Async MIDI playback failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in MIDI playback thread: {e}")

        # Clean up finished threads
        self._active_threads = [t for t in self._active_threads if t.is_alive()]

        # Start new playback thread
        thread = threading.Thread(target=play_thread, daemon=True)
        thread.start()
        self._active_threads.append(thread)

    def stop_all_playback(self):
        """Stop all active MIDI playback and send all notes off."""
        try:
            # Send all notes off
            if self.port_manager.is_port_open():
                self.port_manager._send_all_notes_off()

            # Wait for threads to finish (with timeout)
            for thread in self._active_threads:
                if thread.is_alive():
                    thread.join(timeout=0.5)

            self._active_threads.clear()
            logger.info("All MIDI playback stopped")

        except Exception as e:
            logger.warning(f"Error stopping MIDI playback: {e}")


class MidiManager:
    """
    High-level MIDI management combining port management and playback.
    """

    def __init__(self):
        """Initialize MIDI manager with port manager and playback engine."""
        self.port_manager = MidiPortManager()
        self.playback_engine = MidiPlaybackEngine(self.port_manager)
        self._auto_connect_first_port()
        logger.info("MidiManager initialized")

    def _auto_connect_first_port(self):
        """Automatically connect to the first available MIDI port."""
        available_ports = self.port_manager.get_available_ports()
        if available_ports:
            try:
                self.port_manager.open_port(available_ports[0])
                logger.info(f"Auto-connected to first MIDI port: {available_ports[0]}")
            except MidiError as e:
                logger.warning(f"Could not auto-connect to MIDI port: {e}")

    def get_available_ports(self) -> List[str]:
        """Get list of available MIDI ports."""
        return self.port_manager.get_available_ports()

    def set_port(self, port_name: str) -> bool:
        """
        Set the active MIDI port.

        Args:
            port_name: Name of port to set

        Returns:
            True if port was set successfully, False otherwise
        """
        try:
            self.port_manager.open_port(port_name)
            return True
        except MidiError as e:
            logger.warning(f"Could not set MIDI port: {e}")
            return False

    def get_current_port(self) -> str:
        """Get name of current MIDI port."""
        return self.port_manager.get_current_port_name()

    def is_available(self) -> bool:
        """Check if MIDI system is available."""
        try:
            import mido
            return True
        except ImportError:
            return False

    def play_chord(self, midi_notes: List[int], velocity: int = None, duration: float = None, async_play: bool = True):
        """
        Play a chord (multiple notes simultaneously).

        Args:
            midi_notes: List of MIDI note numbers
            velocity: MIDI velocity (optional)
            duration: Note duration in seconds (optional)
            async_play: Whether to play asynchronously (default: True)
        """
        if async_play:
            self.playback_engine.play_notes_async(midi_notes, velocity, duration)
        else:
            try:
                self.playback_engine.play_notes_sync(midi_notes, velocity, duration)
            except MidiError as e:
                logger.warning(f"Chord playback failed: {e}")

    def play_sequence(self, chord_sequence: List[List[int]], velocity: int = None, duration: float = None):
        """
        Play a sequence of chords with timing.

        Args:
            chord_sequence: List of chord (each chord is list of MIDI notes)
            velocity: MIDI velocity for all chords
            duration: Duration for each chord
        """

        def play_sequence_thread():
            chord_duration = duration or self.playback_engine.default_duration
            for chord in chord_sequence:
                try:
                    self.playback_engine.play_notes_sync(chord, velocity, chord_duration)
                except MidiError as e:
                    logger.warning(f"Failed to play chord in sequence: {e}")
                    continue

        thread = threading.Thread(target=play_sequence_thread, daemon=True)
        thread.start()

    def configure_playback(self, enabled: bool = None, velocity: int = None, duration: float = None):
        """
        Configure playback settings.

        Args:
            enabled: Enable/disable playback (optional)
            velocity: Default velocity (optional)
            duration: Default duration (optional)
        """
        if enabled is not None:
            self.playback_engine.set_enabled(enabled)
        if velocity is not None:
            self.playback_engine.set_default_velocity(velocity)
        if duration is not None:
            self.playback_engine.set_default_duration(duration)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current MIDI system status.

        Returns:
            Dictionary with MIDI status information
        """
        return {
            'available': self.is_available(),
            'enabled': self.playback_engine.is_enabled,
            'current_port': self.get_current_port(),
            'available_ports': self.get_available_ports(),
            'default_velocity': self.playback_engine.default_velocity,
            'default_duration': self.playback_engine.default_duration,
            'active_threads': len(self.playback_engine._active_threads)
        }

    def cleanup(self):
        """Clean up MIDI resources."""
        try:
            self.playback_engine.stop_all_playback()
            self.port_manager.close_port()
            logger.info("MIDI manager cleaned up")
        except Exception as e:
            logger.warning(f"Error during MIDI cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
