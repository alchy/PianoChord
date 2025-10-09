# Training Mode - Specifikace a Koncept

## Přehled
Training Mode je interaktivní režim pro trénink rozpoznávání a hraní akordů na MIDI klaviatuře.

## Technické požadavky

### 1. MIDI Input/Output
- **MIDI Port Out** (přejmenováno z "MIDI Port"): Pro přehrávání akordů aplikací
- **MIDI Port In** (nový): Pro příjem MIDI zpráv z klaviatury uživatele
  - Výběr z dostupných MIDI input portů
  - Automatický výběr prvního dostupného portu
  - Dropdown menu pro výběr jiného portu
  - **Pokud MIDI Port In není dostupný → celá Training funkce bude zašedivělá (disabled)**

### 2. GUI Struktura

#### Hlavní okno - změny:
```
[Chord Analysis]
  - Chord: [______] [Analyze] [Chord-Scale Info]
  - Voicing: (Root) (Smooth) (Drop2)

[MIDI]
  - [x] Play MIDI
  - Velocity: [====64====]
  - MIDI Port Out: [Microsoft GS Wavetable...▼]  <- PŘEJMENOVÁNO
  - MIDI Port In:  [USB MIDI Device...▼]         <- NOVÉ
  - [Start Training]                              <- NOVÉ TLAČÍTKO
```

#### Training okno (samostatné):
```
┌─────────────────────────────────────────────────┐
│ Training Mode - Chord Recognition               │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │   [Piano Keyboard Visualization]       │     │
│  │   (88 keys)                             │     │
│  └────────────────────────────────────────┘     │
│                                                  │
│  Target Chord: [  Dm7  ]  <-- Velké zobrazení  │
│                                                  │
│  Status: [Waiting for input...]                │
│         nebo [Try Again!]                       │
│         nebo [Correct! ✓]                       │
│                                                  │
│  Score: 8/16 (50%)                              │
│  Current Level: Intermediate (4-note chords)   │
│                                                  │
│  [Next Chord] [Skip] [Show Answer] [Exit]     │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Funkční Workflow

### 3. Logika Training Mode

#### Inicializace:
1. Uživatel stiskne "Start Training" v hlavním okně
2. Kontrola dostupnosti MIDI Port In:
   - Pokud není dostupný → zobrazit chybovou zprávu
   - Pokud je dostupný → otevřít Training okno

3. Training okno se inicializuje:
   - Načte session state (pokud existuje)
   - Vygeneruje první akord podle obtížnosti

#### Difficulty Levels (postupný růst):
```python
TRAINING_LEVELS = {
    "Beginner": {
        "chord_types": ["maj", "m"],  # Pouze triády
        "required_correct": 5,
        "name": "Triads (3 notes)"
    },
    "Elementary": {
        "chord_types": ["maj7", "m7", "7"],
        "required_correct": 8,
        "name": "Seventh Chords (4 notes)"
    },
    "Intermediate": {
        "chord_types": ["maj9", "m9", "9", "6", "m6"],
        "required_correct": 10,
        "name": "Extended Chords"
    },
    "Advanced": {
        "chord_types": ["7b9", "7#9", "m7b5", "dim7", "maj13"],
        "required_correct": 12,
        "name": "Altered & Complex Chords"
    }
}
```

#### Chord Selection Algorithm:
```python
def select_next_chord(self, previous_chord=None, session_history=[]):
    """
    Vybere další akord pro trénink.

    Priorita:
    1. Harmonická kontinuita (z databáze progresí)
    2. Nepoužité akordy v této session
    3. Aktuální difficulty level
    4. Náhodný výběr z dostupných
    """

    # Pokud existuje předchozí akord, hledej progrese
    if previous_chord:
        candidates = find_progressions_from_chord(previous_chord)
        # Filtruj podle difficulty
        candidates = filter_by_difficulty(candidates, current_level)
        # Odstraň už použité
        candidates = remove_used_chords(candidates, session_history)

        if candidates:
            return weighted_random_choice(candidates)

    # Fallback: náhodný akord z aktuální difficulty
    return random_chord_from_level(current_level)
```

### 4. MIDI Input Processing

#### Event Flow:
```
User presses key on MIDI keyboard
         ↓
MIDI Port In receives NOTE_ON event
         ↓
Application plays the note back via MIDI Port Out (instant feedback)
         ↓
Application adds note to current_chord_buffer[]
         ↓
Check if buffer has expected number of notes (3, 4, 5...)
         ↓
YES → Analyze chord
         ↓
Compare with target chord
         ↓
Match? → Display "Correct!" → Next chord
         ↓
No match? → attempt_count++
         ↓
attempt_count == 1? → Display "Try Again!"
         ↓
attempt_count == 2? → Show answer (highlight keys in yellow)
                    → Allow retry or next chord
```

#### Chord Recognition Logic:
```python
def recognize_played_chord(self, midi_notes: List[int], target_chord: str) -> bool:
    """
    Rozpozná, zda zahraný akord odpovídá cílovému.

    Pravidla:
    - Akord může být v jakémkoli obratu (inversion)
    - Akord může být v jakékoli oktávě
    - Počet not musí odpovídat definici akordu
    - Noty musí odpovídat intervalové struktuře

    Returns:
        True pokud je akord správný (v jakémkoli tvaru)
    """
    target_notes = get_chord_notes_normalized(target_chord)
    played_notes = normalize_to_pitch_classes(midi_notes)

    return set(played_notes) == set(target_notes)
