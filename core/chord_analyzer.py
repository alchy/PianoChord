# core/chord_analyzer.py
"""
core/chord_analyzer.py - Nezávislý analyzátor akordů.
Čistá logika bez GUI závislostí - může být použita v jiných programech.
Analyzuje akordy a hledá je v databázi progresí.
"""

from typing import Dict, Any, List
import logging
from config import MusicalConstants
from core.music_theory import parse_chord_name, get_chord_intervals

logger = logging.getLogger(__name__)


class ChordAnalyzer:
    """
    Nezávislý analyzátor harmonie s využitím databáze reálných progresí.
    Může být použit bez GUI nebo jako součást jiné aplikace.
    """

    @classmethod
    def analyze(cls, base_note: str, chord_type: str, database_manager=None) -> Dict[str, Any]:
        """
        Hlavní metoda pro analýzu akordu.
        Zaměřuje se na vlastnosti akordu a jeho výskyt v reálných progresích.

        Args:
            base_note: Základní nota akordu (např. "C", "F#")
            chord_type: Typ akordu (např. "maj7", "m7")
            database_manager: Instance ProgressionManager pro hledání progresí (volitelné)

        Returns:
            Dict[str, Any]: Slovník s výsledky analýzy obsahující:
                - chord_name: Celý název akordu
                - base_note: Základní nota
                - chord_type: Typ akordu
                - chord_intervals: Intervaly v půltónech
                - chord_notes: Seznam not v akordu (názvy)
                - midi_notes: MIDI čísla not v základní pozici
                - real_progressions: Seznam nalezených progresí (pokud je database_manager)
        """
        chord_full_name = f"{base_note}{chord_type or ''}".strip()

        # Pokud je chord_type prázdný, považujeme za dur
        if not chord_type:
            chord_type = "maj"

        logger.debug(f"Analyzuji akord: {chord_full_name} (base_note='{base_note}', chord_type='{chord_type}')")

        # Analýza intervalů a not akordu
        try:
            chord_intervals = get_chord_intervals(chord_type)
            chord_notes = cls._get_chord_note_names(base_note, chord_intervals)
            midi_notes = cls._get_chord_midi_notes(base_note, chord_intervals)
        except (ValueError, IndexError) as e:
            logger.error(f"Chyba při získávání not pro {chord_full_name}: {e}")
            chord_intervals = []
            chord_notes = []
            midi_notes = []

        # Hledání v databázi progresí (pokud je k dispozici)
        real_progressions = []
        if database_manager:
            try:
                real_progressions = database_manager.find_progressions_by_chord(base_note, chord_type)
                logger.debug(f"Nalezeno {len(real_progressions)} progresí pro {chord_full_name}")
            except Exception as e:
                logger.error(f"Chyba při hledání progresí pro {chord_full_name}: {e}")

        # Sestavení výsledku
        result = {
            "chord_name": chord_full_name,
            "base_note": base_note,
            "chord_type": chord_type,
            "chord_intervals": chord_intervals,
            "chord_notes": chord_notes,
            "midi_notes": midi_notes,
            "real_progressions": real_progressions,
        }

        logger.info(
            f"Analýza dokončena pro {chord_full_name}: {len(chord_notes)} not, {len(real_progressions)} progresí")
        return result

    @classmethod
    def analyze_chord_name(cls, chord_full_name: str, database_manager=None) -> Dict[str, Any]:
        """
        Analyzuje akord zadaný celým názvem.
        Pohodlná metoda která sama parsuje název.

        Args:
            chord_full_name: Celý název akordu (např. "Cmaj7")
            database_manager: Instance ProgressionManager pro hledání progresí

        Returns:
            Dict[str, Any]: Výsledky analýzy

        Raises:
            ValueError: Pokud je název akordu neplatný
        """
        try:
            base_note, chord_type = parse_chord_name(chord_full_name)
            return cls.analyze(base_note, chord_type, database_manager)
        except ValueError as e:
            logger.error(f"Chyba při parsování akordu '{chord_full_name}': {e}")
            raise

    @classmethod
    def _get_chord_note_names(cls, base_note: str, intervals: List[int]) -> List[str]:
        """
        Převede intervaly na názvy not.

        Args:
            base_note: Základní nota
            intervals: Seznam intervalů v půltónech

        Returns:
            List[str]: Seznam názvů not
        """
        if not intervals:
            return []

        try:
            base_note_val = MusicalConstants.PIANO_KEYS.index(base_note)
            note_names = []

            for interval in intervals:
                note_index = (base_note_val + interval) % 12
                note_names.append(MusicalConstants.PIANO_KEYS[note_index])

            return note_names
        except (ValueError, IndexError) as e:
            logger.error(f"Chyba při převodu intervalů na noty pro {base_note}: {e}")
            return []

    @classmethod
    def _get_chord_midi_notes(cls, base_note: str, intervals: List[int], octave: int = 4) -> List[int]:
        """
        Převede intervaly na MIDI čísla not v zadané oktávě.

        Args:
            base_note: Základní nota
            intervals: Seznam intervalů v půltónech
            octave: Oktáva pro MIDI noty (default 4 = C4)

        Returns:
            List[int]: Seznam MIDI čísel not
        """
        if not intervals:
            return []

        try:
            base_note_val = MusicalConstants.PIANO_KEYS.index(base_note)
            base_midi = 12 * octave + base_note_val

            return [base_midi + interval for interval in intervals]
        except (ValueError, IndexError) as e:
            logger.error(f"Chyba při převodu na MIDI noty pro {base_note}: {e}")
            return []

    @classmethod
    def get_chord_voicing(cls, base_note: str, chord_type: str, voicing_type: str = "root",
                          prev_chord_midi: List[int] = None) -> List[int]:
        """
        Získá MIDI noty pro akord v určitém voicingu.
        Nezávislá metoda pro generování voicingů.

        Args:
            base_note: Základní nota akordu
            chord_type: Typ akordu
            voicing_type: Typ voicingu ("root", "smooth", "drop2")
            prev_chord_midi: Předchozí akord pro smooth voicing

        Returns:
            List[int]: MIDI čísla not v požadovaném voicingu
        """
        # Základní root voicing
        chord_intervals = get_chord_intervals(chord_type)
        root_voicing = cls._get_chord_midi_notes(base_note, chord_intervals)

        if voicing_type == "smooth" and prev_chord_midi:
            return cls._get_smooth_voicing(root_voicing, prev_chord_midi)
        elif voicing_type == "drop2":
            return cls._get_drop2_voicing(root_voicing)
        else:
            return root_voicing

    @classmethod
    def _get_smooth_voicing(cls, root_voicing: List[int], prev_chord_midi: List[int]) -> List[int]:
        """
        Najde nejbližší inverzi akordu k předchozímu akordu pro plynulé přechody.

        Args:
            root_voicing: Základní voicing akordu
            prev_chord_midi: MIDI noty předchozího akordu

        Returns:
            List[int]: MIDI noty v smooth voicingu
        """
        if not prev_chord_midi or not root_voicing:
            return root_voicing

        best_voicing = root_voicing
        min_distance = float('inf')

        # Vypočítá průměrnou výšku předchozího akordu
        avg_prev = sum(prev_chord_midi) / len(prev_chord_midi)

        # Prozkoumá různé oktávy a inverze pro nejmenší vzdálenost
        for octave_shift in range(-2, 3):
            for inversion in range(len(root_voicing)):
                # Vytvoří inverzi (rotuje noty)
                inverted_notes = root_voicing[inversion:] + [note + 12 for note in root_voicing[:inversion]]
                current_voicing = [note + octave_shift * 12 for note in inverted_notes]

                # Vypočítá vzdálenost od předchozího akordu
                avg_current = sum(current_voicing) / len(current_voicing)
                distance = abs(avg_current - avg_prev)

                if distance < min_distance:
                    min_distance = distance
                    best_voicing = current_voicing

        logger.debug(f"Smooth voicing: vzdálenost {min_distance:.1f}")
        return best_voicing

    @classmethod
    def _get_drop2_voicing(cls, root_voicing: List[int]) -> List[int]:
        """
        Vytvoří Drop 2 voicing - druhý nejvyšší tón se posune o oktávu dolů.

        Args:
            root_voicing: Základní voicing akordu

        Returns:
            List[int]: MIDI noty v Drop 2 voicingu
        """
        # Pro triády (3 noty) nemá Drop 2 smysl, vrací root voicing
        if len(root_voicing) < 4:
            logger.debug("Drop 2 není vhodný pro triády, použiji root voicing")
            return root_voicing

        # Vytvoří kopii pro úpravu
        drop2_voicing = root_voicing.copy()

        # Najde druhý nejvyšší tón (předposlední v seřazeném seznamu)
        sorted_notes = sorted(drop2_voicing)
        second_highest = sorted_notes[-2]

        # Najde index druhého nejvyššího tónu v původním voicingu
        second_highest_index = drop2_voicing.index(second_highest)

        # Posune druhý nejvyšší tón o oktávu dolů
        drop2_voicing[second_highest_index] = second_highest - 12

        # Seřadí noty vzestupně pro správné zobrazení
        drop2_voicing.sort()

        logger.debug(f"Drop 2 voicing: {root_voicing} -> {drop2_voicing}")
        return drop2_voicing

    @classmethod
    def get_chord_info_summary(cls, chord_name: str) -> str:
        """
        Vytvoří textové shrnutí informací o akordu.
        Užitečné pro zobrazení nebo export.

        Args:
            chord_name: Název akordu

        Returns:
            str: Textové shrnutí vlastností akordu
        """
        try:
            analysis = cls.analyze_chord_name(chord_name)

            summary = f"Akord: {analysis['chord_name']}\n"
            summary += f"Noty: {', '.join(analysis['chord_notes'])}\n"
            summary += f"Intervaly: {analysis['chord_intervals']}\n"
            summary += f"MIDI noty: {analysis['midi_notes']}\n"

            if analysis['real_progressions']:
                summary += f"Počet progresí v databázi: {len(analysis['real_progressions'])}\n"
            else:
                summary += "Žádné progrese v databázi nenalezeny\n"

            return summary

        except Exception as e:
            return f"Chyba při analýze akordu {chord_name}: {e}"

    @classmethod
    def batch_analyze_chords(cls, chord_names: List[str], database_manager=None) -> Dict[str, Dict[str, Any]]:
        """
        Analyzuje více akordů najednou.
        Užitečné pro analýzu celých progresí.

        Args:
            chord_names: Seznam názvů akordů
            database_manager: Instance ProgressionManager

        Returns:
            Dict[str, Dict[str, Any]]: Slovník s výsledky analýzy pro každý akord
        """
        results = {}
        logger.info(f"Spouštím batch analýzu pro {len(chord_names)} akordů")

        for chord_name in chord_names:
            try:
                results[chord_name] = cls.analyze_chord_name(chord_name, database_manager)
            except Exception as e:
                logger.error(f"Chyba při analýze akordu {chord_name}: {e}")
                results[chord_name] = {
                    "error": str(e),
                    "chord_name": chord_name
                }

        logger.info(f"Batch analýza dokončena: {len(results)} výsledků")
        return results

    @classmethod
    def compare_chords(cls, chord1: str, chord2: str) -> Dict[str, Any]:
        """
        Porovná dva akordy a najde společné/rozdílné vlastnosti.

        Args:
            chord1: První akord
            chord2: Druhý akord

        Returns:
            Dict[str, Any]: Výsledky porovnání
        """
        try:
            analysis1 = cls.analyze_chord_name(chord1)
            analysis2 = cls.analyze_chord_name(chord2)

            # Porovnání not
            notes1 = set(analysis1['chord_notes'])
            notes2 = set(analysis2['chord_notes'])

            common_notes = list(notes1.intersection(notes2))
            different_notes1 = list(notes1.difference(notes2))
            different_notes2 = list(notes2.difference(notes1))

            # Porovnání intervalů
            intervals1 = set(analysis1['chord_intervals'])
            intervals2 = set(analysis2['chord_intervals'])

            return {
                "chord1": chord1,
                "chord2": chord2,
                "common_notes": common_notes,
                "different_notes": {
                    chord1: different_notes1,
                    chord2: different_notes2
                },
                "common_intervals": list(intervals1.intersection(intervals2)),
                "different_intervals": {
                    chord1: list(intervals1.difference(intervals2)),
                    chord2: list(intervals2.difference(intervals1))
                },
                "similarity_score": len(common_notes) / max(len(notes1), len(notes2))
            }

        except Exception as e:
            logger.error(f"Chyba při porovnání akordů {chord1} a {chord2}: {e}")
            return {"error": str(e)}


