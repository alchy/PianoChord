# database_manager.py
"""
Database management for Piano Chord Analyzer.
Handles loading, searching, and managing chord progression database.
"""

import json
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from chord_analysis import ChordAnalyzer
from transposition_engine import TranspositionEngine
from errors import DatabaseError, handle_error, safe_execute

logger = logging.getLogger(__name__)


class ProgressionDatabase:
    """
    Manages the chord progression database with search and caching capabilities.
    """

    def __init__(self, database_path: str, chord_analyzer: ChordAnalyzer, transposition_engine: TranspositionEngine):
        """
        Initialize the progression database.

        Args:
            database_path: Path to the JSON database file
            chord_analyzer: ChordAnalyzer instance for validation
            transposition_engine: TranspositionEngine for creating transpositions
        """
        self.database_path = Path(database_path)
        self.chord_analyzer = chord_analyzer
        self.transposition_engine = transposition_engine

        # Core data storage
        self.original_database = {}
        self.transposed_cache = {}
        self.search_cache = {}

        # Metadata caches
        self.genres_cache = {}
        self.composers_cache = {}
        self.keys_cache = set()

        # Load and process database
        self._load_database()
        self._build_caches()

        logger.info(f"ProgressionDatabase initialized with {len(self.original_database)} songs")

    @handle_error
    def _load_database(self):
        """
        Load the progression database from JSON file with fallback.

        Raises:
            DatabaseError: If database cannot be loaded or is invalid
        """
        try:
            if not self.database_path.exists():
                logger.warning(f"Database file not found: {self.database_path}")
                self.original_database = self._get_fallback_database()
                return

            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate database structure
            if not isinstance(data, dict):
                raise DatabaseError("Database must be a JSON object")

            # Validate each song entry
            validated_data = {}
            for song_name, song_data in data.items():
                if self._validate_song_data(song_name, song_data):
                    validated_data[song_name] = song_data
                else:
                    logger.warning(f"Skipping invalid song entry: {song_name}")

            self.original_database = validated_data
            logger.info(f"Loaded {len(self.original_database)} valid songs from database")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in database file: {e}")
            raise DatabaseError(f"Database file contains invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            raise DatabaseError(f"Cannot load database: {e}")

    def _validate_song_data(self, song_name: str, song_data: dict) -> bool:
        """
        Validate a single song entry in the database.

        Args:
            song_name: Name of the song
            song_data: Song data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not isinstance(song_data, dict):
                logger.warning(f"Song {song_name}: data must be a dict")
                return False

            if 'progressions' not in song_data:
                logger.warning(f"Song {song_name}: missing 'progressions' field")
                return False

            progressions = song_data['progressions']
            if not isinstance(progressions, list) or not progressions:
                logger.warning(f"Song {song_name}: 'progressions' must be non-empty list")
                return False

            # Validate each progression
            for i, progression in enumerate(progressions):
                if not isinstance(progression, dict):
                    logger.warning(f"Song {song_name}: progression {i} must be dict")
                    return False

                if 'chords' not in progression:
                    logger.warning(f"Song {song_name}: progression {i} missing 'chords'")
                    return False

                chords = progression['chords']
                if not isinstance(chords, list) or not chords:
                    logger.warning(f"Song {song_name}: progression {i} 'chords' must be non-empty list")
                    return False

                # Validate chord names
                for j, chord in enumerate(chords):
                    if not isinstance(chord, str) or not chord.strip():
                        logger.warning(f"Song {song_name}: progression {i} chord {j} invalid")
                        return False

                    # Check if chord can be parsed (optional validation)
                    if not self.chord_analyzer.validate_chord_name(chord):
                        logger.warning(f"Song {song_name}: invalid chord '{chord}' in progression {i}")
                        # Don't return False here - might be extended chord notation

            return True

        except Exception as e:
            logger.warning(f"Error validating song {song_name}: {e}")
            return False

    def _get_fallback_database(self) -> Dict:
        """
        Get a minimal fallback database when main database fails to load.

        Returns:
            Basic database with essential progressions
        """
        return {
            "ii-V-I Major Basic": {
                "genre": "jazz-progressions",
                "key": "C",
                "difficulty": "Easy",
                "progressions": [
                    {
                        "chords": ["Dm7", "G7", "Cmaj7"],
                        "description": "Basic ii-V-I progression in C major"
                    }
                ]
            },
            "ii-V-i Minor Basic": {
                "genre": "jazz-progressions",
                "key": "Cm",
                "difficulty": "Easy",
                "progressions": [
                    {
                        "chords": ["Dm7b5", "G7", "Cm7"],
                        "description": "Basic ii-V-i progression in C minor"
                    }
                ]
            },
            "Blues in C": {
                "genre": "blues",
                "key": "C",
                "difficulty": "Easy",
                "progressions": [
                    {
                        "chords": ["C7", "F7", "C7", "G7"],
                        "description": "Basic 12-bar blues progression"
                    }
                ]
            }
        }

    @handle_error
    def _build_caches(self):
        """Build lookup caches for faster searching."""
        self.genres_cache.clear()
        self.composers_cache.clear()
        self.keys_cache.clear()

        for song_name, song_data in self.original_database.items():
            # Build genre cache
            genre = song_data.get('genre', 'unknown')
            if genre not in self.genres_cache:
                self.genres_cache[genre] = []
            self.genres_cache[genre].append(song_name)

            # Build composer cache
            composer = song_data.get('composer', 'unknown')
            if composer not in self.composers_cache:
                self.composers_cache[composer] = []
            self.composers_cache[composer].append(song_name)

            # Build keys cache
            key = song_data.get('key', 'C')
            self.keys_cache.add(key)

        logger.info(
            f"Built caches: {len(self.genres_cache)} genres, {len(self.composers_cache)} composers, {len(self.keys_cache)} keys")

    @handle_error
    def search_by_chord(self, chord_name: str, include_transpositions: bool = True) -> List[Dict]:
        """
        Search for progressions containing a specific chord.

        Args:
            chord_name: Chord to search for
            include_transpositions: Whether to include transposed versions

        Returns:
            List of matching progressions with metadata

        Raises:
            DatabaseError: If search fails
        """
        # Check cache first
        cache_key = f"{chord_name}_{include_transpositions}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key].copy()

        try:
            results = []

            # Search original database
            for song_name, song_data in self.original_database.items():
                matching_progressions = self._find_chord_in_song(chord_name, song_data)
                for progression in matching_progressions:
                    results.append({
                        'song': song_name,
                        'chords': progression['chords'],
                        'description': progression.get('description', ''),
                        'genre': song_data.get('genre', 'unknown'),
                        'key': song_data.get('key', 'C'),
                        'composer': song_data.get('composer', 'unknown'),
                        'year': song_data.get('year', None),
                        'difficulty': song_data.get('difficulty', 'unknown'),
                        'transposed_by': 0,
                        'original_key': song_data.get('key', 'C')
                    })

            # Search transposed versions if requested
            if include_transpositions:
                transposed_results = self._search_transposed_versions(chord_name)
                results.extend(transposed_results)

            # Cache results
            self.search_cache[cache_key] = results.copy()

            logger.info(f"Found {len(results)} progressions containing chord '{chord_name}'")
            return results

        except Exception as e:
            raise DatabaseError(f"Search failed for chord '{chord_name}': {e}")

    def _find_chord_in_song(self, chord_name: str, song_data: Dict) -> List[Dict]:
        """
        Find progressions in a song that contain the specified chord.

        Args:
            chord_name: Chord to find
            song_data: Song data to search in

        Returns:
            List of matching progressions
        """
        matching_progressions = []

        for progression in song_data.get('progressions', []):
            chords = progression.get('chords', [])
            if chord_name in chords:
                matching_progressions.append(progression)

        return matching_progressions

    def _search_transposed_versions(self, chord_name: str) -> List[Dict]:
        """
        Search for the chord in all transposed versions of songs.

        Args:
            chord_name: Chord to search for

        Returns:
            List of matching transposed progressions
        """
        results = []

        for song_name, song_data in self.original_database.items():
            # Try transposing this song to all keys to find the chord
            for semitones in range(1, 12):
                try:
                    # Check if we have this transposition cached
                    cache_key = f"{song_name}_{semitones}"
                    if cache_key not in self.transposed_cache:
                        transposed_data = self.transposition_engine.transpose_song_data(song_data, semitones)
                        self.transposed_cache[cache_key] = transposed_data

                    transposed_data = self.transposed_cache[cache_key]
                    matching_progressions = self._find_chord_in_song(chord_name, transposed_data)

                    for progression in matching_progressions:
                        results.append({
                            'song': song_name,
                            'chords': progression['chords'],
                            'description': progression.get('description', ''),
                            'genre': transposed_data.get('genre', 'unknown'),
                            'key': transposed_data.get('key', 'C'),
                            'composer': song_data.get('composer', 'unknown'),
                            'year': song_data.get('year', None),
                            'difficulty': song_data.get('difficulty', 'unknown'),
                            'transposed_by': semitones,
                            'original_key': song_data.get('key', 'C')
                        })

                except Exception as e:
                    logger.debug(f"Failed to transpose {song_name} by {semitones}: {e}")
                    continue

        return results

    def get_songs_by_genre(self, genre: str) -> List[str]:
        """
        Get all songs of a specific genre.

        Args:
            genre: Genre to search for

        Returns:
            List of song names
        """
        return self.genres_cache.get(genre, []).copy()

    def get_songs_by_composer(self, composer: str) -> List[str]:
        """
        Get all songs by a specific composer.

        Args:
            composer: Composer to search for

        Returns:
            List of song names
        """
        return self.composers_cache.get(composer, []).copy()

    def get_songs_by_key(self, key: str) -> List[str]:
        """
        Get all songs in a specific key.

        Args:
            key: Key to search for

        Returns:
            List of song names
        """
        matching_songs = []
        for song_name, song_data in self.original_database.items():
            if song_data.get('key', '').lower() == key.lower():
                matching_songs.append(song_name)
        return matching_songs

    def get_all_genres(self) -> List[str]:
        """Get list of all available genres."""
        return list(self.genres_cache.keys())

    def get_all_composers(self) -> List[str]:
        """Get list of all available composers."""
        return list(self.composers_cache.keys())

    def get_all_keys(self) -> List[str]:
        """Get list of all available keys."""
        return sorted(self.keys_cache)

    def get_song_data(self, song_name: str) -> Optional[Dict]:
        """
        Get complete data for a specific song.

        Args:
            song_name: Name of song to retrieve

        Returns:
            Song data dictionary or None if not found
        """
        return self.original_database.get(song_name)

    def get_database_stats(self) -> Dict:
        """
        Get statistics about the database.

        Returns:
            Dictionary with database statistics
        """
        total_progressions = sum(len(song_data.get('progressions', []))
                                 for song_data in self.original_database.values())

        total_chords = 0
        for song_data in self.original_database.values():
            for progression in song_data.get('progressions', []):
                total_chords += len(progression.get('chords', []))

        return {
            'total_songs': len(self.original_database),
            'total_progressions': total_progressions,
            'total_chords': total_chords,
            'genres_count': len(self.genres_cache),
            'composers_count': len(self.composers_cache),
            'keys_count': len(self.keys_cache),
            'cached_transpositions': len(self.transposed_cache),
            'cached_searches': len(self.search_cache)
        }

    def clear_caches(self):
        """Clear all internal caches to free memory."""
        self.transposed_cache.clear()
        self.search_cache.clear()
        logger.info("Database caches cleared")

    @handle_error
    def reload_database(self):
        """
        Reload the database from file and rebuild caches.

        Raises:
            DatabaseError: If reload fails
        """
        self.clear_caches()
        self._load_database()
        self._build_caches()
        logger.info("Database reloaded successfully")
