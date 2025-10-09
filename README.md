# Piano Chord Analyzer - Jazz Training Edition

Aplikace pro analýzu a trénink jazzových akordických progresí. Navrženo pro hráče klavíru a studenty jazzu, kteří chtějí zlepšit své porozumění akordům, voicingům a progresím.

## Funkce

### Základní funkce
- **Analýza akordů**: Zadejte název akordu a zobrazí se na virtuální klaviatuře
- **MIDI přehrávání**: Slyšte akordy v reálném čase přes MIDI výstup
- **Vyhledávání progresí**: Najděte skladby obsahující zadaný akord
- **Progression Player**: Procházejte a přehrávejte akordové progrese z databáze

### Voicing typy
- **Root position**: Základní pozice akordu
- **Smooth voicing**: Minimalizuje pohyb mezi akordy (voice leading)
- **Drop-2 voicing**: Profesionální jazzový voicing

### Jazz Theory funkce
- **Detekce sekundárních dominant**: Automatická identifikace V/X akordů
- **Transponovaná databáze**: Všechny progrese dostupné ve všech tóninách
- **Anotace funkcí**: Zobrazení harmonických funkcí akordů
- **Play Secondary Dominant**: Přehrání sekundární dominanty k aktuálnímu akordu

## Instalace

### Požadavky
- Python 3.8 nebo novější
- Tkinter (obvykle součást Pythonu)
- MIDI výstup (volitelné, ale doporučené pro plnou funkcionalitu)

### Kroky instalace

1. **Klonování repozitáře**
```bash
git clone <repository-url>
cd PianoChord
```

2. **Vytvoření virtuálního prostředí** (doporučeno)
```bash
python -m venv .venv
```

3. **Aktivace virtuálního prostředí**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Instalace závislostí**
```bash
pip install -r requirements.txt
```

5. **Spuštění aplikace**
```bash
python gui.py
```

## Struktura projektu

```
PianoChord/
├── config.py              # Konfigurace: konstanty, stupnice, akordy
├── music_analytics.py     # Hudební logika: analýza, voicing, transpozice
├── midi_playback.py       # MIDI přehrávání a správa portů
├── gui.py                 # GUI: klaviatura, ovládací prvky, zobrazení
├── database.json          # Databáze jazzových progresí
├── requirements.txt       # Python závislosti
├── README.md              # Tento soubor
└── main.py                # (Archivováno - starší monolitická verze)
```

## Použití

### Základní workflow

1. **Analýza jednotlivého akordu**
   - Zadejte název akordu (např. `Dm7`, `G7b9`, `Cmaj7`)
   - Klikněte na "Analyze" nebo stiskněte Enter
   - Akord se zobrazí na klaviatuře a přehraje přes MIDI
   - V dolní části se zobrazí skladby obsahující tento akord

2. **Procházení progresí**
   - Double-click na progresi v záložce "Chord Analysis"
   - Progrese se načte do "Progression Player"
   - Používejte tlačítka "<< Previous" a "Next >>" pro navigaci
   - Nebo použijte klávesové zkratky:
     - **Left/Right arrow**: Navigace s přehráním MIDI
     - **Up/Down arrow**: Tichá navigace (bez MIDI)
     - **Enter**: Přehrát aktuální akord

3. **Experiment s voicingem**
   - Vyberte voicing typ: Root, Smooth, nebo Drop2
   - Stejný akord zazní rozdílně podle vybraného voicingu
   - Smooth voicing je vhodný pro poslech voice leadingu

4. **Sekundární dominanty**
   - Po načtení progrese klikněte "Play Sec Dom"
   - Přehraje sekundární dominantu k aktuálnímu akordu
   - Červeně zvýrazněné anotace (např. "V7/ii") indikují sekundární dominanty

### Klávesové zkratky

| Klávesa | Akce |
|---------|------|
| Enter | Analyzovat akord / Přehrát aktuální akord z progrese |
| Left Arrow | Předchozí akord (s MIDI) |
| Right Arrow | Následující akord (s MIDI) |
| Up Arrow | Předchozí akord (bez MIDI) |
| Down Arrow | Následující akord (bez MIDI) |

### Formát akordů

Aplikace rozpoznává následující typy akordů:

**Durové:**
- `C`, `Cmaj`, `Cmaj7`, `Cmaj9`, `C6`

**Mollové:**
- `Cm`, `Cm7`, `Cm9`, `Cm6`, `Cm(maj7)`

