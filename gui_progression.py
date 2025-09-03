# gui_progression.py
"""
Progression player GUI components for Piano Chord Analyzer.
Contains components for playing through chord progressions and navigation.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Callable, Optional
from errors import handle_error

logger = logging.getLogger(__name__)


class ProgressionNavigationPanel:
    """
    Panel for navigating through chord progressions with previous/next buttons.
    """

    def __init__(self, parent_frame: ttk.Frame, navigation_callbacks: Dict[str, Callable]):
        """
        Initialize progression navigation panel.

        Args:
            parent_frame: Parent tkinter frame
            navigation_callbacks: Dictionary of callback functions:
                - 'previous': Function to call for previous chord
                - 'next': Function to call for next chord
                - 'first': Function to call to go to first chord
                - 'last': Function to call to go to last chord
        """
        self.parent = parent_frame
        self.callbacks = navigation_callbacks

        # Create navigation frame
        self.frame = ttk.Frame(parent_frame, padding=10)

        # Navigation controls
        self.previous_button = self._create_previous_button()
        self.current_chord_label = self._create_current_chord_label()
        self.next_button = self._create_next_button()
        self.position_label = self._create_position_label()

        # Additional controls
        self.first_button = self._create_first_button()
        self.last_button = self._create_last_button()

        logger.info("ProgressionNavigationPanel initialized")

    def _create_previous_button(self) -> ttk.Button:
        """Create previous chord button."""
        button = ttk.Button(self.frame, text="◀ Previous",
                            command=self.callbacks.get('previous', lambda: None))
        button.pack(side=tk.LEFT, padx=5)
        return button

    def _create_next_button(self) -> ttk.Button:
        """Create next chord button."""
        button = ttk.Button(self.frame, text="Next ▶",
                            command=self.callbacks.get('next', lambda: None))
        button.pack(side=tk.RIGHT, padx=5)
        return button

    def _create_first_button(self) -> ttk.Button:
        """Create first chord button."""
        button = ttk.Button(self.frame, text="⏮ First",
                            command=self.callbacks.get('first', lambda: None))
        button.pack(side=tk.LEFT, padx=2)
        return button

    def _create_last_button(self) -> ttk.Button:
        """Create last chord button."""
        button = ttk.Button(self.frame, text="Last ⏭",
                            command=self.callbacks.get('last', lambda: None))
        button.pack(side=tk.RIGHT, padx=2)
        return button

    def _create_current_chord_label(self) -> ttk.Label:
        """Create label for displaying current chord."""
        label = ttk.Label(self.frame, text="No progression loaded",
                          font=("Arial", 16, "bold"), anchor="center")
        label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=20)
        return label

    def _create_position_label(self) -> ttk.Label:
        """Create label for displaying position in progression."""
        label = ttk.Label(self.frame, text="", font=("Arial", 10))
        label.pack(side=tk.BOTTOM, pady=(5, 0))
        return label

    def update_current_chord(self, chord_name: str, position: int, total: int):
        """
        Update the display with current chord information.

        Args:
            chord_name: Name of current chord
            position: Current position (0-based)
            total: Total number of chords in progression
        """
        self.current_chord_label.config(text=chord_name)

        if total > 0:
            position_text = f"{position + 1} of {total}"
            self.position_label.config(text=position_text)

            # Enable/disable navigation buttons based on position
            self.previous_button.config(state="normal" if position > 0 else "disabled")
            self.first_button.config(state="normal" if position > 0 else "disabled")
            self.next_button.config(state="normal" if position < total - 1 else "disabled")
            self.last_button.config(state="normal" if position < total - 1 else "disabled")
        else:
            self.position_label.config(text="")
            # Disable all navigation buttons
            for button in [self.previous_button, self.next_button, self.first_button, self.last_button]:
                button.config(state="disabled")

    def clear_progression(self):
        """Clear progression display."""
        self.current_chord_label.config(text="No progression loaded")
        self.position_label.config(text="")
        for button in [self.previous_button, self.next_button, self.first_button, self.last_button]:
            button.config(state="disabled")

    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)


class ProgressionListWidget:
    """
    Widget for displaying and interacting with chord progression list.
    """

    def __init__(self, parent_frame: ttk.Frame, chord_click_callback: Callable[[int, str], None]):
        """
        Initialize progression list widget.

        Args:
            parent_frame: Parent tkinter frame
            chord_click_callback: Function to call when chord is clicked (receives index and chord name)
        """
        self.parent = parent_frame
        self.chord_click_callback = chord_click_callback

        # Create frame
        self.frame = ttk.Frame(parent_frame)

        # Current progression data
        self.chords = []
        self.current_index = 0
        self.annotations = []

        # Create treeview for progression display
        self.tree = self._create_progression_tree()
        self.scrollbar = self._create_scrollbar()

        logger.info("ProgressionListWidget initialized")

    def _create_progression_tree(self) -> ttk.Treeview:
        """Create treeview for progression display."""
        columns = ("Index", "Chord", "Function")
        tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=12)

        # Configure columns
        tree.heading("Index", text="#")
        tree.heading("Chord", text="Chord")
        tree.heading("Function", text="Function")

        tree.column("Index", width=50, anchor="center")
        tree.column("Chord", width=120, anchor="center")
        tree.column("Function", width=200, anchor="w")

        # Bind events
        tree.bind("<Double-1>", self._on_double_click)
        tree.bind("<Button-1>", self._on_single_click)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return tree

    def _create_scrollbar(self) -> ttk.Scrollbar:
        """Create scrollbar for treeview."""
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        return scrollbar

    def _on_double_click(self, event):
        """Handle double-click on chord in list."""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        try:
            index = int(item['values'][0]) - 1  # Convert to 0-based index
            chord_name = item['values'][1]
            self.chord_click_callback(index, chord_name)
            logger.debug(f"Double-clicked chord {index}: {chord_name}")
        except (ValueError, IndexError) as e:
            logger.warning(f"Error processing chord click: {e}")

    def _on_single_click(self, event):
        """Handle single click for selection highlight."""
        # Single click just selects, double click activates
        pass

    @handle_error
    def load_progression(self, chords: List[str], annotations: List[str] = None):
        """
        Load a chord progression into the widget.

        Args:
            chords: List of chord names
            annotations: Optional list of chord function annotations
        """
        self.chords = chords.copy()
        self.annotations = annotations.copy() if annotations else [""] * len(chords)
        self.current_index = 0

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add chord items
        for i, chord in enumerate(chords):
            annotation = self.annotations[i] if i < len(self.annotations) else ""

            values = (str(i + 1), chord, annotation)
            item_id = self.tree.insert("", "end", values=values)

            # Apply special styling for certain chord functions
            if annotation and ("V/" in annotation or "vii" in annotation):
                self.tree.item(item_id, tags=("secondary_dominant",))

        # Configure tag styles
        self.tree.tag_configure("secondary_dominant", foreground="red")
        self.tree.tag_configure("current", background="lightblue")

        # Highlight first chord if any
        if chords:
            self.highlight_current_chord(0)

        logger.info(f"Loaded progression with {len(chords)} chords")

    def highlight_current_chord(self, index: int):
        """
        Highlight the current chord in the list.

        Args:
            index: Index of chord to highlight (0-based)
        """
        if not (0 <= index < len(self.chords)):
            return

        # Clear previous highlighting
        for item in self.tree.get_children():
            self.tree.item(item, tags=())
            # Reapply special tags
            item_values = self.tree.item(item)['values']
            if len(item_values) > 2 and item_values[2]:
                annotation = item_values[2]
                if "V/" in annotation or "vii" in annotation:
                    self.tree.item(item, tags=("secondary_dominant",))

        # Highlight current chord
        children = self.tree.get_children()
        if index < len(children):
            current_item = children[index]
            current_tags = list(self.tree.item(current_item, 'tags'))
            current_tags.append("current")
            self.tree.item(current_item, tags=tuple(current_tags))

            # Scroll to show current item
            self.tree.selection_set(current_item)
            self.tree.see(current_item)

    def get_chord_at_index(self, index: int) -> Optional[str]:
        """
        Get chord name at specified index.

        Args:
            index: Index of chord (0-based)

        Returns:
            Chord name or None if index invalid
        """
        if 0 <= index < len(self.chords):
            return self.chords[index]
        return None

    def get_current_chord(self) -> Optional[str]:
        """Get currently highlighted chord."""
        return self.get_chord_at_index(self.current_index)

    def get_progression_length(self) -> int:
        """Get length of current progression."""
        return len(self.chords)

    def clear_progression(self):
        """Clear the progression list."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.chords.clear()
        self.annotations.clear()
        self.current_index = 0

    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)


