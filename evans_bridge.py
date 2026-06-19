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


def _engine_script_named(name):
    return os.path.join(ENGINE_DIR, "improved", name)


def generate_arrangement(chords, out_path, bpm=110, melody=True, seed=1):
    """Z akordů (list značek) vyrobí plnou Evansovskou aranž a uloží do out_path.
    Vrátí cestu k souboru, nebo vyhodí RuntimeError."""
    script = _engine_script_named("arrange_chords.py")
    if not os.path.exists(script):
        raise RuntimeError(f"Motor nenalezen: {script}\n"
                           "Nastav EVANS_ENGINE_DIR.")
    cmd = [_engine_python(), script, "--chords", " | ".join(chords),
           "--out", out_path, "--bpm", str(bpm), "--seed", str(seed)]
    if not melody:
        cmd.append("--no-melody")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=120)
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError((proc.stderr or "Motor nevrátil výstup.").strip())
    data = json.loads(out.splitlines()[-1])
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["output"]


def play_file(path):
    """Přehraje MIDI soubor do loopMIDI přes player motoru. Neblokuje (Popen)."""
    script = _engine_script_named("player.py")
    if not os.path.exists(script):
        raise RuntimeError(f"Player nenalezen: {script}")
    env = dict(os.environ, PYTHONUTF8="1")
    return subprocess.Popen([_engine_python(), script, path], env=env)


# ===========================================================================
# Evansovy rootless voicingy (čistě stdlib port z dear-mister-evans/voicings.py)
# Pro typ voicingu "Evans" v PianoChordu. Voice-leading z předchozího akordu.
# ===========================================================================
import itertools

PIANO_KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# rootless 4-tónové voicingy: offsety v půltónech od základu (root vynechán,
# kromě m7b5/dim7). Klíče = naše kvality.
_ROOTLESS = {
    'maj7': [4, 7, 11, 2], '6': [4, 7, 9, 2], 'm7': [3, 7, 10, 2],
    'm6': [3, 7, 9, 2], '7': [4, 10, 2, 9], 'sus': [5, 10, 2, 7],
    'm7b5': [3, 6, 10, 0], 'dim7': [3, 6, 9, 0], 'mMaj7': [3, 7, 11, 2],
    'aug': [4, 8, 11, 2],
}
_WIN_LO, _WIN_HI = 52, 76


def quality_to_token(chord_type):
    """Převede akordovou kvalitu z PianoChordu na náš rootless token."""
    ct = (chord_type or "").strip()
    low = ct.lower()
    if 'm7b5' in low or 'min7b5' in low or 'ø' in ct:
        return 'm7b5'
    if 'dim' in low or '°' in ct:
        return 'dim7'
    is_minor = (low.startswith('m') and not low.startswith('maj')) or \
               low.startswith('-') or low.startswith('min')
    if is_minor and 'maj7' in low:
        return 'mMaj7'
    if low.startswith('maj') or ct.startswith('M') or 'Δ' in ct:
        return '6' if ('6' in low and '/' not in low and '6' == low[:1]) else 'maj7'
    if 'aug' in low or '+' in ct:
        return 'aug'
    if 'sus' in low:
        return 'sus'
    if is_minor:
        return 'm6' if '6' in ct else 'm7'
    if low.startswith('6') or low.startswith('69') or '6/9' in low:
        return '6'
    if any(d in ct for d in ('7', '9', '11', '13')):
        return '7'
    return 'maj7'  # holý dur -> Evans přidá barvu (9, 7)


def _pcs_for(root, token):
    offs = _ROOTLESS.get(token, _ROOTLESS['maj7'])
    seen, out = set(), []
    for o in offs:
        pc = (root + o) % 12
        if pc not in seen:
            seen.add(pc); out.append(pc)
    while len(out) < 4:
        out.append((out[0] + 7) % 12)
    return out[:4]


def _place_near(pc, target):
    d = (pc - target) % 12
    return target + (d - 12 if d > 6 else d)


def _build_close(pcs, center=63):
    pcs = sorted(pcs)
    voic = [48 + pcs[0]]
    for pc in pcs[1:]:
        nx = voic[-1] + ((pc - voic[-1]) % 12)
        if nx == voic[-1]:
            nx += 12
        voic.append(nx)
    while sum(voic) / len(voic) < center - 4:
        voic = [v + 12 for v in voic]
    while sum(voic) / len(voic) > center + 4:
        voic = [v - 12 for v in voic]
    return sorted(voic)


def _voice_lead(prev, pcs):
    best, best_cost = None, 1e9
    for perm in itertools.permutations(pcs):
        placed = [_place_near(perm[i], prev[i]) for i in range(4)]
        if len(set(placed)) < 4:
            continue
        if any(p < _WIN_LO - 3 or p > _WIN_HI + 3 for p in placed):
            continue
        cost = sum(abs(placed[i] - prev[i]) for i in range(4))
        if cost < best_cost:
            best_cost, best = cost, sorted(placed)
    return best or _build_close(pcs)


def evans_voicing(root_pc, chord_type, prev_notes=None):
    """Vrátí 4 MIDI tóny Evansova rootless voicingu pro daný akord.
    prev_notes: předchozí voicing (kvůli voice-leadingu)."""
    token = quality_to_token(chord_type)
    pcs = _pcs_for(root_pc, token)
    if prev_notes:
        ref = sorted(prev_notes)
        ref = (ref + [ref[-1]] * 4)[:4] if len(ref) < 4 else \
              [ref[0], ref[len(ref) // 3], ref[2 * len(ref) // 3], ref[-1]]
        return _voice_lead(ref, pcs)
    return _build_close(pcs, center=63)


if __name__ == "__main__":
    # rychlý test:  python evans_bridge.py "cesta.mid"
    if len(sys.argv) < 2:
        print("použití: python evans_bridge.py <soubor.mid>"); sys.exit(1)
    print("engine:", _engine_python())
    print("script:", _engine_script(), "(existuje:", available(), ")")
    d = get_progression_from_midi(sys.argv[1])
    print("tónina:", d["key"])
    print("akordy:", " | ".join(d["chords"]))
