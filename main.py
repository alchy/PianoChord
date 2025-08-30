import tkinter as tk
from typing import List, Dict, Tuple, Optional


class MusicalConstants:
    """Konstanty pro hudební teorii"""
    PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    WHITE_KEYS = ["C", "D", "E", "F", "G", "A", "B"]
    BLACK_KEYS = ["C#", "D#", "F#", "G#", "A#"]

    NUMBER_OF_OCTAVES = 5
    ARCHETYPE_SIZE = NUMBER_OF_OCTAVES * 12

    WHITE_KEY_WIDTH = 30
    WHITE_KEY_HEIGHT = 150
    BLACK_KEY_WIDTH = 20
    BLACK_KEY_HEIGHT = 100


class ChordLibrary:
    """Knihovna akordů a jejich voicingů"""

    CHORD_VOICINGS = {
        'maj': [0, 4, 7],  # Major triad
        'maj7': [0, 4, 7, 11],  # Major 7th chord
        'maj9': [0, 4, 7, 11, 14],  # Major 9th chord
        'm': [0, 3, 7],  # Minor triad
        'm7': [0, 3, 7, 10],  # Minor 7th chord
        'm9': [0, 3, 7, 10, 14],  # Minor 9th chord
        '7': [0, 4, 7, 10],  # Dominant 7th chord
        '9': [0, 4, 7, 10, 14],  # Dominant 9th chord
        '13': [0, 4, 7, 10, 14, 17, 21],  # Dominant 13th chord
        'm7b5': [0, 3, 6, 10],  # Minor 7th flat 5 (half-diminished)
        'dim': [0, 3, 6],  # Diminished triad
        'dim7': [0, 3, 6, 9],  # Diminished 7th chord
        'sus4': [0, 5, 7],  # Suspended 4th chord
        'sus2': [0, 2, 7],  # Suspended 2nd chord
        '6': [0, 4, 7, 9],  # Major 6th chord
        'm6': [0, 3, 7, 9],  # Minor 6th chord
    }


class ScaleTheory:
    """Třída pro práci se stupnicemi a stupni"""

    SCALE_INTERVALS = {
        'major': [2, 2, 1, 2, 2, 2, 1],
        'melodic_minor': [2, 1, 2, 2, 2, 2, 1],
        'natural_minor': [2, 1, 2, 2, 1, 2, 2],
        'harmonic_minor': [2, 1, 2, 2, 1, 3, 1]
    }

    # Nejčastější jazzové progrese pro dur a moll
    JAZZ_PROGRESSIONS = {
        'major': {
            'I': [['vi', 'IV'], ['V', 'vi'], ['ii', 'V']],
            'ii': [['V', 'I'], ['vi', 'V'], ['iii', 'vi']],
            'iii': [['vi', 'ii'], ['IV', 'V'], ['vi', 'IV']],
            'IV': [['V', 'I'], ['ii', 'V'], ['vi', 'iii']],
            'V': [['I', 'vi'], ['vi', 'IV'], ['I', 'IV']],
            'vi': [['ii', 'V'], ['IV', 'V'], ['iii', 'IV']],
            'vii': [['I', 'vi'], ['iii', 'vi'], ['V', 'I']]
        },
        'minor': {
            'i': [['iv', 'V'], ['VI', 'VII'], ['ii', 'V']],
            'ii': [['V', 'i'], ['iv', 'V'], ['VII', 'i']],
            'III': [['VI', 'ii'], ['iv', 'V'], ['VII', 'i']],
            'iv': [['V', 'i'], ['ii', 'V'], ['VII', 'III']],
            'V': [['i', 'iv'], ['VI', 'iv'], ['i', 'VII']],
            'VI': [['ii', 'V'], ['iv', 'V'], ['VII', 'i']],
            'VII': [['i', 'iv'], ['III', 'VI'], ['V', 'i']]
        }
    }

    # Mapování akordů na stupně pro dur
    MAJOR_DEGREE_CHORDS = {
        'I': ['maj', 'maj7', 'maj9', '6'],
        'ii': ['m', 'm7', 'm9'],
        'iii': ['m', 'm7', 'm9'],
        'IV': ['maj', 'maj7', 'maj9', '6'],
        'V': ['7', '9', '13', 'sus4'],
        'vi': ['m', 'm7', 'm9', 'm6'],
        'vii': ['m7b5', 'dim', 'dim7']
    }

    # Mapování akordů na stupně pro moll
    MINOR_DEGREE_CHORDS = {
        'i': ['m', 'm7', 'm9', 'm6'],
        'ii': ['m7b5', 'dim'],
        'III': ['maj', 'maj7', 'maj9'],
        'iv': ['m', 'm7', 'm9'],
        'V': ['7', '9', 'm', 'm7'],  # V může být dur i moll v mollu
        'VI': ['maj', 'maj7', 'maj9'],
        'VII': ['maj', 'maj7', 'maj9']
    }

    @classmethod
    def get_scale_notes(cls, base_note: str, scale_type: str) -> List[str]:
        """Vrátí noty ve stupnici"""
        intervals = cls.SCALE_INTERVALS[scale_type]
        base_index = MusicalConstants.PIANO_KEYS.index(base_note.upper())

        scale_notes = [base_note.upper()]
        index = base_index
        for interval in intervals:
            index += interval
            scale_notes.append(MusicalConstants.PIANO_KEYS[index % len(MusicalConstants.PIANO_KEYS)])

        return scale_notes

    @classmethod
    def find_chord_degree(cls, chord_type: str, scale_type: str) -> Optional[str]:
        """Najde stupeň akordu v dané stupnici"""
        if scale_type in ['major']:
            degree_map = cls.MAJOR_DEGREE_CHORDS
        else:  # minor scales
            degree_map = cls.MINOR_DEGREE_CHORDS

        for degree, chords in degree_map.items():
            if chord_type in chords:
                return degree
        return None

    @classmethod
    def suggest_progressions(cls, current_degree: str, scale_type: str) -> List[List[str]]:
        """Navrhne dvě nejčastější progrese od daného stupně"""
        progression_type = 'major' if scale_type == 'major' else 'minor'

        if current_degree in cls.JAZZ_PROGRESSIONS[progression_type]:
            return cls.JAZZ_PROGRESSIONS[progression_type][current_degree][:2]  # Vrátí první 2 progrese
        return []