class ProgressionControlPanel:
    """
    Panel with additional controls for progression playback.
    """

    def __init__(self, parent_frame: ttk.Frame, control_callbacks: Dict[str, Callable]):
        """
        Initialize progression control panel.

        Args:
            parent_frame: Parent tkinter frame
            control_callbacks: Dictionary of callback functions for various controls
        """
        self.parent = parent_frame
        self.callbacks = control_callbacks

        # Create frame
        self.frame = ttk.LabelFrame(parent_frame, text="Progression Controls", padding=10)

        # Playback controls
        self.auto_play_var = tk.BooleanVar(value=False)
        self.play_speed_var = tk.DoubleVar(value=1.0)

        # Create control widgets
        self._create_playback_controls()
        self._create_analysis_controls()

        logger.info("ProgressionControlPanel initialized")

    def _create_playback_controls(self):
        """Create playback control widgets."""
        playback_frame = ttk.Frame(self.frame)
        playback_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(playback_frame, text="Playback:").pack()

        # Auto-play checkbox
        ttk.Checkbutton(playback_frame, text="Auto-play progression",
                        variable=self.auto_play_var,
                        command=self._on_auto_play_changed).pack()

        # Speed control
        speed_frame = ttk.Frame(playback_frame)
        speed_frame.pack(pady=5)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        speed_scale = ttk.Scale(speed_frame, from_=0.5, to=3.0,
                                variable=self.play_speed_var, length=100,
                                command=self._on_speed_changed)
        speed_scale.pack(side=tk.LEFT, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.pack(side=tk.LEFT)

        # Play/Stop buttons
        button_frame = ttk.Frame(playback_frame)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="▶ Play All",
                   command=self.callbacks.get('play_all', lambda: None)).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="⏸ Stop",
                   command=self.callbacks.get('stop', lambda: None)).pack(side=tk.LEFT, padx=2)

    def _create_analysis_controls(self):
        """Create analysis control widgets."""
        analysis_frame = ttk.Frame(self.frame)
        analysis_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(analysis_frame, text="Analysis:").pack()

        # Secondary dominant button
        ttk.Button(analysis_frame, text="Play Secondary Dominant",
                   command=self.callbacks.get('play_secondary', lambda: None)).pack(pady=2)

        # Chord info button
        ttk.Button(analysis_frame, text="Chord Information",
                   command=self.callbacks.get('chord_info', lambda: None)).pack(pady=2)

        # Export button
        ttk.Button(analysis_frame, text="Export Progression",
                   command=self.callbacks.get('export', lambda: None)).pack(pady=2)

    def _on_auto_play_changed(self):
        """Handle auto-play setting change."""
        callback = self.callbacks.get('auto_play_changed')
        if callback:
            callback(self.auto_play_var.get())

    def _on_speed_changed(self, value):
        """Handle playback speed change."""
        speed = float(value)
        self.speed_label.config(text=f"{speed:.1f}x")
        callback = self.callbacks.get('speed_changed')
        if callback:
            callback(speed)

    def get_auto_play(self) -> bool:
        """Get auto-play setting."""
        return self.auto_play_var.get()

    def get_play_speed(self) -> float:
        """Get playback speed setting."""
        return self.play_speed_var.get()

    def set_auto_play(self, enabled: bool):
        """Set auto-play setting."""
        self.auto_play_var.set(enabled)

    def set_play_speed(self, speed: float):
        """Set playback speed."""
        self.play_speed_var.set(speed)
        self.speed_label.config(text=f"{speed:.1f}x")

    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)


