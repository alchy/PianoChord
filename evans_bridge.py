# evans_bridge.py
"""
Most na motor "dear-mister-evans": z libovolného MIDI vytáhne akordovou progresi.

Volá samostatný PŘÍKAZ (improved/extract_progression.py) v jeho VLASTNÍM venv,
takže PianoChord nemusí mít numpy ani sdílet prostředí — je to čistá GUI
nadstavba nad CLI motorem.

Konfigurace: proměnná prostředí EVANS_ENGINE_DIR ukazuje na složku repa
dear-mister-evans (default níže).
"""
import os, sys, json, subprocess

ENGINE_DIR = os.environ.get(
    "EVANS_ENGINE_DIR", r"C:\Users\jindr\PycharmProjects\jazz-markov")

def _engine_python():
    cand = os.path.join(ENGINE_DIR, ".venv", "Scripts", "python.exe")
    return cand if os.path.exists(cand) else sys.executable

def _engine_script():
    return os.path.join(ENGINE_DIR, "improved", "extract_progression.py")

def available():
    return os.path.exists(_engine_script())

def get_progression_from_midi(midi_path, bars=32, keep_repeats=False):
    """Vrátí dict {'key','chords','bars','source'} nebo vyhodí RuntimeError."""
    if not available():
        raise RuntimeError(
            "Motor dear-mister-evans nenalezen.\n"
            f"Hledám: {_engine_script()}\n"
            "Nastav proměnnou prostředí EVANS_ENGINE_DIR na složku toho repa.")
    cmd = [_engine_python(), _engine_script(), midi_path]
    if bars:
        cmd += ["--bars", str(bars)]
    if keep_repeats:
        cmd += ["--keep-repeats"]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=120)
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError((proc.stderr or "Motor nevrátil žádný výstup.").strip())
    try:
        data = json.loads(out.splitlines()[-1])
    except Exception:
        raise RuntimeError(f"Nečitelný výstup motoru:\n{out[:300]}")
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


if __name__ == "__main__":
    # rychlý test:  python evans_bridge.py "cesta.mid"
    if len(sys.argv) < 2:
        print("použití: python evans_bridge.py <soubor.mid>"); sys.exit(1)
    print("engine:", _engine_python())
    print("script:", _engine_script(), "(existuje:", available(), ")")
    d = get_progression_from_midi(sys.argv[1])
    print("tónina:", d["key"])
    print("akordy:", " | ".join(d["chords"]))
