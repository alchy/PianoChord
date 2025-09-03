# voicing_engine.py
"""
Voicing engine for Piano Chord Analyzer.
Handles different voicing strategies: root position, smooth voice leading, drop-2, etc.
"""

import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from chord_analysis import ChordAnalyzer
from errors import VoicingError, handle_error

logger = logging.getLogger(__name__)


class VoicingStrategy(ABC):
    """Abstract base class for voicing strategies."""

    @abstractmethod
    def calculate_voicing(self, midi_notes: List[int], previous_voicing: Optional[List[int]] = None) -> List[int]:
        """
        Calculate voicing for given MIDI notes.

        Args:
            midi_notes: Basic chord MIDI notes
            previous_voicing: Previous chord voicing for smooth voice leading

        Returns:
            List of MIDI notes for the voicing
        """
        pass


class RootPositionVoicing(VoicingStrategy):
    """Root position voicing - chords in basic position."""

    def calculate_voicing(self, midi_notes: List[int], previous_voicing: Optional[List[int]] = None) -> List[int]:
        """
        Returns chord in root position (no changes).

        Args:
            midi_notes: Basic chord MIDI notes
            previous_voicing: Ignored for root position

        Returns:
            Original MIDI notes sorted
        """
        return sorted(midi_notes)


class SmoothVoicing(VoicingStrategy):
    """Smooth voice leading - minimizes movement between chords."""

    def calculate_voicing(self, midi_notes: List[int], previous_voicing: Optional[List[int]] = None) -> List[int]:
        """
        Calculate smooth voicing to minimize voice movement.

        Args:
            midi_notes: Basic chord MIDI notes
            previous_voicing: Previous chord for comparison

        Returns:
            Optimized MIDI notes for smooth voice leading
        """
        if not previous_voicing:
            return sorted(midi_notes)

        best_voicing = midi_notes.copy()
        min_distance = float('inf')

        # Calculate average pitch of previous chord
        prev_average = sum(previous_voicing) / len(previous_voicing)

        # Try different octave shifts and inversions
        for octave_shift in range(-2, 3):  # Up to 2 octaves in either direction
            for inversion in range(len(midi_notes)):
                # Create inversion by moving notes up an octave
                inverted_notes = (midi_notes[inversion:] +
                                  [note + 12 for note in midi_notes[:inversion]])

                # Apply octave shift to all notes
                current_voicing = [note + (octave_shift * 12) for note in inverted_notes]

                # Ensure notes are in valid MIDI range
                current_voicing = [note for note in current_voicing if 0 <= note <= 127]

                if not current_voicing:
                    continue

                # Calculate average pitch and distance from previous
                current_average = sum(current_voicing) / len(current_voicing)
                distance = abs(current_average - prev_average)

                # Keep track of best voicing
                if distance < min_distance:
                    min_distance = distance
                    best_voicing = current_voicing.copy()

        return sorted(best_voicing)


class Drop2Voicing(VoicingStrategy):
    """Drop-2 voicing - drops the second highest note by an octave."""

    def calculate_voicing(self, midi_notes: List[int], previous_voicing: Optional[List[int]] = None) -> List[int]:
        """
        Calculate drop-2 voicing.

        Args:
            midi_notes: Basic chord MIDI notes
            previous_voicing: Ignored for drop-2

        Returns:
            MIDI notes with drop-2 voicing applied
        """
        if len(midi_notes) < 4:
            # Need at least 4 notes for drop-2, return as-is
            return sorted(midi_notes)

        # Sort notes and identify second highest
        sorted_notes = sorted(midi_notes)
        second_highest = sorted_notes[-2]

        # Create new voicing with second highest note dropped an octave
        drop2_voicing = midi_notes.copy()

        # Find and replace the second highest note
        for i, note in enumerate(drop2_voicing):
            if note == second_highest:
                drop2_voicing[i] = note - 12
                break

        # Filter out notes below MIDI range
        drop2_voicing = [note for note in drop2_voicing if note >= 0]

        return sorted(drop2_voicing)


