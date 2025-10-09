# note_training.py
"""
Module for Note Training Mode - single note recognition training.
"""

import logging
import time
import random
from typing import List, Dict, Optional, Tuple

import config

logger = logging.getLogger(__name__)


# Note Training difficulty levels
NOTE_TRAINING_LEVELS = {
    "Beginner": {
        "note_range": ["C", "D", "E", "F", "G", "A", "B"],  # Pouze bílé klávesy (C dur)
        "use_accidentals": False,
        "required_correct": 7,
        "name": "White Keys Only (C major)",
        "order": 0
    },
    "Elementary": {
        "note_range": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],  # Všechny noty
        "use_accidentals": True,
        "accidental_style": "sharp",  # Pouze křížky
        "required_correct": 10,
        "name": "All Notes (Sharp notation)",
        "order": 1
    },
    "Intermediate": {
        "note_range": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],  # Všechny noty
        "use_accidentals": True,
        "accidental_style": "flat",  # Pouze béčka
        "required_correct": 10,
        "name": "All Notes (Flat notation)",
        "order": 2
    },
    "Advanced": {
        "note_range": config.PIANO_KEYS,  # Všechny noty
        "use_accidentals": True,
        "accidental_style": "mixed",  # Náhodně křížky nebo béčka
        "required_correct": 15,
        "name": "Mixed Accidentals",
        "order": 3
    }
}