class ProgressionInfoPanel:
    """
    Panel for displaying information about the current progression.
    """

    def __init__(self, parent_frame: ttk.Frame):
        """
        Initialize progression info panel.

        Args:
            parent_frame: Parent tkinter frame
        """
        self.parent = parent_frame

        # Create frame
        self.frame = ttk.LabelFrame(parent_frame, text="Progression Information", padding=10)

        # Info variables
        self.song_name_var = tk.StringVar(value="")
        self.genre_var = tk.StringVar(value="")
        self.key_var = tk.StringVar(value="")
        self.composer_var = tk.StringVar(value="")
        self.description_var = tk.StringVar(value="")

        # Create info display
        self._create_info_display()

        logger.info("ProgressionInfoPanel initialized")

    def _create_info_display(self):
        """Create information display widgets."""
        # Song info frame
        song_frame = ttk.Frame(self.frame)
        song_frame.pack(fill=tk.X, pady=2)

        ttk.Label(song_frame, text="Song:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(song_frame, textvariable=self.song_name_var).pack(side=tk.LEFT, padx=(5, 0))

        # Details frame
        details_frame = ttk.Frame(self.frame)
        details_frame.pack(fill=tk.X, pady=2)

        # Genre
        ttk.Label(details_frame, text="Genre:").pack(side=tk.LEFT)
        ttk.Label(details_frame, textvariable=self.genre_var).pack(side=tk.LEFT, padx=(5, 15))

        # Key
        ttk.Label(details_frame, text="Key:").pack(side=tk.LEFT)
        ttk.Label(details_frame, textvariable=self.key_var).pack(side=tk.LEFT, padx=(5, 15))

        # Composer
        composer_frame = ttk.Frame(self.frame)
        composer_frame.pack(fill=tk.X, pady=2)

        ttk.Label(composer_frame, text="Composer:").pack(side=tk.LEFT)
        ttk.Label(composer_frame, textvariable=self.composer_var).pack(side=tk.LEFT, padx=(5, 0))

        # Description
        desc_frame = ttk.Frame(self.frame)
        desc_frame.pack(fill=tk.X, pady=2)

        ttk.Label(desc_frame, text="Description:", font=("Arial", 9, "bold")).pack(anchor="w")
        desc_label = ttk.Label(desc_frame, textvariable=self.description_var,
                               wraplength=400, justify="left")
        desc_label.pack(anchor="w", padx=(10, 0))

    def update_progression_info(self, progression_data: Dict):
        """
        Update progression information display.

        Args:
            progression_data: Dictionary with progression information
        """
        self.song_name_var.set(progression_data.get('song', 'Unknown'))
        self.genre_var.set(progression_data.get('genre', 'Unknown'))
        self.key_var.set(progression_data.get('key', 'Unknown'))
        self.composer_var.set(progression_data.get('composer', 'Unknown'))
        self.description_var.set(progression_data.get('description', 'No description available'))

        # Add transposition info if applicable
        transposed_by = progression_data.get('transposed_by', 0)
        if transposed_by > 0:
            original_key = progression_data.get('original_key', 'Unknown')
            current_description = self.description_var.get()
            enhanced_description = f"{current_description}\n\nTransposed +{transposed_by} semitones from original key: {original_key}"
            self.description_var.set(enhanced_description)

    def clear_info(self):
        """Clear all progression information."""
        self.song_name_var.set("")
        self.genre_var.set("")
        self.key_var.set("")
        self.composer_var.set("")
        self.description_var.set("")

    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)
