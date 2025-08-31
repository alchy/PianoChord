# midi_manager.py
"""
midi_manager.py - Centralizovaná správa MIDI funkcí.
Odděluje MIDI logiku od GUI a ostatních komponent.
"""

import logging
import mido
import time
import threading
from typing import List, Optional, Callable
from config import AppConfig

logger = logging.getLogger(__name__)


class MidiManager:
    """Centralizovaná správa všech MIDI operací."""

    def __init__(self):
        self.outport: Optional[mido.ports.BasePort] = None
        self.current_port_name: Optional[str] = None
        self.is_enabled: bool = False
        self.velocity: int = AppConfig.DEFAULT_MIDI_VELOCITY
        self._midi_lock = threading.Lock()

        # Callback pro notifikace (např. pro GUI update)
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_success: Optional[Callable[[str], None]] = None

    def initialize(self) -> bool:
        """
        Inicializuje MIDI systém.
        Vrací True při úspěchu, False při selhání.
        """
        try:
            available_ports = self.get_available_ports()
            if not available_ports:
                self._handle_error("Žádný dostupný MIDI port. Nainstalujte virtuální MIDI port.")
                return False

            # Automaticky vybere první dostupný port
            success = self.set_port(available_ports[0])
            if success:
                self._handle_success("MIDI systém úspěšně inicializován")
                return True
            return False

        except ImportError as e:
            self._handle_error(f"MIDI závislosti nejsou nainstalované: {e}")
            return False
        except Exception as e:
            self._handle_error(f"Neočekávaná chyba při inicializaci MIDI: {e}")
            return False

    def get_available_ports(self) -> List[str]:
        """Vrací seznam dostupných MIDI výstupních portů."""
        try:
            return mido.get_output_names()
        except Exception as e:
            logger.error(f"Chyba při načítání MIDI portů: {e}")
            return []

    def set_port(self, port_name: str) -> bool:
        """
        Nastaví MIDI výstupní port.
        Vrací True při úspěchu.
        """
        try:
            # Zavře stávající port
            self.close_port()

            # Otevře nový port
            self.outport = mido.open_output(port_name)
            self.current_port_name = port_name
            logger.info(f"MIDI port nastaven na: {port_name}")
            return True

        except Exception as e:
            error_msg = f"Chyba při nastavení MIDI portu '{port_name}': {e}"
            self._handle_error(error_msg)
            return False

    def close_port(self) -> None:
        """Bezpečně zavře MIDI port."""
        if self.outport:
            try:
                self.outport.close()
            except Exception as e:
                logger.warning(f"Chyba při zavírání MIDI portu: {e}")
            finally:
                self.outport = None
                self.current_port_name = None

    def play_chord(self, midi_notes: List[int], duration: float = None, velocity: int = None) -> bool:
        """
        Přehraje akord s danými MIDI notami.
        Používá threading pro neblokující operaci.
        Vrací True pokud byl příkaz odeslán úspěšně.
        """
        if not self.is_enabled or not self.outport:
            return False

        # Použije výchozí hodnoty pokud nejsou poskytnuty
        if duration is None:
            duration = AppConfig.DEFAULT_CHORD_DURATION
        if velocity is None:
            velocity = self.velocity

        # Spustí přehrávání v samostatném threadu
        def play_thread():
            self._play_chord_blocking(midi_notes, duration, velocity)

        thread = threading.Thread(target=play_thread, daemon=True)
        thread.start()
        return True

    def _play_chord_blocking(self, midi_notes: List[int], duration: float, velocity: int) -> None:
        """Interní metoda pro blokující přehrání akordu."""
        with self._midi_lock:
            try:
                # Pošle note_on pro všechny noty
                for note in midi_notes:
                    msg_on = mido.Message('note_on', note=note, velocity=velocity)
                    self.outport.send(msg_on)

                # Čeká specifikovanou dobu
                time.sleep(duration)

                # Pošle note_off pro všechny noty
                for note in midi_notes:
                    msg_off = mido.Message('note_off', note=note, velocity=0)
                    self.outport.send(msg_off)

                logger.debug(f"Přehrán MIDI akord: {midi_notes}, velocity: {velocity}")

            except Exception as e:
                self._handle_error(f"Chyba při přehrávání MIDI akordu: {e}")

    def stop_all_notes(self) -> bool:
        """
        Zastaví všechny hrající MIDI noty.
        Vrací True při úspěchu.
        """
        if not self.outport:
            return False

        try:
            with self._midi_lock:
                # Pošle All Notes Off zprávu
                msg = mido.Message('control_change', control=AppConfig.MIDI_ALL_NOTES_OFF_CC, value=0)
                self.outport.send(msg)
                logger.debug("Všechny MIDI noty zastaveny")
                return True

        except Exception as e:
            self._handle_error(f"Chyba při zastavování MIDI not: {e}")
            return False

    def set_velocity(self, velocity: int) -> None:
        """Nastaví velocity pro budoucí přehrávání."""
        self.velocity = max(0, min(127, int(velocity)))  # Clamp na 0-127

    def set_enabled(self, enabled: bool) -> None:
        """Zapne/vypne MIDI přehrávání."""
        self.is_enabled = enabled
        if enabled and not self.outport:
            # Pokus o re-inicializaci když se zapíná MIDI
            self.initialize()

    def cleanup(self) -> None:
        """Vyčistí všechny MIDI zdroje při ukončení aplikace."""
        self.stop_all_notes()
        self.close_port()
        logger.info("MIDI systém vyčištěn")

    def _handle_error(self, error_message: str) -> None:
        """Centralizované zpracování chyb."""
        logger.error(error_message)
        if self.on_error:
            self.on_error(error_message)

    def _handle_success(self, success_message: str) -> None:
        """Centralizované zpracování úspěšných operací."""
        logger.info(success_message)
        if self.on_success:
            self.on_success(success_message)