class PianoKey:
    """Reprezentuje jednu klávesu na klaviatuře"""

    def __init__(self, key_nr: int):
        self.key_nr = key_nr
        self.relative_key_nr = key_nr % 12
        self.octave = key_nr // 12
        self.key_desc = self._assign_key_description()
        self.bbox = self._calculate_bbox()
        self.sharp = self.key_desc in MusicalConstants.BLACK_KEYS
        self.fill = "black" if self.sharp else "white"

    def _assign_key_description(self) -> str:
        """Přiřadí název klávesy"""
        return MusicalConstants.PIANO_KEYS[self.relative_key_nr]

    def _calculate_bbox(self) -> Tuple[int, int, int, int]:
        """Vypočítá pozici a velikost klávesy"""
        x_offsets = {
            0: 0, 1: MusicalConstants.WHITE_KEY_WIDTH - MusicalConstants.BLACK_KEY_WIDTH / 2,
            2: MusicalConstants.WHITE_KEY_WIDTH,
            3: 2 * MusicalConstants.WHITE_KEY_WIDTH - MusicalConstants.BLACK_KEY_WIDTH / 2,
            4: 2 * MusicalConstants.WHITE_KEY_WIDTH, 5: 3 * MusicalConstants.WHITE_KEY_WIDTH,
            6: 4 * MusicalConstants.WHITE_KEY_WIDTH - MusicalConstants.BLACK_KEY_WIDTH / 2,
            7: 4 * MusicalConstants.WHITE_KEY_WIDTH,
            8: 5 * MusicalConstants.WHITE_KEY_WIDTH - MusicalConstants.BLACK_KEY_WIDTH / 2,
            9: 5 * MusicalConstants.WHITE_KEY_WIDTH,
            10: 6 * MusicalConstants.WHITE_KEY_WIDTH - MusicalConstants.BLACK_KEY_WIDTH / 2,
            11: 6 * MusicalConstants.WHITE_KEY_WIDTH
        }

        x_offset = x_offsets.get(self.relative_key_nr, 0)
        x1 = self.octave * (7 * MusicalConstants.WHITE_KEY_WIDTH) + x_offset

        is_white_key = self.relative_key_nr in {0, 2, 4, 5, 7, 9, 11}
        width = MusicalConstants.WHITE_KEY_WIDTH if is_white_key else MusicalConstants.BLACK_KEY_WIDTH
        height = MusicalConstants.WHITE_KEY_HEIGHT if is_white_key else MusicalConstants.BLACK_KEY_HEIGHT

        return (x1, 0, x1 + width, height)


