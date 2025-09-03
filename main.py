# piano_chord_analyzer.py
"""
Piano Chord Analyzer - Main Application
Refactored version with clean separation of concerns and proper error handling.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Import configuration
from app_config import (
    APP_TITLE, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE,
    setup_logging, validate_config, get_app_info
)

# Import our modular components
from errors import PianoAnalyzerError, ChordParsingError, MidiError, DatabaseError, handle_error
from chord_analysis import ChordAnalyzer
from transposition_engine import TranspositionEngine
from voicing_engine import VoicingEngine
from database_manager import ProgressionDatabase
from midi_manager import MidiManager

# Import GUI components
from gui_components import (KeyboardDisplay, ChordInputPanel, VoicingControlPanel,
                            MidiControlPanel, StatusBar)
from gui_analysis import ProgressionResultsTree, ChordAnalysisPanel, SearchFiltersPanel
from gui_progression import (ProgressionNavigationPanel, ProgressionListWidget,
                             ProgressionControlPanel, ProgressionInfoPanel)

logger = logging.getLogger(__name__)


class PianoChordAnalyzer:
    """
    Main application class for Piano Chord Analyzer.
    Coordinates all components and manages application state.
    """

    def __init__(self):
        """Initialize the Piano Chord Analyzer application."""
        logger.info("Initializing Piano Chord Analyzer")

        # Initialize core components
        self._initialize_core_components()

        # Initialize GUI
        self._initialize_gui()

        # Initialize application state
        self._initialize_state()

        # Setup keyboard bindings
        self._setup_keyboard_bindings()

        logger.info("Piano Chord Analyzer initialized successfully")

    def _initialize_core_components(self):
        """Initialize core business logic components."""
        try:
            # Core analysis components
            self.chord_analyzer = ChordAnalyzer()
            self.transposition_engine = TranspositionEngine(self.chord_analyzer)
            self.voicing_engine = VoicingEngine(self.chord_analyzer)

            # Database
            database_path = "database.json"
            self.database = ProgressionDatabase(database_path, self.chord_analyzer, self.transposition_engine)

            # MIDI system
            self.midi_manager = MidiManager()

            logger.info("Core components initialized")

        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}")
            messagebox.showerror("Initialization Error",
                               f"Failed to initialize core components:\n{e}")
            sys.exit(1)

    def _initialize_gui(self):
        """Initialize GUI components and layout."""
        # Main window
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.rowconfigure(2, weight=0)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)  # Main content area

        # Create main layout
        self._create_keyboard_section()
        self._create_main_content()
        self._create_status_bar()

        logger.info("GUI initialized")

    def _create_keyboard_section(self):
        """Create the piano keyboard display section."""
        keyboard_frame = ttk.Frame(self.root, padding=10)
        keyboard_frame.grid(row=0, column=0, sticky="ew")
        keyboard_frame.columnconfigure(0, weight=1)

        # Canvas for keyboard
        keyboard_width = 52 * 18  # 52 white keys * 18 pixels each
        canvas = tk.Canvas(keyboard_frame, width=keyboard_width, height=100, bg="lightgray")
        canvas.grid(row=0, column=0, pady=10)

        # Initialize keyboard display
        self.keyboard_display = KeyboardDisplay(canvas)

        # Control panels below keyboard
        controls_frame = ttk.Frame(keyboard_frame)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=10)

        # Chord input panel
        self.chord_input_panel = ChordInputPanel(controls_frame, self._on_chord_analyze)
        self.chord_input_panel.frame.pack(side=tk.LEFT, fill="x", expand=True)

        # Voicing control panel
        self.voicing_control_panel = VoicingControlPanel(controls_frame, self._on_voicing_changed)
        self.voicing_control_panel.frame.pack(side=tk.LEFT, padx=10)

        # MIDI control panel
        self.midi_control_panel = MidiControlPanel(controls_frame, self.midi_manager)
        self.midi_control_panel.frame.pack(side=tk.LEFT, padx=10)

    def _create_main_content(self):
        """Create main content area with tabbed interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Analysis tab
        self._create_analysis_tab()

        # Progression player tab
        self._create_progression_tab()

    def _create_analysis_tab(self):
        """Create chord analysis tab."""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Chord Analysis")

        # Configure grid
        analysis_frame.columnconfigure(0, weight=2)
        analysis_frame.columnconfigure(1, weight=1)
        analysis_frame.rowconfigure(1, weight=1)

        # Search filters
        self.search_filters_panel = SearchFiltersPanel(analysis_frame, self._on_filters_changed)
        self.search_filters_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Results tree (left side)
        results_frame = ttk.LabelFrame(analysis_frame, text="Search Results", padding=5)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 2), pady=5)

        self.progression_results_tree = ProgressionResultsTree(results_frame, self._on_progression_selected)
        self.progression_results_tree.pack(fill="both", expand=True)

        # Analysis panel (right side)
        self.chord_analysis_panel = ChordAnalysisPanel(analysis_frame)
        self.chord_analysis_panel.grid(row=1, column=1, sticky="nsew", padx=(2, 5), pady=5)

    def _create_progression_tab(self):
        """Create progression player tab."""
        progression_frame = ttk.Frame(self.notebook)
        self.notebook.add(progression_frame, text="Progression Player")

        # Configure grid
        progression_frame.columnconfigure(0, weight=2)
        progression_frame.columnconfigure(1, weight=1)
        progression_frame.rowconfigure(1, weight=1)

        # Navigation panel (top)
        navigation_callbacks = {
            'previous': self._go_to_previous_chord,
            'next': self._go_to_next_chord,
            'first': self._go_to_first_chord,
            'last': self._go_to_last_chord
        }
        self.progression_navigation = ProgressionNavigationPanel(progression_frame, navigation_callbacks)
        self.progression_navigation.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Progression list (left side)
        list_frame = ttk.LabelFrame(progression_frame, text="Chord Progression", padding=5)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 2), pady=5)

        self.progression_list_widget = ProgressionListWidget(list_frame, self._on_chord_clicked)
        self.progression_list_widget.pack(fill="both", expand=True)

        # Info and controls (right side)
        right_frame = ttk.Frame(progression_frame)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(2, 5), pady=5)
        right_frame.rowconfigure(1, weight=1)

        # Progression info
        self.progression_info_panel = ProgressionInfoPanel(right_frame)
        self.progression_info_panel.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Control panel
        control_callbacks = {
            'play_all': self._play_all_chords,
            'stop': self._stop_playback,
            'play_secondary': self._play_secondary_dominant,
            'chord_info': self._show_chord_info,
            'export': self._export_progression,
            'auto_play_changed': self._on_auto_play_changed,
            'speed_changed': self._on_speed_changed
        }
        self.progression_control_panel = ProgressionControlPanel(right_frame, control_callbacks)
        self.progression_control_panel.grid(row=1, column=0, sticky="new", pady=5)

    def _create_status_bar(self):
        """Create status bar at bottom of window."""
        self.status_bar = StatusBar(self.root)

        # Update MIDI status
        midi_status = self.midi_manager.get_status()
        self.status_bar.set_midi_status(midi_status['available'], midi_status['current_port'])

    def _initialize_state(self):
        """Initialize application state variables."""
        # Current progression state
        self.current_progression = []
        self.current_progression_data = {}
        self.current_chord_index = 0

        # Last analysis results for caching
        self.last_chord_analysis = {}
        self.last_search_results = []

        # Playback state
        self.is_auto_playing = False
        self.playback_speed = 1.0

        # Initialize search filters
        self._update_search_filters()

    def _setup_keyboard_bindings(self):
        """Setup keyboard shortcuts."""
        self.root.bind('<Return>', self._on_enter_pressed)
        self.root.bind('<Control-q>', lambda e: self.root.quit())

        # Progression navigation
        self.root.bind('<Left>', lambda e: self._go_to_previous_chord())
        self.root.bind('<Right>', lambda e: self._go_to_next_chord())
        self.root.bind('<Home>', lambda e: self._go_to_first_chord())
        self.root.bind('<End>', lambda e: self._go_to_last_chord())

        # Silent navigation (Shift + arrow keys)
        self.root.bind('<Shift-Left>', lambda e: self._go_to_previous_chord(play_midi=False))
        self.root.bind('<Shift-Right>', lambda e: self._go_to_next_chord(play_midi=False))

        # Focus management
        self.root.bind('<Control-f>', lambda e: self.chord_input_panel.focus_entry())

    # Event handlers for chord analysis
    @handle_error
    def _on_chord_analyze(self, chord_name: str):
        """Handle chord analysis request."""
        if not chord_name:
            self.status_bar.set_status("Please enter a chord name")
            return

        try:
            # Analyze the chord
            analysis = self.chord_analyzer.analyze_chord_in_key(chord_name, "C")  # Default key
            self.last_chord_analysis = analysis

            # Generate voicing and display on keyboard
            voicing = self.voicing_engine.generate_voicing(chord_name)
            voicing_type = self.voicing_engine.get_current_strategy()
            self.keyboard_display.highlight_midi_notes(voicing, voicing_type)

            # Play MIDI if enabled
            if self.midi_manager.get_status()['enabled']:
                self.midi_manager.play_chord(voicing, async_play=True)

            # Search for progressions
            progressions = self.database.search_by_chord(chord_name, include_transpositions=True)
            self.last_search_results = progressions

            # Apply current filters
            filtered_progressions = self._apply_current_filters(progressions)

            # Update displays
            self.progression_results_tree.display_progressions(filtered_progressions)
            self.chord_analysis_panel.display_chord_analysis(chord_name, analysis)

            # Update status
            self.status_bar.set_status(f"Found {len(filtered_progressions)} progressions with {chord_name}")

            logger.info(f"Analyzed chord: {chord_name}, found {len(progressions)} total progressions")

        except ChordParsingError as e:
            messagebox.showerror("Chord Error", f"Cannot parse chord '{chord_name}':\n{e}")
            self.status_bar.set_status(f"Error: Invalid chord '{chord_name}'")
        except Exception as e:
            logger.error(f"Error analyzing chord {chord_name}: {e}")
            messagebox.showerror("Analysis Error", f"Error analyzing chord:\n{e}")
            self.status_bar.set_status("Analysis failed")

    @handle_error
    def _on_voicing_changed(self, voicing_type: str):
        """Handle voicing type change."""
        self.voicing_engine.set_voicing_strategy(voicing_type)

        # Re-display current chord with new voicing if applicable
        if self.current_progression and 0 <= self.current_chord_index < len(self.current_progression):
            current_chord = self.current_progression[self.current_chord_index]
            self._display_chord(current_chord, play_midi=False)

        self.status_bar.set_status(f"Voicing changed to: {voicing_type}")
        logger.info(f"Voicing strategy changed to: {voicing_type}")

    def _on_filters_changed(self, filters: Dict):
        """Handle search filter changes."""
        if self.last_search_results:
            filtered_results = self._apply_filters(self.last_search_results, filters)
            self.progression_results_tree.display_progressions(filtered_results)
            self.status_bar.set_status(f"Filtered to {len(filtered_results)} progressions")

    # Event handlers for progression selection and navigation
    @handle_error
    def _on_progression_selected(self, progression_data: Dict):
        """Handle progression selection from search results."""
        try:
            # Load progression
            chords = progression_data.get('chords', [])
            if not chords:
                messagebox.showwarning("Invalid Progression", "Selected progression has no chords")
                return

            # Create annotations using secondary dominant detection
            key = progression_data.get('key', 'C')
            annotations = self._detect_chord_functions(chords, key)

            # Update progression state
            self.current_progression = chords
            self.current_progression_data = progression_data
            self.current_chord_index = 0

            # Update GUI components
            self.progression_list_widget.load_progression(chords, annotations)
            self.progression_info_panel.update_progression_info(progression_data)
            self.progression_navigation.update_current_chord(chords[0], 0, len(chords))

            # Display and play first chord
            self._display_chord(chords[0], play_midi=True)

            # Switch to progression tab
            self.notebook.select(1)  # Select progression tab

            self.status_bar.set_status(f"Loaded: {progression_data.get('song', 'Unknown')} ({len(chords)} chords)")
            logger.info(f"Loaded progression: {progression_data.get('song', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error loading progression: {e}")
            messagebox.showerror("Load Error", f"Error loading progression:\n{e}")

    def _go_to_previous_chord(self, play_midi: bool = True):
        """Navigate to previous chord in progression."""
        if not self.current_progression or self.current_chord_index <= 0:
            return

        self.current_chord_index -= 1
        chord = self.current_progression[self.current_chord_index]

        self._update_progression_display()
        self._display_chord(chord, play_midi=play_midi)

        logger.debug(f"Previous chord: {chord} (index {self.current_chord_index})")

    def _go_to_next_chord(self, play_midi: bool = True):
        """Navigate to next chord in progression."""
        if not self.current_progression or self.current_chord_index >= len(self.current_progression) - 1:
            return

        self.current_chord_index += 1
        chord = self.current_progression[self.current_chord_index]

        self._update_progression_display()
        self._display_chord(chord, play_midi=play_midi)

        logger.debug(f"Next chord: {chord} (index {self.current_chord_index})")

    def _go_to_first_chord(self, play_midi: bool = True):
        """Navigate to first chord in progression."""
        if not self.current_progression:
            return

        self.current_chord_index = 0
        chord = self.current_progression[0]

        self._update_progression_display()
        self._display_chord(chord, play_midi=play_midi)

        logger.debug(f"First chord: {chord}")

    def _go_to_last_chord(self, play_midi: bool = True):
        """Navigate to last chord in progression."""
        if not self.current_progression:
            return

        self.current_chord_index = len(self.current_progression) - 1
        chord = self.current_progression[self.current_chord_index]

        self._update_progression_display()
        self._display_chord(chord, play_midi=play_midi)

        logger.debug(f"Last chord: {chord}")

    @handle_error
    def _on_chord_clicked(self, index: int, chord_name: str):
        """Handle chord click in progression list."""
        if 0 <= index < len(self.current_progression):
            self.current_chord_index = index
            self._update_progression_display()
            self._display_chord(chord_name, play_midi=True)
            logger.debug(f"Jumped to chord {index}: {chord_name}")

    # Progression control event handlers
    def _play_all_chords(self):
        """Play all chords in the progression sequentially."""
        if not self.current_progression:
            messagebox.showwarning("No Progression", "No progression loaded to play")
            return

        # TODO: Implement sequential playback with timing
        self.status_bar.show_temporary_message("Sequential playback not yet implemented", 2000)
        logger.info("Play all chords requested")

    def _stop_playback(self):
        """Stop all MIDI playback."""
        self.midi_manager.playback_engine.stop_all_playback()
        self.is_auto_playing = False
        self.status_bar.show_temporary_message("Playback stopped", 1000)
        logger.info("Playback stopped")

    def _play_secondary_dominant(self):
        """Play the secondary dominant for current chord."""
        if not self.current_progression or self.current_chord_index >= len(self.current_progression):
            return

        current_chord = self.current_progression[self.current_chord_index]
        try:
            # Generate secondary dominant
            base_note, _ = self.chord_analyzer.parse_chord_name(current_chord)
            # Calculate V7 of current chord (up a fifth)
            base_index = self.chord_analyzer.chord_to_midi_notes(base_note + "7")[0] % 12
            dom_index = (base_index + 7) % 12
            dom_note = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][dom_index]
            secondary_dom = f"{dom_note}7"

            # Play secondary dominant
            voicing = self.voicing_engine.generate_voicing(secondary_dom, use_previous=False)
            self.midi_manager.play_chord(voicing, async_play=True)

            self.status_bar.show_temporary_message(f"Playing {secondary_dom} (V7/{current_chord})", 2000)
            logger.info(f"Played secondary dominant: {secondary_dom} for {current_chord}")

        except Exception as e:
            logger.warning(f"Could not play secondary dominant for {current_chord}: {e}")
            self.status_bar.show_temporary_message("Could not generate secondary dominant", 2000)

    def _show_chord_info(self):
        """Show detailed information about current chord."""
        if not self.current_progression or self.current_chord_index >= len(self.current_progression):
            return

        current_chord = self.current_progression[self.current_chord_index]
        try:
            key = self.current_progression_data.get('key', 'C')
            analysis = self.chord_analyzer.analyze_chord_in_key(current_chord, key)

            # Create info window
            info_window = tk.Toplevel(self.root)
            info_window.title(f"Chord Information: {current_chord}")
            info_window.geometry("400x300")
            info_window.transient(self.root)

            # Display analysis
            text_widget = tk.Text(info_window, wrap=tk.WORD, padx=10, pady=10)
            text_widget.pack(fill=tk.BOTH, expand=True)

            info_lines = [
                f"Chord: {current_chord}",
                f"Root: {analysis.get('base_note', 'Unknown')}",
                f"Type: {analysis.get('chord_type', 'Major')}",
                f"In key of {key}: {analysis.get('roman_numeral', 'Unknown')}",
                f"",
                f"MIDI Notes: {', '.join(map(str, analysis.get('midi_notes', [])))}",
                f"Diatonic: {'Yes' if analysis.get('is_diatonic', False) else 'No'}",
                f"Dominant Function: {'Yes' if analysis.get('is_dominant', False) else 'No'}",
            ]

            text_widget.insert(tk.END, "\n".join(info_lines))
            text_widget.config(state=tk.DISABLED)

            logger.info(f"Showing chord info for: {current_chord}")

        except Exception as e:
            logger.error(f"Error showing chord info: {e}")
            messagebox.showerror("Chord Info Error", f"Could not get chord information:\n{e}")

    def _export_progression(self):
        """Export current progression to various formats."""
        if not self.current_progression:
            messagebox.showwarning("No Progression", "No progression loaded to export")
            return

        # TODO: Implement export functionality (MIDI, text, etc.)
        self.status_bar.show_temporary_message("Export functionality not yet implemented", 2000)
        logger.info("Export progression requested")

    def _on_auto_play_changed(self, enabled: bool):
        """Handle auto-play setting change."""
        self.is_auto_playing = enabled
        logger.info(f"Auto-play {'enabled' if enabled else 'disabled'}")

    def _on_speed_changed(self, speed: float):
        """Handle playback speed change."""
        self.playback_speed = speed
        logger.info(f"Playback speed changed to: {speed}x")

    # Utility methods
    def _on_enter_pressed(self, event):
        """Handle Enter key press."""
        focused_widget = self.root.focus_get()

        # If chord entry has focus, analyze chord
        if focused_widget == self.chord_input_panel.chord_entry:
            chord_name = self.chord_input_panel.get_chord_name()
            if chord_name:
                self._on_chord_analyze(chord_name)
        # If in progression and no specific focus, play current chord
        elif self.current_progression and self.current_chord_index < len(self.current_progression):
            current_chord = self.current_progression[self.current_chord_index]
            self._display_chord(current_chord, play_midi=True)

    def _update_progression_display(self):
        """Update progression display components."""
        if not self.current_progression:
            return

        chord = self.current_progression[self.current_chord_index]
        total = len(self.current_progression)

        # Update navigation panel
        self.progression_navigation.update_current_chord(chord, self.current_chord_index, total)

        # Update list widget
        self.progression_list_widget.highlight_current_chord(self.current_chord_index)

    @handle_error
    def _display_chord(self, chord_name: str, play_midi: bool = True):
        """Display chord on keyboard and optionally play MIDI."""
        try:
            # Generate voicing
            voicing = self.voicing_engine.generate_voicing(chord_name)
            voicing_type = self.voicing_engine.get_current_strategy()

            # Display on keyboard
            self.keyboard_display.highlight_midi_notes(voicing, voicing_type)

            # Play MIDI if requested and enabled
            if play_midi and self.midi_manager.get_status()['enabled']:
                self.midi_manager.play_chord(voicing, async_play=True)

        except Exception as e:
            logger.warning(f"Could not display chord {chord_name}: {e}")
            self.status_bar.show_temporary_message(f"Error displaying chord: {chord_name}", 2000)

    def _detect_chord_functions(self, chords: List[str], key: str) -> List[str]:
        """Detect chord functions/annotations for a progression."""
        try:
            # Use chord analyzer to detect secondary dominants and other functions
            annotations = []
            scale_notes = self.chord_analyzer.get_scale_notes(key)

            for i, chord in enumerate(chords):
                try:
                    analysis = self.chord_analyzer.analyze_chord_in_key(chord, key)
                    roman_numeral = analysis.get('roman_numeral', '')

                    # Check for secondary dominant
                    if i < len(chords) - 1:
                        next_chord = chords[i + 1]
                        if self._is_secondary_dominant(chord, next_chord, key):
                            next_analysis = self.chord_analyzer.analyze_chord_in_key(next_chord, key)
                            next_roman = next_analysis.get('roman_numeral', '')
                            annotations.append(f"V7/{next_roman}")
                        else:
                            annotations.append(roman_numeral)
                    else:
                        annotations.append(roman_numeral)

                except Exception as e:
                    logger.debug(f"Could not analyze chord {chord}: {e}")
                    annotations.append("")

            return annotations

        except Exception as e:
            logger.warning(f"Error detecting chord functions: {e}")
            return [""] * len(chords)

    def _is_secondary_dominant(self, chord1: str, chord2: str, key: str) -> bool:
        """Check if chord1 is a secondary dominant of chord2."""
        try:
            base1, type1 = self.chord_analyzer.parse_chord_name(chord1)
            base2, _ = self.chord_analyzer.parse_chord_name(chord2)

            # Check if chord1 is dominant type
            if not self.chord_analyzer.is_dominant_chord(type1):
                return False

            # Check if base1 is a fifth above base2
            base1_idx = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"].index(base1)
            base2_idx = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"].index(base2)

            return (base1_idx - base2_idx) % 12 == 7  # Perfect fifth above

        except Exception:
            return False

    def _apply_current_filters(self, progressions: List[Dict]) -> List[Dict]:
        """Apply currently selected filters to progression list."""
        current_filters = self.search_filters_panel.get_current_filters()
        return self._apply_filters(progressions, current_filters)

    def _apply_filters(self, progressions: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to progression list."""
        filtered = progressions

        # Genre filter
        if filters.get('genre', 'All') != 'All':
            filtered = [p for p in filtered if p.get('genre', '').lower() == filters['genre'].lower()]

        # Composer filter
        if filters.get('composer', 'All') != 'All':
            filtered = [p for p in filtered if p.get('composer', '').lower() == filters['composer'].lower()]

        # Key filter
        if filters.get('key', 'All') != 'All':
            filtered = [p for p in filtered if p.get('key', '').lower() == filters['key'].lower()]

        # Transposition filter
        if not filters.get('include_transpositions', True):
            filtered = [p for p in filtered if p.get('transposed_by', 0) == 0]

        return filtered

    def _update_search_filters(self):
        """Update search filter options from database."""
        try:
            genres = self.database.get_all_genres()
            composers = self.database.get_all_composers()
            keys = self.database.get_all_keys()

            self.search_filters_panel.set_available_options(genres, composers, keys)
            logger.debug("Updated search filter options")

        except Exception as e:
            logger.warning(f"Could not update search filters: {e}")

    # Application lifecycle methods
    def run(self):
        """Run the main application."""
        try:
            self.status_bar.set_status("Ready - Enter a chord name to analyze")
            logger.info("Piano Chord Analyzer started")

            # Focus chord entry initially
            self.chord_input_panel.focus_entry()

            # Start main loop
            self.root.mainloop()

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            messagebox.showerror("Application Error", f"Unexpected error:\n{e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up resources before exit."""
        try:
            # Stop MIDI playback and close ports
            self.midi_manager.cleanup()

            # Clear caches
            self.database.clear_caches()

            logger.info("Application cleanup completed")

        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")


def main():
    """Main entry point for the application."""
    try:
        # Setup logging first
        setup_logging()
        logger = logging.getLogger(__name__)

        # Print startup banner
        app_info = get_app_info()
        print(f"\n{app_info['title']}")
        print("=" * len(app_info['title']))
        print("Refactored Piano Chord Analyzer")
        print("Clean architecture with modular components\n")

        # Validate configuration
        config_errors = validate_config()
        if config_errors:
            print("Configuration errors found:")
            for error in config_errors:
                print(f"  - {error}")
            print("\nProceeding with fallback settings...\n")

        # Check Python version
        if sys.version_info < (3, 7):
            print("Error: Python 3.7 or higher is required")
            print(f"Current version: {sys.version}")
            sys.exit(1)

        # Check for required modules
        required_modules = ['tkinter', 'json', 'logging', 'threading', 'pathlib']
        missing_modules = []

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            print(f"Error: Missing required modules: {', '.join(missing_modules)}")
            print("Please install the missing modules and try again.")
            sys.exit(1)

        # Check for MIDI support (optional)
        try:
            import mido
            print("✓ MIDI support available")
        except ImportError:
            print("⚠ MIDI support not available")
            print("  Install python-rtmidi and mido for full MIDI functionality:")
            print("  pip install python-rtmidi mido")
            print()

        # Check if database exists
        database_path = Path("database.json")
        if not database_path.exists():
            print("⚠ Database file 'database.json' not found")
            print("  Application will use fallback progressions")
            print("  Please ensure database.json is in the current directory")
            print()
        else:
            print("✓ Database file found")

        print("Starting application...\n")

        # Create and run application
        app = PianoChordAnalyzer()
        app.run()

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except ImportError as e:
        print(f"Import Error: {e}")
        print("\nThis might be due to missing dependencies or incorrect file structure.")
        print("Please ensure all required files are in the same directory:")
        print("  - app_config.py")
        print("  - errors.py")
        print("  - chord_analysis.py")
        print("  - transposition_engine.py")
        print("  - voicing_engine.py")
        print("  - database_manager.py")
        print("  - midi_manager.py")
        print("  - gui_components.py")
        print("  - gui_analysis.py")
        print("  - gui_progression.py")
        print("  - database.json")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error starting application: {e}", exc_info=True)
        print(f"\nCritical error: {e}")
        print("Check the log file 'piano_analyzer.log' for detailed information")
        sys.exit(1)


if __name__ == "__main__":
    main()