```

### 5. Scoring System

```python
class TrainingSession:
    def __init__(self):
        self.correct_count = 0
        self.total_attempts = 0
        self.chords_played = []
        self.current_level = "Beginner"
        self.start_time = time.time()

    def record_attempt(self, chord: str, correct: bool, attempts: int):
        """Zaznamenává pokus o zahrání akordu."""
        self.total_attempts += attempts
        if correct:
            self.correct_count += 1

        self.chords_played.append({
            'chord': chord,
            'correct': correct,
            'attempts': attempts,
            'timestamp': time.time()
        })

        # Kontrola postupu na další level
        self.check_level_progression()

    def get_score_percentage(self) -> float:
        """Vrací úspěšnost v procentech."""
        if self.total_attempts == 0:
            return 0.0
        return (self.correct_count / self.total_attempts) * 100

    def check_level_progression(self):
        """Kontroluje, zda má uživatel postoupit na další level."""
        current_level_data = TRAINING_LEVELS[self.current_level]

        # Počet správných v řadě za posledních N pokusů
        recent = self.chords_played[-10:]
        correct_in_row = sum(1 for c in recent if c['correct'] and c['attempts'] == 1)

        if correct_in_row >= current_level_data['required_correct']:
            self.level_up()
```

### 6. Visual Feedback

#### States klaviatury:
1. **Default** - šedá/bílá/černá (normální stav)
2. **Playing** - zelená (uživatel právě hraje notu)
3. **Correct** - zelená s checkmark (správný akord)
4. **Hint** - žlutá (nápověda po 2. neúspěšném pokusu)
5. **Wrong** - červené bliknutí (špatný akord)

#### Status messages:
- `"Play the chord: Dm7"` - výzva
- `"Waiting for input..."` - čeká na MIDI
- `"Try again!"` - první neúspěch (červený text)
- `"Correct! ✓"` - úspěch (zelený text)
- `"Showing answer..."` - zobrazena nápověda (žlutý text)

## Implementační Fáze

### Fáze 1: MIDI Input Setup
- [ ] Přidat MIDI input port selection do `midi_playback.py`
- [ ] Upravit GUI pro MIDI Port In/Out
- [ ] Implementovat callback pro MIDI input events

### Fáze 2: Training Core Logic
- [ ] Vytvořit `training_mode.py` s třídou `TrainingSession`
- [ ] Implementovat chord selection algorithm
- [ ] Implementovat chord recognition logic

### Fáze 3: Training GUI
- [ ] Vytvořit samostatné Training okno
- [ ] Implementovat keyboard visualization
- [ ] Přidat status display a scoring

### Fáze 4: Integration & Testing
- [ ] Propojit MIDI input s chord recognition
- [ ] Testovat různé MIDI klaviatury
- [ ] Ladit obtížnost levelů

## Technické poznámky

### MIDI Input Handling (mido):
```python
import mido

def setup_midi_input(port_name):
    """Nastaví MIDI input port a callback."""
    inport = mido.open_input(port_name, callback=on_midi_message)
    return inport

def on_midi_message(message):
    """Zpracuje příchozí MIDI zprávu."""
    if message.type == 'note_on':
        # Play note via output
        play_note_feedback(message.note, message.velocity)

        # Add to buffer
        add_note_to_buffer(message.note)

        # Check if chord complete
        check_chord_completion()

    elif message.type == 'note_off':
        # Remove from buffer
        remove_note_from_buffer(message.note)
```

### Harmonická Kontinuita:
- Využívá existující `database.json` pro hledání progresí
- Preferuje akordy, které následují v běžných jazz progressions
- Fallback na náhodný výběr pokud není nalezena progrese

### Session Persistence (volitelné pro budoucnost):
```json
{
  "session_id": "2025-01-09-15-30",
  "current_level": "Elementary",
  "score": {"correct": 8, "total": 16},
  "chords_history": [
    {"chord": "C", "correct": true, "attempts": 1},
    {"chord": "Dm7", "correct": false, "attempts": 2}
  ]
}
```

## UI/UX Considerations

1. **Accessibility**:
   - Velké, čitelné písmo pro Target Chord
   - Barevné rozlišení pro různé stavy
   - Klávesové zkratky (Space = Next, Enter = Retry)

2. **Motivation**:
   - Progress bar pro level advancement
   - Gratulace při level up
   - Statistiky po session (čas, úspěšnost, nejtěžší akordy)

3. **Flexibility**:
   - Možnost přeskočit akord (Skip)
   - Možnost zobrazit nápovědu kdykoliv (Show Answer)
   - Možnost reset session

## Budoucí Rozšíření

- [ ] Multiple choice mode (vybrat ze 4 možností)
- [ ] Time challenge mode (co nejvíc akordů za 2 minuty)
- [ ] Custom training sets (pouze m7b5, jen alterované dominanty, atd.)
- [ ] Voice leading training (hrát smooth voice leading mezi akordy)
- [ ] Export statistik do CSV/PDF
