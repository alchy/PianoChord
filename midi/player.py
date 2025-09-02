# midi/player.py
"""
midi/player.py - Nezávislý MIDI přehrávač s threading podporou.
Může být použit samostatně v jiných hudebních aplikacích.
Obsahuje vlastní logiku pro časování a správu MIDI portů.
"""

import logging
import time
import threading
from typing import List, Optional, Callable
from config import AppConfig

logger = logging.getLogger(__name__)

# Kontrola dostupnosti MIDI knihoven
try:
    import mido

    MIDI_AVAILABLE = True
except ImportError:
    logger.warning("MIDI knihovna 'mido' není dostupná. MIDI funkce nebudou fungovat.")
    MIDI_AVAILABLE = False


class MidiPlayer:
    """
    Nezávislý MIDI přehrávač s pokročilou správou portů a threading.
    Může být použit v jiných aplikacích bez GUI závislostí.
    """

    def __init__(self):
        self.outport: Optional = None
        self.current_port_name: Optional[str] = None
        self.is_enabled: bool = False
        self.velocity: int = AppConfig.DEFAULT_MIDI_VELOCITY
        self._midi_lock = threading.Lock()

        # Callback funkce pro notifikace (volitelné)
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_success: Optional[Callable[[str], None]] = None
        self.on_chord_played: Optional[Callable[[List[int]], None]] = None

    def initialize(self) -> bool:
        """
        Inicializuje MIDI systém a automaticky vybere první dostupný port.

        Returns:
            bool: True při úspěchu, False při selhání
        """
        if not MIDI_AVAILABLE:
            self._handle_error("MIDI knihovny nejsou dostupné")
            return False

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

        except Exception as e:
            self._handle_error(f"Neočekávaná chyba při inicializaci MIDI: {e}")
            return False

    def get_available_ports(self) -> List[str]:
        """
        Vrací seznam dostupných MIDI výstupních portů.

        Returns:
            List[str]: Seznam názvů MIDI portů
        """
        if not MIDI_AVAILABLE:
            return []

        try:
            ports = mido.get_output_names()
            logger.debug(f"Dostupné MIDI porty: {ports}")
            return ports
        except Exception as e:
            logger.error(f"Chyba při načítání MIDI portů: {e}")
            return []

    def set_port(self, port_name: str) -> bool:
        """
        Nastaví aktivní MIDI výstupní port.

        Args:
            port_name: Název MIDI portu

        Returns:
            bool: True při úspěchu
        """
        if not MIDI_AVAILABLE:
            return False

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
        """Bezpečně zavře aktivní MIDI port."""
        if self.outport:
            try:
                self.outport.close()
                logger.debug(f"MIDI port {self.current_port_name} zavřen")
            except Exception as e:
                logger.warning(f"Chyba při zavírání MIDI portu: {e}")
            finally:
                self.outport = None
                self.current_port_name = None

    def play_chord(self, midi_notes: List[int], duration: float = None, velocity: int = None) -> bool:
        """
        Přehraje akord s danými MIDI notami.
        Používá threading pro neblokující operaci.

        Args:
            midi_notes: Seznam MIDI čísel not k přehrání
            duration: Délka přehrávání v sekundách (None = použije default)
            velocity: Síla úderu (None = použije aktuální nastavení)

        Returns:
            bool: True pokud byl příkaz odeslán úspěšně
        """
        if not self.is_enabled or not self.outport or not MIDI_AVAILABLE:
            logger.debug("MIDI přehrávání vypnuto nebo port nedostupný")
            return False

        if not midi_notes:
            logger.warning("Prázdný seznam MIDI not")
            return False

        # Použije výchozí hodnoty pokud nejsou poskytnuty
        if duration is None:
            duration = AppConfig.DEFAULT_CHORD_DURATION
        if velocity is None:
            velocity = self.velocity

        # Validace hodnot
        duration = max(0.1, min(10.0, duration))  # 0.1-10 sekund
        velocity = max(1, min(127, velocity))  # 1-127 MIDI rozsah
        midi_notes = [max(21, min(108, note)) for note in midi_notes]  # 88-klávesy rozsah

        # Spustí přehrávání v samostatném threadu
        def play_thread():
            self._play_chord_blocking(midi_notes, duration, velocity)

        thread = threading.Thread(target=play_thread, daemon=True)
        thread.start()

        logger.debug(f"MIDI akord spuštěn: {midi_notes}, velocity={velocity}, duration={duration}s")
        return True

    def _play_chord_blocking(self, midi_notes: List[int], duration: float, velocity: int) -> None:
        """
        Interní metoda pro blokující přehrání akordu.
        Běží v samostatném threadu.

        Args:
            midi_notes: MIDI čísla not
            duration: Délka přehrávání
            velocity: Síla úderu
        """
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

                # Callback pro úspěšné přehrání
                if self.on_chord_played:
                    self.on_chord_played(midi_notes)

                logger.debug(f"MIDI akord dokončen: {midi_notes}")

            except Exception as e:
                self._handle_error(f"Chyba při přehrávání MIDI akordu: {e}")

    def play_single_note(self, midi_note: int, duration: float = None, velocity: int = None) -> bool:
        """
        Přehraje jednu notu.
        Pohodlná metoda pro testování nebo jednoduché použití.

        Args:
            midi_note: MIDI číslo noty
            duration: Délka přehrávání
            velocity: Síla úderu

        Returns:
            bool: True při úspěchu
        """
        return self.play_chord([midi_note], duration, velocity)

    def play_chord_sequence(self, chord_sequence: List[List[int]], duration_per_chord: float = None) -> bool:
        """
        Přehraje sekvenci akordů za sebou.

        Args:
            chord_sequence: Seznam akordů (každý akord je seznam MIDI not)
            duration_per_chord: Délka každého akordu

        Returns:
            bool: True pokud byla sekvence spuštěna
        """
        if not chord_sequence:
            return False

        def sequence_thread():
            for chord in chord_sequence:
                if chord:  # Přeskočí prázdné akordy
                    self._play_chord_blocking(chord, duration_per_chord or AppConfig.DEFAULT_CHORD_DURATION,
                                              self.velocity)
                else:
                    # Pauza pro prázdné akordy
                    time.sleep(duration_per_chord or AppConfig.DEFAULT_CHORD_DURATION)

        thread = threading.Thread(target=sequence_thread, daemon=True)
        thread.start()

        logger.info(f"Spuštěna sekvence {len(chord_sequence)} akordů")
        return True

    def stop_all_notes(self) -> bool:
        """
        Zastaví všechny hrající MIDI noty.

        Returns:
            bool: True při úspěchu
        """
        if not self.outport or not MIDI_AVAILABLE:
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
        """
        Nastaví velocity pro budoucí přehrávání.

        Args:
            velocity: Síla úderu (0-127)
        """
        self.velocity = max(0, min(127, int(velocity)))
        logger.debug(f"MIDI velocity nastavena na: {self.velocity}")

    def set_enabled(self, enabled: bool) -> None:
        """
        Zapne/vypne MIDI přehrávání.

        Args:
            enabled: True pro zapnutí, False pro vypnutí
        """
        old_state = self.is_enabled
        self.is_enabled = enabled

        if enabled and not self.outport:
            # Pokus o re-inicializaci když se zapíná MIDI
            self.initialize()
        elif not enabled and old_state:
            # Zastaví všechny noty při vypínání
            self.stop_all_notes()

        logger.info(f"MIDI přehrávání {'zapnuto' if enabled else 'vypnuto'}")

    def get_status(self) -> dict:
        """
        Vrací aktuální stav MIDI playeru.

        Returns:
            dict: Informace o stavu MIDI systému
        """
        return {
            "midi_available": MIDI_AVAILABLE,
            "is_enabled": self.is_enabled,
            "current_port": self.current_port_name,
            "velocity": self.velocity,
            "has_active_port": self.outport is not None,
            "available_ports": self.get_available_ports()
        }

    def cleanup(self) -> None:
        """Vyčistí všechny MIDI zdroje při ukončení aplikace."""
        logger.info("Čištění MIDI zdrojů...")
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


