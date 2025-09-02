# 🎹 Piano Chord Analyzer

**Piano Chord Analyzer** je pokročilá GUI aplikace v Pythonu pro analýzu piano akordů, studium jazzové harmonie a procvičování progresí. Ideální nástroj pro hudebníky, kteří chtějí porozumět harmonii, voicingům a strukturám jazzových standardů.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

## ✨ Hlavní funkce

### 🎼 **Analýza akordů**
- Zadejte jakýkoli akord (např. "Cmaj7", "F#m7b5", "G7alt") 
- Zobrazí strukturu, noty a voicing na virtuální klaviatuře
- Automatické navrhování fallback akordů pro neznámé typy

### 🎹 **Virtuální klaviatura**
- 88 kláves s realistickým zobrazením
- Tři typy voicingů s barevným rozlišením:
  - **🔴 Root voicing** - základní pozice akordu
  - **🟢 Smooth voicing** - plynulé přechody mezi akordy
  - **🔵 Drop 2 voicing** - jazzový otevřený voicing

### 🎵 **Databáze jazzových standardů**
- **80+ klasických skladeb** včetně:
  - Bill Evans ("Waltz for Debby", "Blue in Green")
  - John Coltrane ("Giant Steps", "Blue Bossa") 
  - Michel Petrucciani ("Looking Up", "Brazilian Like")
  - Klasiky ("Autumn Leaves", "All The Things You Are")
- **Automatické transpozice** - každá píseň v 12 tóninách
- **ii-V-I progrese** ve všech obtížnostech

### 🎮 **Progression Player**
- Procházejte progrese krok za krokem
- Klávesové zkratky (←/→) pro rychlou navigaci
- Kliknutelná tlačítka akordů pro přeskakování
- Export progresí do textových souborů

### 🎚️ **MIDI podpora**
- Realtime přehrávání akordů přes MIDI
- Nastavitelná velocity a porty
- Podpora všech MIDI zařízení a virtuálních portů

### 📊 **Pokročilé funkce**
- **Tritonové substituce** pro dominantní akordy
- **Enharmonické ekvivalenty** (Db = C#)
- **Kompletní log** všech operací s exportem
- **Hledání progresí** podle konkrétního akordu

## 🚀 Rychlý start

### Požadavky
```bash
python 3.8+
tkinter (součást standardní instalace Pythonu)
```

### Instalace
```bash
# Klonování repozitáře
git clone https://github.com/your-username/piano-chord-analyzer.git
cd piano-chord-analyzer

# Instalace závislostí
pip install -r requirements.txt

# Spuštění aplikace
python main.py
```

### MIDI setup (volitelné)
Pro použití MIDI funkcí nainstalujte:
```bash
pip install mido python-rtmidi
```

## 📖 Jak používat

### 1. **Analýza jednotlivých akordů**
```
1. Zadejte akord do vstupního pole (např. "Dm7")
2. Stiskněte Enter nebo klikněte "Analyzovat" 
3. Akord se zobrazí na klaviatuře a v analýze
4. V dolní části uvidíte reálné progrese s tímto akordem
```

### 2. **Procvičování progresí**
```
1. Přejděte na tab "Progression Player"
2. Vyberte píseň z dropdown menu
3. Klikněte "Nahrát celou píseň"
4. Používejte šipky nebo tlačítka pro procházení
```

### 3. **Voicing experimenty**
```
1. Vyberte typ voicingu (Root/Smooth/Drop 2)
2. Zadávejte různé akordy a pozorujte rozdíly
3. Smooth voicing automaticky vytváří plynulé přechody
```

## 🏗️ Architektura projektu

```
piano-chord-analyzer/
├── main.py                    # 🚀 Vstupní bod aplikace
├── requirements.txt           # 📦 Python závislosti  
├── utils_config.py           # ⚙️ Konfigurace a konstanty
│
├── core_music_theory.py      # 🎼 Centrální hudební teorie
├── core_constants.py         # 🎹 Definice akordů a voicingů
├── core_harmony.py           # 🎵 Analýza harmonií
├── core_database.py          # 🗄️ Databáze jazzových standardů
├── core_state.py            # 📊 Správa stavu aplikace
│
├── gui_main_window.py        # 🖥️ Hlavní GUI okno
├── gui_controls.py           # 🎚️ Ovládací prvky
├── gui_analysis.py           # 📈 GUI pro analýzu
├── gui_progression.py        # 🎮 Progression player GUI
├── gui_keyboard.py           # 🎹 Virtuální klaviatura
│
├── display_chord.py          # 🎨 Zobrazování akordů
└── hw_midi.py               # 🎛️ MIDI hardware podpora
```

### 🔧 **Klíčové moduly:**

- **`core_music_theory.py`** - Centrální modul pro všechny hudební operace (transpozice, parsování)
- **`core_constants.py`** - Definice 15+ typů akordů a voicingů 
- **`core_database.py`** - 80+ jazzových standardů s automatickými transpozicemi
- **`gui_*`** - Modulární GUI komponenty pro čistou separaci

## 🎯 Pokročilé použití

### Vlastní progrese
```python
# V Progression Player můžete načíst vlastní progrese
# dvojklikem na jakoukoliv progrese z analýzy akordů
```

### MIDI experimenty  
```python
# Změňte velocity, vyzkoušejte různá MIDI zařízení
# Všechny akordy se přehrávají v reálném čase
```

### Export dat
```python
# Log obsahuje kompletní historii - exportovatelný do .txt
# Progrese lze exportovat pro použití v DAW
```

## 🔧 Vývoj a přispívání

### Spuštění ve vývojovém režimu
```bash
# Zapnutí debug režimu
export DEBUG=True  # Linux/Mac
set DEBUG=True     # Windows

python main.py
```

### Struktura pro nové funkce
```python
# Hudební funkce přidávejte do core_music_theory.py
# GUI komponenty do příslušných gui_* modulů  
# Nové akordy do core_constants.py CHORD_VOICINGS
```

### Testování
```bash
# Ověření importů (test cyklických importů)
python -c "import core_constants, core_harmony, core_database; print('✅ Import OK')"

# Test MIDI
python -c "import hw_midi; print('🎛️ MIDI OK')"
```

## 📦 Vytvoření distribuce

### Pomocí PyInstaller
```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed \
    --hidden-import "mido.backends.rtmidi" \
    --hidden-import "rtmidi" \
    main.py
```

### Pomocí auto-py-to-exe (GUI)
```bash
pip install auto-py-to-exe
auto-py-to-exe
```

## 🎵 Podporované akordy

### Základní typy
- **Major**: `maj`, `maj7`, `maj9`, `6`, `maj7#5`, `maj7b5`
- **Minor**: `m`, `m7`, `m9`, `m6`, `m7b5`, `m(maj7)`
- **Dominant**: `7`, `9`, `13`, `7b9`, `7b5`, `7#5`
- **Ostatní**: `dim`, `dim7`, `aug`, `sus2`, `sus4`

### Příklady použití
```
Cmaj7, F#m7b5, G7alt, Bbdim7, Esus4, Am(maj7)
```
