# training_mode.py
"""
Module for Training Mode - chord recognition training system.
"""

import logging
import time
import random
from typing import List, Dict, Optional, Tuple

import config
from music_analytics import MusicAnalytics

logger = logging.getLogger(__name__)


# Training difficulty levels podle specifikace
TRAINING_LEVELS = {
    "Beginner": {
        "chord_types": ["maj", "m"],  # Pouze triády
        "required_correct": 5,
        "name": "Triads (3 notes)",
        "order": 0
    },
    "Elementary": {
        "chord_types": ["maj7", "m7", "7"],
        "required_correct": 8,
        "name": "Seventh Chords (4 notes)",
        "order": 1
    },
    "Intermediate": {
        "chord_types": ["maj9", "m9", "9", "6", "m6"],
        "required_correct": 10,
        "name": "Extended Chords",
        "order": 2
    },
    "Advanced": {
        "chord_types": ["7b9", "7#9", "m7b5", "dim7", "maj13"],
        "required_correct": 12,
        "name": "Altered & Complex Chords",
        "order": 3
    }
}


class TrainingSession:
    """
    Manages a training session for chord recognition.
    Tracks progress, scoring, and difficulty progression.
    """

    def __init__(self, music_analytics: MusicAnalytics):
        # Input: music_analytics (MusicAnalytics)
        # Description: Initializes training session with Beginner level.
        # Output: None
        # Called by: TrainingWindow
        self.music_analytics = music_analytics

        # Session state
        self.current_level = "Beginner"
        self.start_time = time.time()

        # Scoring
        self.correct_count = 0
        self.total_attempts = 0
        self.chords_played: List[Dict] = []

        # Current challenge
        self.target_chord: Optional[str] = None
        self.attempt_count = 0  # Počet pokusů pro aktuální akord

        # History (pro zabránění opakování)
        self.session_history: List[str] = []

        logger.info(f"Training session started at level: {self.current_level}")

    def select_next_chord(self) -> str:
        """
        Vybere další akord pro trénink podle algoritmu z specifikace.

        Priorita:
        1. Harmonická kontinuita (z databáze progresí)
        2. Nepoužité akordy v této session
        3. Aktuální difficulty level
        4. Náhodný výběr z dostupných

        Returns:
            str: Název akordu (např. "Dm7")
        """
        level_data = TRAINING_LEVELS[self.current_level]
        chord_types = level_data["chord_types"]

        # Pokud existuje předchozí akord, hledej progrese
        if self.target_chord:
            candidates = self._find_progressions_from_chord(self.target_chord, chord_types)
            if candidates:
                # Odstraň už použité akordy z kandidátů
                unused_candidates = [c for c in candidates if c not in self.session_history[-10:]]
                if unused_candidates:
                    return random.choice(unused_candidates)
                else:
                    return random.choice(candidates)  # Pokud všechny použité, použij jakýkoli

        # Fallback: náhodný akord z aktuální difficulty
        return self._random_chord_from_level(chord_types)

    def _find_progressions_from_chord(self, chord_name: str, allowed_types: List[str]) -> List[str]:
        """
        Hledá akordy, které následují po daném akordu v databázi progresí.

        Args:
            chord_name: Název akordu
            allowed_types: Povolené typy akordů pro aktuální level

        Returns:
            List[str]: Seznam kandidátních akordů
        """
        candidates = []

        for song_data in self.music_analytics.database.values():
            chords = song_data.get('chords', [])

            # Najdi akord v progresi
            for i, chord in enumerate(chords):
                if chord == chord_name and i < len(chords) - 1:
                    next_chord = chords[i + 1]

                    # Zkontroluj, zda je typ akordu povolen
                    _, chord_type = self.music_analytics.parse_chord(next_chord)
                    if chord_type in allowed_types:
                        candidates.append(next_chord)

        return list(set(candidates))  # Odstraň duplicity

    def _random_chord_from_level(self, chord_types: List[str]) -> str:
        """
        Vygeneruje náhodný akord z dostupných typů pro daný level.

        Args:
            chord_types: Seznam povolených typů akordů

        Returns:
            str: Náhodný akord
        """
        # Vyber náhodný root note
        root_note = random.choice(config.PIANO_KEYS)

        # Vyber náhodný typ akordu
        chord_type = random.choice(chord_types)

        # Konstruuj název akordu
        if chord_type == "maj":
            return root_note
        else:
            return f"{root_note}{chord_type}"

    def start_new_challenge(self) -> str:
        """
        Zahájí novou challenge s novým cílovým akordem.

        Returns:
            str: Název nového cílového akordu
        """
        self.target_chord = self.select_next_chord()
        self.attempt_count = 0
        self.session_history.append(self.target_chord)

        logger.info(f"New challenge: {self.target_chord}")
        return self.target_chord

    def check_chord(self, played_notes: set) -> Tuple[bool, str]:
        """
        Zkontroluje, zda zahraný akord odpovídá cílovému.

        Args:
            played_notes: Set MIDI note numbers

        Returns:
            Tuple[bool, str]: (správně, zpráva)
        """
        if not self.target_chord:
            return False, "No target chord set"

        # Získej noty cílového akordu
        target_notes = self.music_analytics.get_voicing(self.target_chord)
        if not target_notes:
            return False, "Cannot get target chord voicing"

        # Normalizuj na pitch classes (bez oktáv)
        target_pitch_classes = set((note - 21) % 12 for note in target_notes)
        played_pitch_classes = set((note - 21) % 12 for note in played_notes)

        # Porovnej
        is_correct = target_pitch_classes == played_pitch_classes

        if is_correct:
            message = "Correct! ✓"
            logger.info(f"Correct answer for {self.target_chord}")
        else:
            self.attempt_count += 1
            if self.attempt_count == 1:
                message = "Try again!"
            elif self.attempt_count >= 2:
                message = "Showing answer..."
            else:
                message = "Try again!"
            logger.info(f"Incorrect attempt #{self.attempt_count} for {self.target_chord}")

        return is_correct, message

    def record_attempt(self, correct: bool):
        """
        Zaznamenává pokus o zahrání akordu.

        Args:
            correct: Zda byl pokus správný
        """
        self.total_attempts += 1

        if correct:
            self.correct_count += 1

        self.chords_played.append({
            'chord': self.target_chord,
            'correct': correct,
            'attempts': self.attempt_count,
            'timestamp': time.time()
        })

        # Kontrola postupu na další level
        self._check_level_progression()

        logger.info(f"Recorded: {self.target_chord} - {'Correct' if correct else 'Incorrect'} "
                   f"(Attempts: {self.attempt_count})")

    def _check_level_progression(self):
        """
        Kontroluje, zda má uživatel postoupit na další level.
        """
        current_level_data = TRAINING_LEVELS[self.current_level]

        # Počet správných v řadě za posledních 10 pokusů
        recent = self.chords_played[-10:]
        correct_in_row = sum(1 for c in recent if c['correct'] and c['attempts'] == 1)

        if correct_in_row >= current_level_data['required_correct']:
            self._level_up()

    def _level_up(self):
        """
        Postoupí uživatele na další level.
        """
        current_order = TRAINING_LEVELS[self.current_level]["order"]

        # Najdi další level
        next_level = None
        for level_name, level_data in TRAINING_LEVELS.items():
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
        if len(self.chords_played) == 0:
            return 0.0
        return (self.correct_count / len(self.chords_played)) * 100

    def get_current_level_name(self) -> str:
        """
        Vrací lidsky čitelný název aktuálního levelu.

        Returns:
            str: Název levelu
        """
        return TRAINING_LEVELS[self.current_level]["name"]

    def get_session_duration(self) -> float:
        """
        Vrací dobu trvání session v sekundách.

        Returns:
            float: Počet sekund
        """
        return time.time() - self.start_time

    def get_target_chord_notes(self) -> List[int]:
        """
        Vrací MIDI noty cílového akordu pro zobrazení nápovědy.

        Returns:
            List[int]: MIDI note numbers
        """
        if not self.target_chord:
            return []
        return self.music_analytics.get_voicing(self.target_chord)

    def skip_current_chord(self):
        """
        Přeskočí aktuální akord (označí jako nesprávný).
        """
        self.chords_played.append({
            'chord': self.target_chord,
            'correct': False,
            'attempts': -1,  # -1 = přeskočeno
            'timestamp': time.time()
        })

        logger.info(f"Skipped chord: {self.target_chord}")

    def get_statistics(self) -> Dict:
        """
        Vrací statistiky session pro zobrazení.

        Returns:
            Dict: Statistiky
        """
        return {
            'total_chords': len(self.chords_played),
            'correct': self.correct_count,
            'percentage': self.get_score_percentage(),
            'current_level': self.current_level,
            'level_name': self.get_current_level_name(),
            'duration': self.get_session_duration(),
            'chords_played': self.chords_played.copy()
        }
