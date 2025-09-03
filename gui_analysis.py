# gui_analysis.py
"""
Analysis results GUI components for Piano Chord Analyzer.
Contains components for displaying chord analysis results and progression search.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Callable, Optional
from errors import handle_error, safe_execute

logger = logging.getLogger(__name__)


class ProgressionResultsTree:
    """
    TreeView component for displaying chord progression search results.
    """

    def __init__(self, parent_frame: ttk.Frame, double_click_callback: Callable[[Dict], None]):
        """
        Initialize progression results tree.

        Args:
            parent_frame: Parent tkinter frame
            double_click_callback: Function to call on double-click (receives progression data)
        """
        self.parent = parent_frame
        self.double_click_callback = double_click_callback

        # Create frame with scrollbars
        self.frame = ttk.Frame(parent_frame)

        # Define columns
        self.columns = ("Song", "Progression", "Description", "Genre", "Key", "Composer")
        self.column_widths = {
            "Song": 180,
            "Progression": 250,
            "Description": 200,
            "Genre": 120,
            "Key": 50,
            "Composer": 150
        }

        # Create treeview
        self.tree = self._create_treeview()
        self.scrollbar = self._create_scrollbar()

        # Store progression data for retrieval
        self.progression_data = {}

        logger.info("ProgressionResultsTree initialized")

    def _create_treeview(self) -> ttk.Treeview:
        """Create and configure the treeview."""
        tree = ttk.Treeview(self.frame, columns=self.columns, show="headings", height=15)

        # Configure columns
        for col in self.columns:
            tree.heading(col, text=col, command=lambda c=col: self._sort_by_column(c))
            tree.column(col, width=self.column_widths.get(col, 100), anchor="w")

        # Bind events
        tree.bind("<Double-1>", self._on_double_click)
        tree.bind("<Button-3>", self._on_right_click)  # Right-click context menu

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return tree

    def _create_scrollbar(self) -> ttk.Scrollbar:
        """Create vertical scrollbar for treeview."""
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        return scrollbar

    def _sort_by_column(self, column: str):
        """
        Sort treeview by column.

        Args:
            column: Column name to sort by
        """
        try:
            items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
            items.sort()

            for index, (_, item) in enumerate(items):
                self.tree.move(item, '', index)

            logger.debug(f"Sorted by column: {column}")
        except Exception as e:
            logger.warning(f"Error sorting by column {column}: {e}")

    def _on_double_click(self, event):
        """Handle double-click on progression."""
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]
        if item_id in self.progression_data:
            progression_data = self.progression_data[item_id]
            self.double_click_callback(progression_data)
            logger.debug(f"Double-clicked progression: {progression_data.get('song', 'Unknown')}")

    def _on_right_click(self, event):
        """Handle right-click for context menu."""
        # TODO: Implement context menu with options like:
        # - Copy progression
        # - Show chord details
        # - Find similar progressions
        pass

    @handle_error
    def display_progressions(self, progressions: List[Dict]):
        """
        Display list of progressions in the tree.

        Args:
            progressions: List of progression dictionaries
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.progression_data.clear()

        # Add new items
        for i, progression in enumerate(progressions):
            try:
                # Format progression display
                chords_str = " → ".join(progression.get('chords', []))

                # Handle transposed songs
                song_name = progression.get('song', 'Unknown')
                transposed_by = progression.get('transposed_by', 0)
                if transposed_by > 0:
                    song_display = f"{song_name} (+{transposed_by})"
                    description = f"{progression.get('description', '')} [From: {progression.get('original_key', '')}]"
                else:
                    song_display = song_name
                    description = progression.get('description', '')

                # Create tree item
                values = (
                    song_display,
                    chords_str,
                    description,
                    progression.get('genre', 'Unknown'),
                    progression.get('key', 'C'),
                    progression.get('composer', 'Unknown')
                )

                item_id = self.tree.insert("", "end", values=values)
                self.progression_data[item_id] = progression

                # Color code transposed items
                if transposed_by > 0:
                    self.tree.item(item_id, tags=('transposed',))

            except Exception as e:
                logger.warning(f"Error adding progression {i}: {e}")

        # Configure tags for styling
        self.tree.tag_configure('transposed', foreground='blue')

        logger.info(f"Displayed {len(progressions)} progressions")

    def get_selected_progression(self) -> Optional[Dict]:
        """
        Get currently selected progression data.

        Returns:
            Progression dictionary or None if no selection
        """
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            return self.progression_data.get(item_id)
        return None

    def clear_results(self):
        """Clear all results from the tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.progression_data.clear()

    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)


class ChordAnalysisPanel:
    """
    Panel for displaying detailed chord analysis information.
    """

    def __init__(self, parent_frame: ttk.Frame):
        """
        Initialize chord analysis panel.

        Args:
            parent_frame: Parent tkinter frame
        """
        self.parent = parent_frame

        # Create frame
        self.frame = ttk.LabelFrame(parent_frame, text="Chord Analysis", padding=10)

        # Analysis display
        self.analysis_text = self._create_analysis_text()

        logger.info("ChordAnalysisPanel initialized")

    def _create_analysis_text(self) -> tk.Text:
        """Create text widget for analysis display."""
        # Create frame for text and scrollbar
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Create text widget
        text_widget = tk.Text(text_frame, height=8, width=50, wrap=tk.WORD, state=tk.DISABLED)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        text_widget.configure(yscrollcommand=scrollbar.set)

        return text_widget

    @handle_error
    def display_chord_analysis(self, chord_name: str, analysis_data: Dict):
        """
        Display detailed chord analysis.

        Args:
            chord_name: Name of analyzed chord
            analysis_data: Analysis results dictionary
        """
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)

        try:
            # Basic chord information
            base_note = analysis_data.get('base_note', 'Unknown')
            chord_type = analysis_data.get('chord_type', '')

            analysis_lines = [
                f"Chord: {chord_name}",
                f"Root Note: {base_note}",
                f"Chord Type: {chord_type if chord_type else 'Major'}",
                f"",
            ]

            # MIDI information
            midi_notes = analysis_data.get('midi_notes', [])
            if midi_notes:
                note_names = self._midi_to_note_names(midi_notes)
                analysis_lines.extend([
                    f"MIDI Notes: {', '.join(map(str, midi_notes))}",
                    f"Note Names: {', '.join(note_names)}",
                    f"Range: {max(midi_notes) - min(midi_notes)} semitones",
                    f""
                ])

            # Key context information if available
            if 'key' in analysis_data:
                key = analysis_data['key']
                roman_numeral = analysis_data.get('roman_numeral', 'Unknown')
                is_diatonic = analysis_data.get('is_diatonic', False)
                is_dominant = analysis_data.get('is_dominant', False)

                analysis_lines.extend([
                    f"In key of {key}:",
                    f"  Roman Numeral: {roman_numeral}",
                    f"  Diatonic: {'Yes' if is_diatonic else 'No'}",
                    f"  Dominant Function: {'Yes' if is_dominant else 'No'}",
                    f""
                ])

            # Progressions found
            progressions = analysis_data.get('progressions', [])
            if progressions:
                analysis_lines.extend([
                    f"Found in {len(progressions)} progressions:",
                    ""
                ])

                # Show first few progressions as examples
                for i, prog in enumerate(progressions[:3]):
                    chords = " → ".join(prog.get('chords', []))
                    song = prog.get('song', 'Unknown')
                    analysis_lines.append(f"  {song}: {chords}")

                if len(progressions) > 3:
                    analysis_lines.append(f"  ... and {len(progressions) - 3} more")

            # Display the analysis
            analysis_text = "\n".join(analysis_lines)
            self.analysis_text.insert(tk.END, analysis_text)

        except Exception as e:
            error_text = f"Error displaying analysis: {e}"
            self.analysis_text.insert(tk.END, error_text)
            logger.error(error_text)

        self.analysis_text.config(state=tk.DISABLED)

    def _midi_to_note_names(self, midi_notes: List[int]) -> List[str]:
        """
        Convert MIDI notes to note names with octaves.

        Args:
            midi_notes: List of MIDI note numbers

        Returns:
            List of note names (e.g., ['C4', 'E4', 'G4'])
        """
        note_names = []
        for midi_note in midi_notes:
            if 0 <= midi_note <= 127:
                octave = (midi_note // 12) - 1
                note_index = midi_note % 12
                note_name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][note_index]
                note_names.append(f"{note_name}{octave}")
            else:
                note_names.append(f"Invalid({midi_note})")
        return note_names

    def clear_analysis(self):
        """Clear the analysis display."""
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.config(state=tk.DISABLED)

    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)


class SearchFiltersPanel:
    """
    Panel for filtering search results by genre, composer, key, etc.
    """

    def __init__(self, parent_frame: ttk.Frame, filter_changed_callback: Callable[[Dict], None]):
        """
        Initialize search filters panel.

        Args:
            parent_frame: Parent tkinter frame
            filter_changed_callback: Function to call when filters change
        """
        self.parent = parent_frame
        self.filter_changed_callback = filter_changed_callback

        # Create frame
        self.frame = ttk.LabelFrame(parent_frame, text="Search Filters", padding=10)

        # Filter variables
        self.genre_var = tk.StringVar(value="All")
        self.composer_var = tk.StringVar(value="All")
        self.key_var = tk.StringVar(value="All")
        self.include_transpositions_var = tk.BooleanVar(value=True)

        # Create filter controls
        self._create_filter_controls()

        logger.info("SearchFiltersPanel initialized")

    def _create_filter_controls(self):
        """Create filter control widgets."""
        # Genre filter
        genre_frame = ttk.Frame(self.frame)
        genre_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(genre_frame, text="Genre:").pack()
        self.genre_combo = ttk.Combobox(genre_frame, textvariable=self.genre_var,
                                        width=15, state="readonly")
        self.genre_combo.pack()
        self.genre_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Composer filter
        composer_frame = ttk.Frame(self.frame)
        composer_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(composer_frame, text="Composer:").pack()
        self.composer_combo = ttk.Combobox(composer_frame, textvariable=self.composer_var,
                                           width=15, state="readonly")
        self.composer_combo.pack()
        self.composer_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Key filter
        key_frame = ttk.Frame(self.frame)
        key_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(key_frame, text="Key:").pack()
        self.key_combo = ttk.Combobox(key_frame, textvariable=self.key_var,
                                      width=10, state="readonly")
        self.key_combo.pack()
        self.key_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Include transpositions checkbox
        transpose_frame = ttk.Frame(self.frame)
        transpose_frame.pack(side=tk.LEFT, padx=20)
        ttk.Checkbutton(transpose_frame, text="Include\nTranspositions",
                        variable=self.include_transpositions_var,
                        command=self._on_filter_changed).pack()

    def _on_filter_changed(self, event=None):
        """Handle filter change."""
        filters = self.get_current_filters()
        self.filter_changed_callback(filters)

    def get_current_filters(self) -> Dict:
        """
        Get current filter settings.

        Returns:
            Dictionary with current filter values
        """
        return {
            'genre': self.genre_var.get(),
            'composer': self.composer_var.get(),
            'key': self.key_var.get(),
            'include_transpositions': self.include_transpositions_var.get()
        }

    def set_available_options(self, genres: List[str], composers: List[str], keys: List[str]):
        """
        Set available options for filters.

        Args:
            genres: List of available genres
            composers: List of available composers
            keys: List of available keys
        """
        # Update genre options
        genre_options = ["All"] + sorted(genres)
        self.genre_combo['values'] = genre_options

        # Update composer options
        composer_options = ["All"] + sorted(composers)
        self.composer_combo['values'] = composer_options

        # Update key options
        key_options = ["All"] + sorted(keys)
        self.key_combo['values'] = key_options

    def reset_filters(self):
        """Reset all filters to default values."""
        self.genre_var.set("All")
        self.composer_var.set("All")
        self.key_var.set("All")
        self.include_transpositions_var.set(True)
        self._on_filter_changed()

    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)
