# midi_player.py
"""
midi_player.py - Modul pro hraní MIDI akordů v reálném čase.
Používá mido pro odesílání MIDI zpráv do výstupního portu.
"""

import mido
import time
import threading
from typing import List
from constants import MusicalConstants  # NOVÉ: Pro MIDI_VELOCITY

DEBUG = True


class MidiPlayer:
    """Třída pro hraní MIDI not v reálném čase."""

    def __init__(self, port_name: str = None):
        """
        Inicializuje MIDI player s výstupním portem.
        Pokud port_name je None, vybere první dostupný.
        """
        self.port_name = port_name
        self.outport = None
        self._open_port()

    def _open_port(self):
        """Otevře MIDI výstupní port."""
        available_ports = mido.get_output_names()
        if not available_ports:
            raise ValueError("Žádný dostupný MIDI výstupní port. Nainstalujte virtuální port jako loopMIDI.")

        if self.port_name is None or self.port_name not in available_ports:
            self.port_name = available_ports[0]  # Default první port
            if DEBUG:
                print(f"Vybrán default MIDI port: {self.port_name}")

        try:
            self.outport = mido.open_output(self.port_name)
        except Exception as e:
            raise ValueError(f"Chyba při otevírání MIDI portu '{self.port_name}': {str(e)}")

    def play_chord(self, midi_notes: List[int], duration: float = 1.0, velocity: int = MusicalConstants.MIDI_VELOCITY):
        """
        Přehraje akord (seznam MIDI not) na danou dobu.
        Používá threading pro non-blocking operaci.
        Velocity z konstanty (default 64, pro snížení hlasitosti).
        """
        if not self.outport:
            raise ValueError("MIDI port není otevřen.")

        def _play_thread():
            # Poslat note_on pro všechny noty současně
            for note in midi_notes:
                msg_on = mido.Message('note_on', note=note, velocity=velocity)
                self.outport.send(msg_on)

            # Počkat duration
            time.sleep(duration)

            # Poslat note_off
            for note in midi_notes:
                msg_off = mido.Message('note_off', note=note, velocity=0)
                self.outport.send(msg_off)

        # Spustit v samostatném threadu
        thread = threading.Thread(target=_play_thread)
        thread.start()

    def get_available_ports(self) -> List[str]:
        """Vrátí seznam dostupných MIDI výstupních portů."""
        return mido.get_output_names()

    def change_port(self, new_port_name: str):
        """Změní MIDI port."""
        if self.outport:
            self.outport.close()
        self.port_name = new_port_name
        self._open_port()

    def close(self):
        """Zavře MIDI port."""
        if self.outport:
            self.outport.close()