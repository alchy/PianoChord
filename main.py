import tkinter as tk


PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
WHITE_KEYS = ["C", "D", "E", "F", "G", "A", "B"]
BLACK_KEYS = ["C#", "D#", "F#", "G#", "A#"]

NUMBER_OF_OCTAVES = 5
ARCHETYPE_SIZE = NUMBER_OF_OCTAVES * 12

WHITE_KEY_WIDTH = 30
WHITE_KEY_HEIGHT = 150
BLACK_KEY_WIDTH = 20
BLACK_KEY_HEIGHT = 100

CHORD_VOICINGS = {
    'maj': [0, 4, 7],              # Major triad
    'maj7': [0, 4, 7, 11],         # Major 7th chord
    'maj9': [0, 4, 7, 11, 14],     # Major 9th chord
    'maj11': [0, 4, 7, 11, 14, 17],# Major 11th chord
    'maj13': [0, 4, 7, 11, 14, 17, 21], # Major 13th chord
    'm': [0, 3, 7],                # Minor triad
    'm7': [0, 3, 7, 10],           # Minor 7th chord
    'm9': [0, 3, 7, 10, 14],       # Minor 9th chord
    'm11': [0, 3, 7, 10, 14, 17],  # Minor 11th chord
    'm13': [0, 3, 7, 10, 14, 17, 21], # Minor 13th chord
    '7': [0, 4, 7, 10],            # Dominant 7th chord
    '9': [0, 4, 7, 10, 14],        # Dominant 9th chord
    '11': [0, 4, 7, 10, 14, 17],   # Dominant 11th chord
    '13': [0, 4, 7, 10, 14, 17, 21], # Dominant 13th chord
    'm7b5': [0, 3, 6, 10],         # Minor 7th flat 5 (half-diminished) chord
    'dim': [0, 3, 6],               # Diminished triad
    'dim7': [0, 3, 6, 9],          # Diminished 7th chord
    'aug': [0, 4, 8],              # Augmented triad
    'aug7': [0, 4, 8, 10],         # Augmented 7th chord
    'sus4': [0, 5, 7],             # Suspended 4th chord
    'sus2': [0, 2, 7],             # Suspended 2nd chord
    'add9': [0, 4, 7, 14],         # Add 9 chord
    '6': [0, 4, 7, 9],             # Major 6th chord
    'm6': [0, 3, 7, 9],            # Minor 6th chord
    'm7b9': [0, 3, 7, 10, 13],     # Minor 7th flat 9 chord
    'm9b5': [0, 3, 6, 10, 14],     # Minor 9th flat 5 chord
    'm11b9': [0, 3, 7, 10, 13, 17],# Minor 11th flat 9 chord
    'm13b9': [0, 3, 7, 10, 13, 17, 21], # Minor 13th flat 9 chord
    '7#9': [0, 4, 7, 10, 15],      # Dominant 7th sharp 9 chord (Hendrix chord)
    '7b9': [0, 4, 7, 10, 13],      # Dominant 7th flat 9 chord
    '7#11': [0, 4, 7, 10, 14, 18], # Dominant 7th sharp 11 chord
    '7b13': [0, 4, 7, 10, 21],     # Dominant 7th flat 13 chord
    '7sus4': [0, 5, 7, 10],        # Dominant 7th suspended 4th chord
    '7sus2': [0, 2, 7, 10],        # Dominant 7th suspended 2nd chord
    '9#11': [0, 4, 7, 10, 14, 18], # Dominant 9th sharp 11 chord
    '13#11': [0, 4, 7, 10, 14, 18, 21], # Dominant 13th sharp 11 chord
    '7b9#5': [0, 4, 8, 10, 13],    # Dominant 7th flat 9 sharp 5 chord
    '7b9b5': [0, 4, 6, 10, 13],    # Dominant 7th flat 9 flat 5 chord
}