class VoicingEngine:
    """
    Main voicing engine that manages different voicing strategies.
    """

    def __init__(self, chord_analyzer: ChordAnalyzer):
        """
        Initialize voicing engine with available strategies.

        Args:
            chord_analyzer: ChordAnalyzer instance for chord parsing
        """
        self.chord_analyzer = chord_analyzer
        self.previous_voicing = []

        # Available voicing strategies
        self.strategies = {
            'root': RootPositionVoicing(),
            'smooth': SmoothVoicing(),
            'drop2': Drop2Voicing()
        }

        # Default voicing type
        self.current_strategy = 'root'

        logger.info("VoicingEngine initialized with strategies: %s", list(self.strategies.keys()))

    def set_voicing_strategy(self, strategy_name: str) -> bool:
        """
        Set the current voicing strategy.

        Args:
            strategy_name: Name of strategy ('root', 'smooth', 'drop2')

        Returns:
            True if strategy was set, False if invalid strategy name
        """
        if strategy_name not in self.strategies:
            logger.warning(f"Unknown voicing strategy: {strategy_name}")
            return False

        self.current_strategy = strategy_name
        logger.info(f"Voicing strategy set to: {strategy_name}")
        return True

    def get_available_strategies(self) -> List[str]:
        """
        Get list of available voicing strategy names.

        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())

    def get_current_strategy(self) -> str:
        """
        Get current voicing strategy name.

        Returns:
            Current strategy name
        """
        return self.current_strategy

    @handle_error
    def generate_voicing(self, chord_name: str, use_previous: bool = True) -> List[int]:
        """
        Generate voicing for a chord using the current strategy.

        Args:
            chord_name: Chord name to voice (e.g., "Dm7", "C#maj9")
            use_previous: Whether to use previous voicing for smooth voice leading

        Returns:
            List of MIDI notes for the voicing

        Raises:
            VoicingError: If voicing generation fails
        """
        try:
            # Get basic chord MIDI notes
            basic_midi = self.chord_analyzer.chord_to_midi_notes(chord_name)

            # Get current strategy
            strategy = self.strategies[self.current_strategy]

            # Calculate voicing
            previous = self.previous_voicing if use_previous else None
            voicing = strategy.calculate_voicing(basic_midi, previous)

            # Update previous voicing for next chord
            if voicing:
                self.previous_voicing = voicing.copy()

            return voicing

        except Exception as e:
            raise VoicingError(f"Cannot generate voicing for chord '{chord_name}': {e}")

    @handle_error
    def generate_progression_voicing(self, chord_names: List[str], strategy_name: Optional[str] = None) -> List[
        List[int]]:
        """
        Generate voicings for an entire chord progression.

        Args:
            chord_names: List of chord names in the progression
            strategy_name: Optional specific strategy to use (defaults to current)

        Returns:
            List of voicings (each voicing is a list of MIDI notes)

        Raises:
            VoicingError: If any chord fails to voice
        """
        if not chord_names:
            return []

        # Temporarily set strategy if specified
        original_strategy = None
        if strategy_name and strategy_name in self.strategies:
            original_strategy = self.current_strategy
            self.current_strategy = strategy_name

        try:
            voicings = []
            failed_chords = []

            # Clear previous voicing for fresh start
            self.previous_voicing = []

            for i, chord_name in enumerate(chord_names):
                try:
                    voicing = self.generate_voicing(chord_name, use_previous=(i > 0))
                    voicings.append(voicing)
                except VoicingError as e:
                    failed_chords.append((i, chord_name, str(e)))
                    logger.warning(f"Failed to voice chord {i}: {chord_name} - {e}")
                    # Use basic root position as fallback
                    try:
                        basic_voicing = self.chord_analyzer.chord_to_midi_notes(chord_name)
                        voicings.append(basic_voicing)
                    except Exception:
                        # Ultimate fallback - empty voicing
                        voicings.append([])

            if failed_chords:
                logger.warning(f"Some chords failed to voice: {failed_chords}")

            return voicings

        finally:
            # Restore original strategy if it was changed
            if original_strategy:
                self.current_strategy = original_strategy

    @handle_error
    def compare_voicing_strategies(self, chord_name: str) -> Dict[str, List[int]]:
        """
        Generate voicings using all available strategies for comparison.

        Args:
            chord_name: Chord to voice with all strategies

        Returns:
            Dictionary mapping strategy names to their voicings

        Raises:
            VoicingError: If basic chord analysis fails
        """
        try:
            basic_midi = self.chord_analyzer.chord_to_midi_notes(chord_name)
            comparison = {}

            for strategy_name, strategy in self.strategies.items():
                try:
                    voicing = strategy.calculate_voicing(basic_midi, self.previous_voicing)
                    comparison[strategy_name] = voicing
                except Exception as e:
                    logger.warning(f"Strategy {strategy_name} failed for {chord_name}: {e}")
                    comparison[strategy_name] = basic_midi.copy()

            return comparison

        except Exception as e:
            raise VoicingError(f"Cannot compare voicing strategies for chord '{chord_name}': {e}")

    def reset_previous_voicing(self):
        """Reset the previous voicing memory (useful for new progressions)."""
        self.previous_voicing = []
        logger.debug("Previous voicing memory reset")

    def get_voicing_info(self, chord_name: str) -> Dict:
        """
        Get detailed information about a chord's voicing.

        Args:
            chord_name: Chord to analyze

        Returns:
            Dictionary with voicing information
        """
        try:
            voicing = self.generate_voicing(chord_name, use_previous=False)
            basic_midi = self.chord_analyzer.chord_to_midi_notes(chord_name)

            return {
                'chord_name': chord_name,
                'strategy': self.current_strategy,
                'basic_notes': basic_midi,
                'voiced_notes': voicing,
                'note_count': len(voicing),
                'pitch_range': max(voicing) - min(voicing) if voicing else 0,
                'lowest_note': min(voicing) if voicing else None,
                'highest_note': max(voicing) if voicing else None
            }

        except Exception as e:
            logger.error(f"Cannot get voicing info for {chord_name}: {e}")
            return {
                'chord_name': chord_name,
                'strategy': self.current_strategy,
                'error': str(e)
            }