class ArchetypeKeyboard:
    """Hlavní třída klaviatury"""

    def __init__(self, canvas: tk.Canvas, nr_of_keys: int):
        self.canvas = canvas
        self.nr_of_keys = nr_of_keys
        self.keys = [PianoKey(i) for i in range(nr_of_keys)]

    def draw(self, keys_to_highlight: List[int] = None):
        """Nakreslí klaviaturu s volitelným zvýrazněním kláves"""
        if keys_to_highlight is None:
            keys_to_highlight = []

        self.canvas.delete("notes")

        # Nejdřív nakreslí bílé klávesy
        for key in self.keys:
            if not key.sharp:
                fill_color = "red" if key.key_nr in keys_to_highlight else key.fill
                self.canvas.create_rectangle(key.bbox, fill=fill_color, outline="black", tags="notes")

        # Pak černé klávesy (aby byly navrchu)
        for key in self.keys:
            if key.sharp:
                fill_color = "red" if key.key_nr in keys_to_highlight else key.fill
                self.canvas.create_rectangle(key.bbox, fill=fill_color, outline="black", tags="notes")


class HarmonyAnalyzer:
    """Třída pro analýzu harmonií a navrhování progresí"""

    @staticmethod
    def analyze_chord(base_note: str, chord_type: str, scale_type: str) -> Dict:
        """Analyzuje akord a vrátí jeho stupeň a navrhované progrese"""

        # Najdi stupeň akordu
        degree = ScaleTheory.find_chord_degree(chord_type, scale_type)
        if not degree:
            return {"error": f"Akord {chord_type} nebyl nalezen v {scale_type} stupnici"}

        # Získej noty stupnice
        scale_notes = ScaleTheory.get_scale_notes(base_note, scale_type)

        # Navrhni progrese
        progressions = ScaleTheory.suggest_progressions(degree, scale_type)

        return {
            "degree": degree,
            "scale_notes": scale_notes,
            "progressions": progressions,
            "analysis": f"Akord {base_note}{chord_type} je {degree} stupeň v {base_note} {scale_type}"
        }