common_progressions = {
    'I': ['maj', 'maj7', 'maj9', 'maj11', 'maj13'],
    'ii': ['m', 'm7', 'm9', 'm11', 'm13'],
    'iii': ['m', 'm7', 'm9', 'm11', 'm13'],
    'IV': ['maj', 'maj7', 'maj9', 'maj11', 'maj13'],
    'V': ['7', '9', '11', '13', '7#9', '13#11'],
    'vi': ['m', 'm7', 'm9', 'm11', 'm13'],
    'vii': ['m7b5', 'm9b5', 'dim', 'dim7'],
    'II': ['maj', 'maj7', 'maj9', 'maj11', 'maj13'],
    'III': ['maj', 'maj7', 'maj9', 'maj11', 'maj13'],
    'VI': ['maj', 'maj7', 'maj9', 'maj11', 'maj13'],
    'VII': ['m7b5', 'm9b5', 'dim', 'dim7', 'm11b9']
}


class ArchetypeKeyboard:
    def __init__(self, nr_of_keys):
        self.nr_of_keys = nr_of_keys
        self.note = []
        for i in range(self.nr_of_keys):
            self.note.append(PianoKey(i))

    def draw(self, keys_to_play):
        # Draw white keys
        for i in range(self.nr_of_keys):
            note = PianoKey(i)
            if not note.sharp:
                fill_color = "red" if i in keys_to_play else note.fill
                canvas.create_rectangle(note.bbox, fill=fill_color, outline="black", tags="notes")

        # Draw black keys
        for i in range(self.nr_of_keys):
            note = PianoKey(i)
            if note.sharp:
                fill_color = "red" if i in keys_to_play else note.fill
                canvas.create_rectangle(note.bbox, fill=fill_color, outline="black", tags="notes")


class PianoKey:
    def __init__(self, key_nr):
        self.key_nr = key_nr
        self.relative_key_nr = self.key_nr % 12
        self.key_desc = self.assign_key_description()
        self.octave = key_nr // 12
        self.relative_key_nr = key_nr % 12
        self.active = False

        x_offsets = {
            0: 0,    # White Key
            1: WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2,   # Black Key 1
            2: WHITE_KEY_WIDTH,   # White Key 1
            3: 2 * WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2,   # Black Key 2
            4: 2 * WHITE_KEY_WIDTH,   # White Key 2
            5: 3 * WHITE_KEY_WIDTH,   # White Key 3
            6: 4 * WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2,   # Black Key 3
            7: 4 * WHITE_KEY_WIDTH,   # White Key 4
            8: 5 * WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2,   # Black Key 4
            9: 5 * WHITE_KEY_WIDTH,   # White Key 5
            10: 6 * WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2,  # Black Key 5
            11: 6 * WHITE_KEY_WIDTH   # White Key 6
        }

        x_offset = x_offsets.get(self.relative_key_nr, 0)
        x1 = self.octave * (7 * WHITE_KEY_WIDTH) + x_offset
        x2 = x1 + (WHITE_KEY_WIDTH if self.relative_key_nr % 12 in {0, 2, 4, 5, 7, 9, 11} else BLACK_KEY_WIDTH)
        y2 = WHITE_KEY_HEIGHT if self.relative_key_nr % 12 in {0, 2, 4, 5, 7, 9, 11} else BLACK_KEY_HEIGHT

        self.fill = "white" if y2 == WHITE_KEY_HEIGHT else "black"
        self.sharp = self.fill == "black"

        y1 = 0
        self.bbox = (x1, y1, x2, y2)

    def assign_key_description(self):
        # Map relative key numbers to key descriptions
        key_descriptions = {
            0: "C",
            1: "C#",
            2: "D",
            3: "D#",
            4: "E",
            5: "F",
            6: "F#",
            7: "G",
            8: "G#",
            9: "A",
            10: "A#",
            11: "B"
        }
        return key_descriptions[self.relative_key_nr]