# Utility funkce pro testování MIDI bez třídy
def test_midi_availability() -> bool:
    """
    Testuje dostupnost MIDI systému.

    Returns:
        bool: True pokud je MIDI dostupné
    """
    if not MIDI_AVAILABLE:
        print("MIDI knihovny nejsou dostupné")
        return False

    try:
        ports = mido.get_output_names()
        print(f"Dostupné MIDI porty: {ports}")
        return len(ports) > 0
    except Exception as e:
        print(f"Chyba při testování MIDI: {e}")
        return False


if __name__ == "__main__":
    # Jednoduché testování MIDI playeru
    print("=== Test MidiPlayer ===")

    # Test dostupnosti
    print("\n1. Test dostupnosti MIDI:")
    available = test_midi_availability()

    if available:
        # Test základních funkcí
        print("\n2. Test MidiPlayer:")
        player = MidiPlayer()

        if player.initialize():
            print(f"MIDI port: {player.current_port_name}")

            # Test jednoduché noty
            player.set_enabled(True)
            print("Přehrávám C4...")
            player.play_single_note(60, duration=0.5)  # C4

            time.sleep(1)  # Čekání na dokončení

            # Test akordu
            print("Přehrávám Cmaj7...")
            player.play_chord([60, 64, 67, 71], duration=1.0)  # Cmaj7

            time.sleep(2)  # Čekání na dokončení

            # Test stavu
            print("\n3. Stav MIDI:")
            status = player.get_status()
            for key, value in status.items():
                print(f"{key}: {value}")

            player.cleanup()
        else:
            print("Inicializace MIDI selhala")
    else:
        print("MIDI není dostupné pro testování")
