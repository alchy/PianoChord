# gui_components.py
"""
Core GUI components for Piano Chord Analyzer.
Contains keyboard display, controls, and common UI elements.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Tuple, Optional, Callable, Dict, Any
from chord_analysis import ChordAnalyzer, PIANO_KEYS, BLACK_KEYS
from errors import handle_error, safe_execute

logger = logging.getLogger(__name__)

# GUI Constants
WHITE_KEY_WIDTH = 18
WHITE_KEY_HEIGHT = 80
BLACK_KEY_WIDTH = 12
BLACK_KEY_HEIGHT = 50
KEYBOARD_WIDTH = 52 * WHITE_KEY_WIDTH  # 88 keys = 52 white keys
KEYBOARD_HEIGHT = WHITE_KEY_HEIGHT + 10

# Colors
WHITE_KEY_FILL = "white"
BLACK_KEY_FILL = "black"
KEY_OUTLINE = "gray"
KEYBOARD_BG = "lightgray"

# Voicing colors
VOICING_COLORS = {
    'root': '#FF6B6B',  # Red
    'smooth': '#4ECDC4',  # Teal
    'drop2': '#45B7D1'  # Blue
}


class PianoKey:
    """
    Represents a single piano key with its visual properties.
    """

    def __init__(self, key_number: int):
        """
        Initialize a piano key.

        Args:
            key_number: Key number (0-87 for 88-key piano)
        """
        self.key_number = key_number
        self.midi_note = key_number + 21  # A0 = MIDI 21

        # Calculate piano key properties
        self.relative_key = (key_number + 9) % 12  # Adjust for A0 start
        self.octave = (key_number + 9) // 12
        self.note_name = PIANO_KEYS[self.relative_key]
        self.is_black = self.note_name in BLACK_KEYS

        # Visual properties
        self.bounding_box = self._calculate_bounding_box()
        self.default_fill = BLACK_KEY_FILL if self.is_black else WHITE_KEY_FILL

    def _calculate_bounding_box(self) -> Tuple[int, int, int, int]:
        """
        Calculate the bounding box for drawing this key.

        Returns:
            Tuple of (x1, y1, x2, y2) coordinates
        """
        # Map piano keys to white key positions
        white_key_positions = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
        white_key_index = self.octave * 7 + white_key_positions[self.relative_key]

        if self.is_black:
            # Black key positioning
            x_pos = white_key_index * WHITE_KEY_WIDTH + WHITE_KEY_WIDTH - (BLACK_KEY_WIDTH // 2)
            return (x_pos, 0, x_pos + BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
        else:
            # White key positioning
            x_pos = white_key_index * WHITE_KEY_WIDTH
            return (x_pos, 0, x_pos + WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)

    def get_display_name(self) -> str:
        """Get display name for this key."""
        return f"{self.note_name}{self.octave}"


class KeyboardDisplay:
    """
    Visual piano keyboard component that can highlight keys.
    """

    def __init__(self, canvas: tk.Canvas):
        """
        Initialize keyboard display.

        Args:
            canvas: Tkinter canvas to draw on
        """
        self.canvas = canvas
        self.keys = [PianoKey(i) for i in range(88)]
        self.highlighted_keys = set()
        self.highlight_color = VOICING_COLORS['root']

        # Draw initial empty keyboard
        self.draw_empty_keyboard()
        logger.info("KeyboardDisplay initialized")

    @handle_error
    def draw_empty_keyboard(self):
        """Draw an empty keyboard with all keys in default colors."""
        self.canvas.delete("all")
        self.highlighted_keys.clear()

        # Draw white keys first
        for key in self.keys:
            if not key.is_black:
                self._draw_single_key(key, is_highlighted=False)

        # Draw black keys on top
        for key in self.keys:
            if key.is_black:
                self._draw_single_key(key, is_highlighted=False)

    def _draw_single_key(self, key: PianoKey, is_highlighted: bool):
        """
        Draw a single piano key.

        Args:
            key: PianoKey instance to draw
            is_highlighted: Whether to draw key as highlighted
        """
        x1, y1, x2, y2 = key.bounding_box

        # Choose colors
        if is_highlighted:
            fill_color = self.highlight_color
            outline_width = 2
        else:
            fill_color = key.default_fill
            outline_width = 1

        # Draw the key rectangle
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=fill_color,
            outline=KEY_OUTLINE,
            width=outline_width,
            tags=f"key_{key.key_number}"
        )

    @handle_error
    def highlight_midi_notes(self, midi_notes: List[int], voicing_type: str = 'root'):
        """
        Highlight piano keys corresponding to MIDI notes.

        Args:
            midi_notes: List of MIDI note numbers to highlight
            voicing_type: Type of voicing for color selection
        """
        # Set highlight color based on voicing type
        self.highlight_color = VOICING_COLORS.get(voicing_type, VOICING_COLORS['root'])

        # Convert MIDI notes to key numbers
        keys_to_highlight = set()
        for midi_note in midi_notes:
            if 21 <= midi_note <= 108:  # Valid piano range
                key_number = midi_note - 21
                keys_to_highlight.add(key_number)

        # Clear canvas
        self.canvas.delete("all")

        for key in self.keys:
            if not key.is_black:
                is_highlighted = key.key_number in keys_to_highlight
                self._draw_single_key(key, is_highlighted)

        for key in self.keys:
            if key.is_black:
                is_highlighted = key.key_number in keys_to_highlight
                self._draw_single_key(key, is_highlighted)
                self.highlighted_keys = keys_to_highlight

    def get_key_at_position(self, x: int, y: int) -> Optional[PianoKey]:
        """
        Get the piano key at the given canvas coordinates.

        Args:
            x: X coordinate on canvas
            y: Y coordinate on canvas

        Returns:
            PianoKey at position or None if no key found
        """
        # Check black keys first (they're on top)
        for key in self.keys:
            if key.is_black:
                x1, y1, x2, y2 = key.bounding_box
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return key

        # Check white keys
        for key in self.keys:
            if not key.is_black:
                x1, y1, x2, y2 = key.bounding_box
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return key

        return None


class ChordInputPanel:
    """
    Panel for chord input and analysis controls.
    """

    def __init__(self, parent_frame: ttk.Frame, analyze_callback: Callable[[str], None]):
        """
        Initialize chord input panel.

        Args:
            parent_frame: Parent tkinter frame
            analyze_callback: Function to call when analyzing chord
        """
        self.parent = parent_frame
        self.analyze_callback = analyze_callback

        # Create main frame
        self.frame = ttk.LabelFrame(parent_frame, text="Chord Analysis", padding=10)

        # Chord entry
        self.chord_var = tk.StringVar()
        self.chord_entry = self._create_chord_entry()

        # Analyze button
        self.analyze_button = self._create_analyze_button()

        logger.info("ChordInputPanel initialized")

    def _create_chord_entry(self) -> ttk.Entry:
        """Create chord entry widget."""
        ttk.Label(self.frame, text="Chord:").pack(side=tk.LEFT, padx=5)

        entry = ttk.Entry(self.frame, textvariable=self.chord_var, width=20)
        entry.pack(side=tk.LEFT, padx=5)
        entry.bind('<Return>', lambda e: self._on_analyze_clicked())

        return entry

    def _create_analyze_button(self) -> ttk.Button:
        """Create analyze button."""
        button = ttk.Button(self.frame, text="Analyze", command=self._on_analyze_clicked)
        button.pack(side=tk.LEFT, padx=5)
        return button

    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        chord_name = self.chord_var.get().strip()
        if chord_name:
            self.analyze_callback(chord_name)
        else:
            logger.warning("Empty chord name entered")

    def get_chord_name(self) -> str:
        """Get current chord name from entry."""
        return self.chord_var.get().strip()

    def set_chord_name(self, chord_name: str):
        """Set chord name in entry."""
        self.chord_var.set(chord_name)

    def clear_chord_name(self):
        """Clear the chord entry."""
        self.chord_var.set("")

    def focus_entry(self):
        """Focus the chord entry widget."""
        self.chord_entry.focus_set()


class VoicingControlPanel:
    """
    Panel for voicing type selection.
    """

    def __init__(self, parent_frame: ttk.Frame, voicing_changed_callback: Callable[[str], None]):
        """
        Initialize voicing control panel.

        Args:
            parent_frame: Parent tkinter frame
            voicing_changed_callback: Function to call when voicing changes
        """
        self.parent = parent_frame
        self.voicing_changed_callback = voicing_changed_callback

        # Create frame
        self.frame = ttk.LabelFrame(parent_frame, text="Voicing", padding=5)

        # Voicing selection
        self.voicing_var = tk.StringVar(value="root")
        self.voicing_buttons = self._create_voicing_buttons()

        logger.info("VoicingControlPanel initialized")

    def _create_voicing_buttons(self) -> Dict[str, ttk.Radiobutton]:
        """Create voicing selection radio buttons."""
        buttons = {}
        voicing_options = [
            ("Root", "root"),
            ("Smooth", "smooth"),
            ("Drop2", "drop2")
        ]

        for text, value in voicing_options:
            button = ttk.Radiobutton(
                self.frame,
                text=text,
                variable=self.voicing_var,
                value=value,
                command=self._on_voicing_changed
            )
            button.pack(side=tk.LEFT, padx=2)
            buttons[value] = button

        return buttons

    def _on_voicing_changed(self):
        """Handle voicing selection change."""
        voicing_type = self.voicing_var.get()
        self.voicing_changed_callback(voicing_type)
        logger.debug(f"Voicing changed to: {voicing_type}")

    def get_current_voicing(self) -> str:
        """Get currently selected voicing type."""
        return self.voicing_var.get()

    def set_voicing(self, voicing_type: str):
        """
        Set voicing type programmatically.

        Args:
            voicing_type: Voicing type to set
        """
        if voicing_type in ['root', 'smooth', 'drop2']:
            self.voicing_var.set(voicing_type)
        else:
            logger.warning(f"Invalid voicing type: {voicing_type}")


class MidiControlPanel:
    """
    Panel for MIDI playback controls.
    """

    def __init__(self, parent_frame: ttk.Frame, midi_manager):
        """
        Initialize MIDI control panel.

        Args:
            parent_frame: Parent tkinter frame
            midi_manager: MidiManager instance
        """
        self.parent = parent_frame
        self.midi_manager = midi_manager

        # Create frame
        self.frame = ttk.LabelFrame(parent_frame, text="MIDI Controls", padding=10)

        # Control variables
        self.enabled_var = tk.BooleanVar(value=True)
        self.velocity_var = tk.IntVar(value=64)
        self.port_var = tk.StringVar()

        # Create controls
        self._create_enable_checkbox()
        self._create_velocity_control()
        self._create_port_selection()

        # Initialize MIDI settings
        self._update_midi_settings()

        logger.info("MidiControlPanel initialized")

    def _create_enable_checkbox(self):
        """Create MIDI enable checkbox."""
        checkbox = ttk.Checkbutton(
            self.frame,
            text="Enable MIDI",
            variable=self.enabled_var,
            command=self._on_enabled_changed
        )
        checkbox.pack(side=tk.LEFT, padx=5)

    def _create_velocity_control(self):
        """Create MIDI velocity control."""
        ttk.Label(self.frame, text="Velocity:").pack(side=tk.LEFT, padx=5)

        velocity_scale = ttk.Scale(
            self.frame,
            from_=0, to=127,
            orient=tk.HORIZONTAL,
            variable=self.velocity_var,
            length=100,
            command=self._on_velocity_changed
        )
        velocity_scale.pack(side=tk.LEFT, padx=5)

    def _create_port_selection(self):
        """Create MIDI port selection."""
        ttk.Label(self.frame, text="MIDI Port:").pack(side=tk.LEFT, padx=(20, 5))

        self.port_combo = ttk.Combobox(
            self.frame,
            textvariable=self.port_var,
            width=25,
            state="readonly"
        )
        self.port_combo.pack(side=tk.LEFT, padx=5)
        self.port_combo.bind("<<ComboboxSelected>>", self._on_port_changed)

        # Populate ports
        self._refresh_ports()

    def _refresh_ports(self):
        """Refresh available MIDI ports."""
        ports = safe_execute(
            lambda: self.midi_manager.get_available_ports(),
            default_value=[],
            error_message="Failed to get MIDI ports"
        )

        self.port_combo['values'] = ports

        if ports:
            current_port = self.midi_manager.get_current_port()
            if current_port in ports:
                self.port_var.set(current_port)
            else:
                self.port_var.set(ports[0])
        else:
            self.port_var.set("No MIDI ports available")

    def _on_enabled_changed(self):
        """Handle MIDI enabled checkbox change."""
        enabled = self.enabled_var.get()
        self.midi_manager.configure_playback(enabled=enabled)
        logger.info(f"MIDI playback {'enabled' if enabled else 'disabled'}")

    def _on_velocity_changed(self, value):
        """Handle velocity slider change."""
        velocity = int(float(value))
        self.midi_manager.configure_playback(velocity=velocity)

    def _on_port_changed(self, event=None):
        """Handle MIDI port selection change."""
        port_name = self.port_var.get()
        if port_name and port_name != "No MIDI ports available":
            success = self.midi_manager.set_port(port_name)
            if not success:
                # Revert to current port
                current_port = self.midi_manager.get_current_port()
                self.port_var.set(current_port)

    def _update_midi_settings(self):
        """Update controls with current MIDI settings."""
        status = self.midi_manager.get_status()
        self.enabled_var.set(status['enabled'])
        self.velocity_var.set(status['default_velocity'])

    def refresh_controls(self):
        """Refresh all MIDI controls."""
        self._refresh_ports()
        self._update_midi_settings()


class StatusBar:
    """
    Status bar for displaying application status and information.
    """

    def __init__(self, parent_frame: ttk.Frame):
        """
        Initialize status bar.

        Args:
            parent_frame: Parent tkinter frame
        """
        self.parent = parent_frame

        # Create status bar frame
        self.frame = ttk.Frame(parent_frame)
        self.frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)

        # Optional: Add separator and additional status info
        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=(10, 5))

        # MIDI status
        self.midi_status_var = tk.StringVar(value="MIDI: Unknown")
        self.midi_status_label = ttk.Label(self.frame, textvariable=self.midi_status_var)
        self.midi_status_label.pack(side=tk.LEFT)

        logger.info("StatusBar initialized")

    def set_status(self, message: str):
        """
        Set main status message.

        Args:
            message: Status message to display
        """
        self.status_var.set(message)

    def set_midi_status(self, midi_available: bool, port_name: str = ""):
        """
        Set MIDI status information.

        Args:
            midi_available: Whether MIDI is available
            port_name: Name of current MIDI port
        """
        if midi_available and port_name:
            self.midi_status_var.set(f"MIDI: {port_name}")
        elif midi_available:
            self.midi_status_var.set("MIDI: Available")
        else:
            self.midi_status_var.set("MIDI: Unavailable")

    def show_temporary_message(self, message: str, duration: int = 3000):
        """
        Show a temporary message that reverts after duration.

        Args:
            message: Message to show
            duration: Duration in milliseconds
        """
        original_message = self.status_var.get()
        self.status_var.set(message)

        def revert_message():
            self.status_var.set(original_message)

        self.status_label.after(duration, revert_message)