def get_scale(base_note, scale):
    # Define the intervals for different scales
    if scale == 'major':
        intervals = [2, 2, 1, 2, 2, 2, 1]
    elif scale == 'melodic_minor':
        intervals = [2, 1, 2, 2, 2, 2, 1]
    elif scale == 'natural_minor':
        intervals = [2, 1, 2, 2, 1, 2, 2]
    elif scale == 'harmonic_minor':
        intervals = [2, 1, 2, 2, 1, 3, 1]
    else:
        raise ValueError("Invalid scale type.")

    # Get the index of the base_note in the PIANO_KEYS list
    base_index = PIANO_KEYS.index(base_note.upper())
    print("[d] base_index: ", base_index)

    # Initialize the scale with the base_note
    scale_enum = [base_note]

    # Generate the scale based on the intervals
    index = base_index
    for interval in intervals:
        index += interval
        scale_enum.append(PIANO_KEYS[index % len(PIANO_KEYS)])

    return scale_enum

def find_chord_progression_degree(chord_name):
    # Iterate through common_progressions to find the progression containing the chord's degrees
    chord_degrees = []
    for progression, degrees in common_progressions.items():
        if chord_name in degrees:
            chord_degrees.append(progression)

    return chord_degrees


def get_chord():
    chord_to_play = chord_entry.get().lower()
    base_note = note_entry.get().upper()  # Convert to uppercase
    scale = scale_type.get()

    print("[d] chord_to_play: ", chord_to_play)
    print("[d] base_note: ", base_note)
    print("[d] scale: ", scale)

    if chord_to_play in CHORD_VOICINGS:
        # get base_index (numeric offset of the base key) from the base_not entered by user
        base_index = PIANO_KEYS.index(base_note) if base_note in PIANO_KEYS else None
        if base_index is not None:
            # get relative numeric list of keys to play, add base_index all keys_to_play to get absolute number position
            keys_to_play = [key + base_index for key in CHORD_VOICINGS[chord_to_play]]
            # redraw all keys
            archetype.draw(keys_to_play)
            #
            for i in keys_to_play:
                print("[d] key_desc: ", archetype.note[i].key_desc)
        else:
            print("Base note not found in piano keys.")
    else:
        print("Chord not found in dictionary")

    print("[d] chord_progression_degree: ", find_chord_progression_degree(chord_to_play))


def loop():
    # Schedule loop again after 1000 milliseconds (1 second)
    root.after(100, loop)


root = tk.Tk()
root.title("Piano Keyboard")

canvas = tk.Canvas(root, width=800, height=400)
canvas.grid(row=0, column=0, columnspan=2)

# Init Archetype
archetype = ArchetypeKeyboard(ARCHETYPE_SIZE)

# Create entry field for chord input
chord_label = tk.Label(root, text="Chord:")
chord_label.grid(row=1, column=0, sticky="e")
chord_entry = tk.Entry(root)
chord_entry.grid(row=1, column=1, sticky="w")

# Create entry field for base note input
note_label = tk.Label(root, text="Base Note:")
note_label.grid(row=2, column=0, sticky="e")
note_entry = tk.Entry(root)
note_entry.grid(row=2, column=1, sticky="w")

# Create radio buttons for selecting scale type
scale_type_label = tk.Label(root, text="Scale Type:")
scale_type_label.grid(row=3, column=0, sticky="e")

scale_type = tk.StringVar()
scale_type.set("major")  # Default scale type
scale_type_frame = tk.Frame(root)
scale_type_frame.grid(row=3, column=1, sticky="w")
major_scale_radio = tk.Radiobutton(scale_type_frame, text="Major", variable=scale_type, value="major")
major_scale_radio.grid(row=0, column=0)
melodic_minor_scale_radio = tk.Radiobutton(scale_type_frame, text="Melodic Minor", variable=scale_type, value="melodic_minor")
melodic_minor_scale_radio.grid(row=0, column=1)
natural_minor_scale_radio = tk.Radiobutton(scale_type_frame, text="Natural Minor", variable=scale_type, value="natural_minor")
natural_minor_scale_radio.grid(row=0, column=2)
harmonic_minor_scale_radio = tk.Radiobutton(scale_type_frame, text="Harmonic Minor", variable=scale_type, value="harmonic_minor")
harmonic_minor_scale_radio.grid(row=0, column=3)

# Create button to trigger chord drawing
chord_button = tk.Button(root, text="Draw Chord", command=get_chord)
chord_button.grid(row=4, column=0, columnspan=2)

# Start the loop
loop()

root.mainloop()