**Dominantní:**
- `C7`, `C9`, `C13`

**Alterované:**
- `C7b9`, `C7#9`, `C7b5`, `C7#5`, `C7alt`

**Zmenšené a zvětšené:**
- `Cdim`, `Cdim7`, `Cm7b5`, `Caug`

**Suspended:**
- `Csus2`, `Csus4`, `C7sus4`

**Poznámka:** Místo `b` (flat) používejte `#` (sharp) notaci:
- `Db7` → `C#7`
- `Eb` → `D#`

## MIDI nastavení

### Výběr MIDI portu
- V sekci "MIDI" vyberte dostupný MIDI port z dropdown menu
- Aplikace automaticky detekuje dostupné MIDI výstupy

### Velocity nastavení
- Upravte hlasitost MIDI pomocí slideru "Velocity" (0-127)
- Výchozí hodnota: 64

### Bez MIDI výstupu
- Aplikace funguje i bez MIDI
- Odškrtněte "Play MIDI" pro vypnutí MIDI přehrávání
- Akordy se budou pouze vizuálně zobrazovat na klaviatuře

## Databáze progresí

Soubor `database.json` obsahuje kolekci jazzových standardů a progresí:

### Obsah databáze
- **Jazz Standards**: Autumn Leaves, All The Things You Are, Giant Steps, atd.
- **Jazz Progressions**: ii-V-I v různých variacích
- **Latin Jazz**: Blue Bossa, Brazilian Like
- **Bebop**: Now's the Time, Giant Steps changes

### Přidání vlastních progresí

Editujte `database.json` a přidejte novou položku:

```json
"Název skladby": {
    "genre": "jazz-standard",
    "key": "C",
    "composer": "Autor",
    "year": 1960,
    "difficulty": "Medium",
    "progressions": [
        {
            "chords": ["Dm7", "G7", "Cmaj7"],
            "description": "Popis progrese"
        }
    ]
}
```

## Řešení problémů

### MIDI nefunguje
1. Zkontrolujte, zda máte nainstalovaný `python-rtmidi`:
   ```bash
   pip install python-rtmidi
   ```
2. Ověřte, že máte dostupný MIDI výstup (hardware nebo software loopback)
3. Na Windows můžete použít virtuální MIDI port (např. loopMIDI)

### Aplikace se nespustí
1. Zkontrolujte verzi Pythonu:
   ```bash
   python --version
   ```
   Vyžaduje Python 3.8+

2. Reinstalujte závislosti:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. Zkontrolujte, že je Tkinter nainstalován:
   ```bash
   python -m tkinter
   ```

### Akord se nezobrazuje
- Zkontrolujte formát názvu akordu (např. `Dm7`, ne `Dmi7`)
- Používejte `#` místo `b` pro alterace
- Zkontrolujte, že akord je v `CHORD_TYPES` v `config.py`

## Plánované funkce

- [ ] **Ear Training Mode**: Cvičení rozpoznávání akordů poslechem
- [ ] **Chord-Scale Visualization**: Zobrazení doporučených stupnic pro improvizaci
- [ ] **Harmonic Function Coloring**: Barevné rozlišení tonic/subdominant/dominant
- [ ] **Progression Generator**: Generování náhodných progresí ve stylu jazzu
- [ ] **Voice Leading Analysis**: Analýza a doporučení pro voice leading
- [ ] **Export to PDF/MIDI**: Export progresí jako notový zápis nebo MIDI soubor
- [ ] **Practice Session Tracker**: Sledování pokroku a statistiky cvičení

## Přispívání

Příspěvky jsou vítány! Pokud máte nápad na vylepšení:

1. Forkněte repozitář
2. Vytvořte feature branch (`git checkout -b feature/amazing-feature`)
3. Commitněte změny (`git commit -m 'Add amazing feature'`)
4. Push do branch (`git push origin feature/amazing-feature`)
5. Otevřete Pull Request

## Licence

Tento projekt je licencován pod MIT licencí - viz LICENSE soubor pro detaily.

## Kontakt

Pro otázky nebo návrhy na vylepšení prosím otevřete Issue na GitHubu.

## Poděkování

- Databáze obsahuje klasické jazzové standardy od autorů jako Duke Ellington, Bill Evans, John Coltrane, a další
- Inspirováno jazzovou pedagogikou a teorií z knih jako "The Jazz Piano Book" (Mark Levine)

---

**Enjoy practicing jazz! 🎹🎵**