def midi_to_key_number(midi_note: int, base_octave_midi_start: int = 21) -> int:
    """
    Převede MIDI číslo na číslo klávesy pro zobrazení na klaviatuře.
    A0 (MIDI 21) = klávesa číslo 0.
    Nezávislá utility funkce.

    Args:
        midi_note: MIDI číslo noty (21-108 pro 88klávesovou klaviaturu)
        base_octave_midi_start: MIDI číslo první klávesy (A0 = 21)

    Returns:
        int: Číslo klávesy pro zobrazení (0-87)
    """
    return midi_note - base_octave_midi_start


def key_number_to_midi(key_number: int, base_octave_midi_start: int = 21) -> int:
    """
    Převede číslo klávesy na MIDI číslo.
    Inverzní funkce k midi_to_key_number.

    Args:
        key_number: Číslo klávesy (0-87)
        base_octave_midi_start: MIDI číslo první klávesy (A0 = 21)

    Returns:
        int: MIDI číslo noty
    """
    return key_number + base_octave_midi_start


if __name__ == "__main__":
    # Jednoduché testování funkcí
    print("=== Test ChordAnalyzer ===")

    # Test základní analýzy
    print("\n1. Základní analýza:")
    result = ChordAnalyzer.analyze_chord_name("Cmaj7")
    print(f"Cmaj7: {result['chord_notes']}")
    print(f"MIDI: {result['midi_notes']}")

    # Test voicingů
    print("\n2. Test voicingů:")
    root = ChordAnalyzer.get_chord_voicing("C", "maj7", "root")
    print(f"Root voicing: {root}")

    drop2 = ChordAnalyzer.get_chord_voicing("C", "maj7", "drop2")
    print(f"Drop2 voicing: {drop2}")

    # Test batch analýzy
    print("\n3. Batch analýza:")
    batch_result = ChordAnalyzer.batch_analyze_chords(["Cmaj7", "Dm7", "G7"])
    for chord, analysis in batch_result.items():
        if "error" not in analysis:
            print(f"{chord}: {analysis['chord_notes']}")

    # Test porovnání akordů
    print("\n4. Porovnání akordů:")
    comparison = ChordAnalyzer.compare_chords("Cmaj7", "Am7")
    print(f"Společné noty: {comparison['common_notes']}")
    print(f"Podobnost: {comparison['similarity_score']:.2f}")

    # Test utility funkcí
    print("\n5. MIDI <-> Key konverze:")
    print(f"MIDI 60 -> Key: {midi_to_key_number(60)}")
    print(f"Key 39 -> MIDI: {key_number_to_midi(39)}")