class PianoApp:
    """Hlavní aplikace"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Piano Harmony Analyzer")

        self._setup_canvas()
        self._setup_controls()
        self._setup_keyboard()

    def _setup_canvas(self):
        """Nastaví canvas pro klaviaturu"""
        self.canvas = tk.Canvas(self.root, width=800, height=400, bg="lightgray")
        self.canvas.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

    def _setup_keyboard(self):
        """Inicializuje klaviaturu"""
        self.keyboard = ArchetypeKeyboard(self.canvas, MusicalConstants.ARCHETYPE_SIZE)
        self.keyboard.draw()

    def _setup_controls(self):
        """Nastaví ovládací prvky"""
        # Akord
        tk.Label(self.root, text="Akord:").grid(row=1, column=0, sticky="e", padx=5)
        self.chord_entry = tk.Entry(self.root, width=10)
        self.chord_entry.grid(row=1, column=1, sticky="w", padx=5)

        # Základní nota
        tk.Label(self.root, text="Základní nota:").grid(row=2, column=0, sticky="e", padx=5)
        self.note_entry = tk.Entry(self.root, width=5)
        self.note_entry.grid(row=2, column=1, sticky="w", padx=5)

        # Typ stupnice
        tk.Label(self.root, text="Stupnice:").grid(row=3, column=0, sticky="e", padx=5)
        self.scale_type = tk.StringVar(value="major")
        scale_frame = tk.Frame(self.root)
        scale_frame.grid(row=3, column=1, sticky="w", padx=5)

        scales = [("Major", "major"), ("Natural Minor", "natural_minor"),
                  ("Harmonic Minor", "harmonic_minor"), ("Melodic Minor", "melodic_minor")]

        for i, (text, value) in enumerate(scales):
            tk.Radiobutton(scale_frame, text=text, variable=self.scale_type,
                           value=value).grid(row=0, column=i, padx=5)

        # Tlačítko pro analýzu
        tk.Button(self.root, text="Analyzovat Harmonii",
                  command=self._analyze_harmony, bg="lightblue").grid(row=4, column=0, columnspan=2, pady=10)

        # Oblast pro výsledky
        self.result_text = tk.Text(self.root, height=8, width=70, wrap=tk.WORD)
        self.result_text.grid(row=5, column=0, columnspan=3, padx=10, pady=5)

        # Scrollbar pro text
        scrollbar = tk.Scrollbar(self.root, command=self.result_text.yview)
        scrollbar.grid(row=5, column=3, sticky="ns")
        self.result_text.config(yscrollcommand=scrollbar.set)

    def _analyze_harmony(self):
        """Hlavní metoda pro analýzu harmonie"""
        try:
            chord_name = self.chord_entry.get().lower().strip()
            base_note = self.note_entry.get().upper().strip()
            scale = self.scale_type.get()

            if not chord_name or not base_note:
                self._show_error("Prosím zadejte akord i základní notu")
                return

            if base_note not in MusicalConstants.PIANO_KEYS:
                self._show_error(f"Neplatná nota: {base_note}")
                return

            if chord_name not in ChordLibrary.CHORD_VOICINGS:
                self._show_error(f"Neznámý akord: {chord_name}")
                return

            # Zobraz akord na klaviatuře
            self._display_chord(base_note, chord_name)

            # Analyzuj harmonii
            analysis = HarmonyAnalyzer.analyze_chord(base_note, chord_name, scale)

            if "error" in analysis:
                self._show_error(analysis["error"])
                return

            # Zobraz výsledky
            self._display_analysis(analysis, base_note, chord_name, scale)

        except Exception as e:
            self._show_error(f"Chyba při analýze: {str(e)}")

    def _display_chord(self, base_note: str, chord_name: str):
        """Zobrazí akord na klaviatuře"""
        base_index = MusicalConstants.PIANO_KEYS.index(base_note)
        keys_to_highlight = [key + base_index for key in ChordLibrary.CHORD_VOICINGS[chord_name]]
        self.keyboard.draw(keys_to_highlight)

    def _display_analysis(self, analysis: Dict, base_note: str, chord_name: str, scale: str):
        """Zobrazí výsledky analýzy"""
        self.result_text.delete(1.0, tk.END)

        result = f"🎵 ANALÝZA HARMONIE 🎵\n"
        result += f"{'=' * 50}\n\n"

        result += f"Akord: {base_note}{chord_name}\n"
        result += f"Stupnice: {base_note} {scale}\n"
        result += f"Stupeň: {analysis['degree']}\n\n"

        result += f"Noty ve stupnici: {' - '.join(analysis['scale_notes'])}\n\n"

        if analysis['progressions']:
            result += f"🎼 NAVRHOVANÉ JAZZOVÉ PROGRESE:\n"
            result += f"{'-' * 40}\n"

            for i, progression in enumerate(analysis['progressions'], 1):
                result += f"\nProgrese {i}: {analysis['degree']} → {progression[0]} → {progression[1]}\n"

                # Převeď stupně na konkrétní akordy
                prog_chords = self._degrees_to_chords(progression, analysis['scale_notes'], scale)
                result += f"Konkrétně: {base_note}{chord_name} → {prog_chords[0]} → {prog_chords[1]}\n"
        else:
            result += "❌ Pro tento akord nebyly nalezeny typické jazzové progrese.\n"

        self.result_text.insert(tk.END, result)

    def _degrees_to_chords(self, progression: List[str], scale_notes: List[str], scale_type: str) -> List[str]:
        """Převede stupně na konkrétní akordy"""
        result = []

        degree_map = ScaleTheory.MAJOR_DEGREE_CHORDS if scale_type == 'major' else ScaleTheory.MINOR_DEGREE_CHORDS

        for degree in progression:
            if degree in degree_map:
                # Vezmi první (nejčastější) akord pro daný stupeň
                chord_type = degree_map[degree][0]

                # Najdi pozici stupně v stupnici
                degree_romans = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii'] if scale_type == 'major' else \
                    ['i', 'ii', 'III', 'iv', 'V', 'VI', 'VII']

                if degree in degree_romans:
                    degree_index = degree_romans.index(degree)
                    note = scale_notes[degree_index]
                    result.append(f"{note}{chord_type}")
                else:
                    result.append(f"?{chord_type}")
            else:
                result.append("?")

        return result

    def _show_error(self, message: str):
        """Zobrazí chybovou zprávu"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"❌ CHYBA: {message}")

    def run(self):
        """Spustí aplikaci"""
        # Nastav výchozí hodnoty
        self.chord_entry.insert(0, "maj7")
        self.note_entry.insert(0, "C")

        self.root.mainloop()


def main():
    """Hlavní funkce programu"""
    app = PianoApp()
    app.run()


if __name__ == "__main__":
    main()