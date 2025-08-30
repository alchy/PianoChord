# main.py
import sys
from piano_gui import PianoGUI

# --- DEBUG ---
# Urcuje, zda se budou vypisovat ladici informace.
DEBUG = True

if DEBUG:
    print("Spouštím aplikaci PianoChord")
    print(f"Verze Pythonu: {sys.version}")

if __name__ == '__main__':
    app = PianoGUI()
    app.run()