class NoteTrainingSession:
    """
    Manages a training session for single note recognition.
    Similar to ChordTrainingSession but for individual notes.
    """

    def __init__(self):
        # Input: None
        # Description: Initializes note training session with Beginner level.
        # Output: None
        # Called by: NoteTrainingWindow

        # Session state
        self.current_level = "Beginner"
        self.start_time = time.time()

        # Scoring
        self.correct_count = 0
        self.total_attempts = 0
        self.notes_played: List[Dict] = []

        # Current challenge
        self.target_note: Optional[str] = None
        self.target_midi_note: Optional[int] = None  # Konkrétní MIDI note number
        self.attempt_count = 0

        # History (pro zabránění opakování)
        self.session_history: List[str] = []

        logger.info(f"Note Training session started at level: {self.current_level}")

    def select_next_note(self) -> Tuple[str, int]:
        """
        Vybere další notu pro trénink.

        Returns:
            Tuple[str, int]: (název noty, MIDI note number)
        """
        level_data = NOTE_TRAINING_LEVELS[self.current_level]
        note_range = level_data["note_range"]

        # Vyber náhodnou notu
        note_name = random.choice(note_range)

        # Pro Advanced level s mixed accidentals: náhodně vyber enharmonickou variantu
        if level_data.get("accidental_style") == "mixed" and "#" in note_name:
            # Např. C# může být i Db
            enharmonic = self._get_enharmonic_equivalent(note_name)
            if enharmonic and random.choice([True, False]):
                note_name = enharmonic

        # Vyber náhodnou oktávu (C4-C6 = MIDI 60-84 pro rozumný rozsah)
        octave = random.choice([4, 5])

        # Vypočítej MIDI note number
        midi_note = self._note_name_to_midi(note_name, octave)

        return note_name, midi_note

    def _get_enharmonic_equivalent(self, note: str) -> Optional[str]:
        """
        Vrací enharmonický ekvivalent noty (křížek → béčko nebo naopak).

        Args:
            note: Název noty (např. "C#")

        Returns:
            Optional[str]: Enharmonický ekvivalent nebo None
        """
        enharmonics = {
            "C#": "Db",
            "D#": "Eb",
            "F#": "Gb",
            "G#": "Ab",
            "A#": "Bb",
            "Db": "C#",
            "Eb": "D#",
            "Gb": "F#",
            "Ab": "G#",
            "Bb": "A#"
        }
        return enharmonics.get(note)

    def _note_name_to_midi(self, note_name: str, octave: int) -> int:
        """
        Převede název noty a oktávu na MIDI note number.

        Args:
            note_name: Název noty (např. "C", "C#", "Db")
            octave: Oktáva (0-8)

        Returns:
            int: MIDI note number
        """
        # Normalizuj název na sharp notaci pro výpočet
        note_map = {
            "C": 0, "C#": 1, "Db": 1,
            "D": 2, "D#": 3, "Eb": 3,
            "E": 4, "Fb": 4,
            "F": 5, "E#": 5, "F#": 6, "Gb": 6,
            "G": 7, "G#": 8, "Ab": 8,
            "A": 9, "A#": 10, "Bb": 10,
            "B": 11, "Cb": 11
        }

        pitch_class = note_map.get(note_name, 0)
        midi_note = 12 * (octave + 1) + pitch_class

        return midi_note

    def start_new_challenge(self) -> Tuple[str, int]:
        """
        Zahájí novou challenge s novou cílovou notou.

        Returns:
            Tuple[str, int]: (název noty, MIDI note number)
        """
        self.target_note, self.target_midi_note = self.select_next_note()
        self.attempt_count = 0
        self.session_history.append(self.target_note)

        logger.info(f"New challenge: {self.target_note} (MIDI: {self.target_midi_note})")
        return self.target_note, self.target_midi_note

    def check_note(self, played_midi_note: int) -> Tuple[bool, str]:
        """
        Zkontroluje, zda zahraná nota odpovídá cílové.

        Args:
            played_midi_note: MIDI note number zahraný uživatelem

        Returns:
            Tuple[bool, str]: (správně, zpráva)
        """
        if not self.target_midi_note:
            return False, "No target note set"

        # Porovnej pitch class (ignoruj oktávu)
        target_pitch_class = self.target_midi_note % 12
        played_pitch_class = played_midi_note % 12

        is_correct = target_pitch_class == played_pitch_class

        if is_correct:
            message = "Correct! ✓"
            logger.info(f"Correct answer: {self.target_note}")
        else:
            self.attempt_count += 1
            if self.attempt_count == 1:
                message = "Try again!"
            elif self.attempt_count >= 2:
                message = "Showing answer..."
            else:
                message = "Try again!"
            logger.info(f"Incorrect attempt #{self.attempt_count} for {self.target_note}")

        return is_correct, message

    def record_attempt(self, correct: bool):
        """
        Zaznamenává pokus o zahrání noty.

        Args:
            correct: Zda byl pokus správný
        """
        self.total_attempts += 1

        if correct:
            self.correct_count += 1

        self.notes_played.append({
            'note': self.target_note,
            'correct': correct,
            'attempts': self.attempt_count,
            'timestamp': time.time()
        })

        # Kontrola postupu na další level
        self._check_level_progression()

        logger.info(f"Recorded: {self.target_note} - {'Correct' if correct else 'Incorrect'} "
                   f"(Attempts: {self.attempt_count})")

    def _check_level_progression(self):
        """
        Kontroluje, zda má uživatel postoupit na další level.
        """
        current_level_data = NOTE_TRAINING_LEVELS[self.current_level]

        # Počet správných na první pokus za posledních 10 pokusů
        recent = self.notes_played[-10:]
        correct_in_row = sum(1 for n in recent if n['correct'] and n['attempts'] == 1)

        if correct_in_row >= current_level_data['required_correct']:
            self._level_up()

    def _level_up(self):
        """
        Postoupí uživatele na další level.
        """
        current_order = NOTE_TRAINING_LEVELS[self.current_level]["order"]

        # Najdi další level
        next_level = None
        for level_name, level_data in NOTE_TRAINING_LEVELS.items():
            if level_data["order"] == current_order + 1:
                next_level = level_name
                break

        if next_level:
            self.current_level = next_level
            logger.info(f"Level up! New level: {self.current_level}")
            return True
        else:
            logger.info("Already at maximum level")
            return False

    def get_score_percentage(self) -> float:
        """
        Vrací úspěšnost v procentech.

        Returns:
            float: Procento úspěšnosti
        """
        if len(self.notes_played) == 0:
            return 0.0
        return (self.correct_count / len(self.notes_played)) * 100

    def get_current_level_name(self) -> str:
        """
        Vrací lidsky čitelný název aktuálního levelu.

        Returns:
            str: Název levelu
        """
        return NOTE_TRAINING_LEVELS[self.current_level]["name"]

    def get_session_duration(self) -> float:
        """
        Vrací dobu trvání session v sekundách.

        Returns:
            float: Počet sekund
        """
        return time.time() - self.start_time

    def skip_current_note(self):
        """
        Přeskočí aktuální notu (označí jako nesprávnou).
        """
        self.notes_played.append({
            'note': self.target_note,
            'correct': False,
            'attempts': -1,  # -1 = přeskočeno
            'timestamp': time.time()
        })

        logger.info(f"Skipped note: {self.target_note}")

    def get_statistics(self) -> Dict:
        """
        Vrací statistiky session pro zobrazení.

        Returns:
            Dict: Statistiky
        """
        return {
            'total_notes': len(self.notes_played),
            'correct': self.correct_count,
            'percentage': self.get_score_percentage(),
            'current_level': self.current_level,
            'level_name': self.get_current_level_name(),
            'duration': self.get_session_duration(),
            'notes_played': self.notes_played.copy()
        }
