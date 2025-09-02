# core/app_state.py
"""
core/app_state.py - Centralizovaná správa stavu aplikace.
Nezávislá na GUI, může být použita v jiných aplikacích.
Spravuje všechny důležité stavy včetně voicing typu, MIDI nastavení a historii.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import AppConfig

logger = logging.getLogger(__name__)


class ApplicationState:
    """
    Centralizovaný stav aplikace - oddělený od GUI.
    Může být použit jako model v MVC architektuře.
    """

    def __init__(self):
        """Inicializuje všechny stavové proměnné na výchozí hodnoty."""

        # Stav aktuální analýzy
        self.current_analysis: Dict[str, Any] = {}
        self.last_displayed_chord: Optional[str] = None

        # Stav progrese
        self.current_progression_chords: List[str] = []
        self.current_progression_index: int = 0
        self.current_progression_source: Optional[str] = None

        # MIDI stav a nastavení
        self.previous_chord_midi: List[int] = []
        self.last_played_chord: Optional[str] = None
        self.midi_enabled: bool = False
        self.midi_velocity: int = AppConfig.DEFAULT_MIDI_VELOCITY

        # Nastavení voicingů
        self.voicing_type: str = "root"  # "root", "smooth", "drop2"

        # Log historie s timestampy
        self.log_messages: List[str] = []

        # Callback funkce pro notifikace (volitelné)
        self.on_state_changed: Optional[callable] = None
        self.on_chord_changed: Optional[callable] = None
        self.on_progression_changed: Optional[callable] = None

        logger.info("ApplicationState inicializován")

    def set_voicing_type(self, voicing_type: str) -> None:
        """
        Nastaví typ voicingu a zaloguje změnu.

        Args:
            voicing_type: Nový typ voicingu ("root", "smooth", "drop2")
        """
        valid_types = ["root", "smooth", "drop2"]
        if voicing_type not in valid_types:
            logger.warning(f"Neplatný typ voicingu: {voicing_type}, použit 'root'")
            voicing_type = "root"

        old_type = self.voicing_type
        self.voicing_type = voicing_type

        if old_type != voicing_type:
            self.log(f"Voicing změněn z '{old_type}' na '{voicing_type}'")
            self._notify_state_changed("voicing_type", old_type, voicing_type)

    def get_voicing_type(self) -> str:
        """
        Vrací aktuální typ voicingu.

        Returns:
            str: Aktuální typ voicingu
        """
        return self.voicing_type

    def set_current_chord_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Nastaví výsledky aktuální analýzy akordu.

        Args:
            analysis: Slovník s výsledky analýzy akordu
        """
        old_analysis = self.current_analysis.copy()
        self.current_analysis = analysis

        chord_name = analysis.get('chord_name', 'Unknown')
        self.log(f"Analyzován akord: {chord_name}")

        if self.on_chord_changed:
            self.on_chord_changed(old_analysis, analysis)

    def set_midi_enabled(self, enabled: bool) -> None:
        """
        Zapne/vypne MIDI přehrávání.

        Args:
            enabled: True pro zapnutí, False pro vypnutí
        """
        old_enabled = self.midi_enabled
        self.midi_enabled = enabled

        if old_enabled != enabled:
            status = "zapnuto" if enabled else "vypnuto"
            self.log(f"MIDI {status}")
            self._notify_state_changed("midi_enabled", old_enabled, enabled)

    def set_midi_velocity(self, velocity: int) -> None:
        """
        Nastaví MIDI velocity.

        Args:
            velocity: Síla úderu (0-127)
        """
        old_velocity = self.midi_velocity
        self.midi_velocity = max(0, min(127, int(velocity)))

        if old_velocity != self.midi_velocity:
            self.log(f"MIDI velocity změněna na {self.midi_velocity}")
            self._notify_state_changed("midi_velocity", old_velocity, self.midi_velocity)

    def load_progression(self, chords: List[str], source_name: str) -> None:
        """
        Nahraje novou progrese a resetuje pozici.

        Args:
            chords: Seznam akordů v progrese
            source_name: Název zdroje progrese (pro logování)
        """
        old_chords = self.current_progression_chords.copy()
        old_source = self.current_progression_source

        self.current_progression_chords = chords.copy()
        self.current_progression_index = 0
        self.current_progression_source = source_name

        self.log(f"Nahrána progrese z: {source_name} ({len(chords)} akordů)")

        if self.on_progression_changed:
            self.on_progression_changed({
                "action": "loaded",
                "old_chords": old_chords,
                "new_chords": chords,
                "old_source": old_source,
                "new_source": source_name
            })

    def step_progression(self, step: int) -> bool:
        """
        Posune se o krok v progrese.

        Args:
            step: Počet kroků (kladný = dopředu, záporný = dozadu)

        Returns:
            bool: True pokud byl krok úspěšný, False pokud dosáhli konce/začátku
        """
        if not self.current_progression_chords:
            return False

        old_index = self.current_progression_index
        new_index = self.current_progression_index + step

        if 0 <= new_index < len(self.current_progression_chords):
            self.current_progression_index = new_index

            current_chord = self.get_current_chord()
            self.log(
                f"Krok v progrese: {current_chord} (pozice {new_index + 1}/{len(self.current_progression_chords)})")

            if self.on_progression_changed:
                self.on_progression_changed({
                    "action": "stepped",
                    "old_index": old_index,
                    "new_index": new_index,
                    "current_chord": current_chord
                })

            return True
        else:
            # Logování hranic progrese
            if new_index >= len(self.current_progression_chords):
                self.log("Dosažen konec progrese")
            else:
                self.log("Dosažen začátek progrese")
            return False

    def jump_to_chord_index(self, index: int) -> bool:
        """
        Skočí na konkrétní akord v progrese.

        Args:
            index: Index akordu v progrese (0-based)

        Returns:
            bool: True pokud skok byl úspěšný
        """
        if not self.current_progression_chords or not (0 <= index < len(self.current_progression_chords)):
            return False

        old_index = self.current_progression_index
        self.current_progression_index = index

        current_chord = self.get_current_chord()
        self.log(f"Skok na akord: {current_chord} (pozice {index + 1}/{len(self.current_progression_chords)})")

        if self.on_progression_changed:
            self.on_progression_changed({
                "action": "jumped",
                "old_index": old_index,
                "new_index": index,
                "current_chord": current_chord
            })

        return True

    def get_current_chord(self) -> Optional[str]:
        """
        Vrací aktuální akord z progrese.

        Returns:
            Optional[str]: Aktuální akord nebo None pokud není progrese
        """
        if not self.current_progression_chords or self.current_progression_index < 0:
            return None
        if self.current_progression_index >= len(self.current_progression_chords):
            return None
        return self.current_progression_chords[self.current_progression_index]

    def get_progression_info(self) -> Dict[str, Any]:
        """
        Vrací informace o aktuální progrese.

        Returns:
            Dict[str, Any]: Informace o progrese
        """
        return {
            "chords": self.current_progression_chords.copy(),
            "current_index": self.current_progression_index,
            "current_chord": self.get_current_chord(),
            "source": self.current_progression_source,
            "length": len(self.current_progression_chords),
            "has_progression": bool(self.current_progression_chords)
        }

    def set_chord_played(self, chord_name: str, midi_notes: List[int]) -> None:
        """
        Zaznamenává přehrání akordu pro MIDI a smooth voicing.

        Args:
            chord_name: Název přehraného akordu
            midi_notes: MIDI čísla přehraných not
        """
        old_chord = self.last_played_chord
        old_notes = self.previous_chord_midi.copy()

        self.last_played_chord = chord_name
        self.previous_chord_midi = midi_notes.copy()

        self.log(f"Přehrán MIDI akord: {chord_name}")
        logger.debug(f"MIDI noty: {midi_notes}")

        self._notify_state_changed("last_played_chord", old_chord, chord_name)

    def should_use_previous_chord_for_smooth(self) -> bool:
        """
        Určuje, zda použít předchozí akord pro smooth voicing.

        Returns:
            bool: True pokud máme předchozí akord a používáme smooth voicing
        """
        return self.voicing_type == "smooth" and bool(self.previous_chord_midi)

    def get_previous_chord_midi(self) -> List[int]:
        """
        Vrací MIDI noty předchozího akordu pro smooth voicing.

        Returns:
            List[int]: MIDI noty předchozího akordu
        """
        return self.previous_chord_midi.copy() if self.previous_chord_midi else []

    def reset_state(self, keep_settings: bool = True) -> None:
        """
        Resetuje stav aplikace do výchozího stavu.

        Args:
            keep_settings: Pokud True, zachová uživatelská nastavení (voicing, MIDI)
        """
        # Vyčistí data
        self.current_analysis.clear()
        self.last_displayed_chord = None
        self.current_progression_chords.clear()
        self.current_progression_index = 0
        self.current_progression_source = None
        self.previous_chord_midi.clear()
        self.last_played_chord = None

        if not keep_settings:
            # Resetuje i uživatelská nastavení
            self.voicing_type = "root"
            self.midi_enabled = False
            self.midi_velocity = AppConfig.DEFAULT_MIDI_VELOCITY

        self.log("Stav aplikace resetován")

        if self.on_state_changed:
            self.on_state_changed("reset", None, None)

    def reset_voicing_state(self) -> None:
        """
        Resetuje pouze stav související s voicingem.
        Užitečné při změně typu voicingu.
        """
        self.previous_chord_midi.clear()
        self.last_played_chord = None
        self.log("Stav voicingu resetován")

    def log(self, message: str) -> None:
        """
        Přidá zprávu do logu s timestampem.

        Args:
            message: Zpráva k zalogování
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.log_messages.append(formatted_msg)

        # Loguje i do systémového loggeru
        logger.info(message)

    def get_log_content(self) -> str:
        """
        Vrací celý obsah logu jako string.

        Returns:
            str: Obsah logu oddělený novými řádky
        """
        return '\n'.join(self.log_messages)

    def get_recent_log_entries(self, count: int = 10) -> List[str]:
        """
        Vrací posledních N záznamů z logu.

        Args:
            count: Počet posledních záznamů

        Returns:
            List[str]: Seznam posledních log záznamů
        """
        return self.log_messages[-count:] if count > 0 else []

    def clear_log(self) -> None:
        """Vymaže historii logu."""
        old_count = len(self.log_messages)
        self.log_messages.clear()
        self.log(f"Log vymazán ({old_count} záznamů)")

    def export_log(self, filepath: str) -> bool:
        """
        Exportuje log do textového souboru.

        Args:
            filepath: Cesta k výstupnímu souboru

        Returns:
            bool: True při úspěšném exportu
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.get_log_content())
            self.log(f"Log exportován do: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Chyba při exportu logu: {e}")
            return False

    def get_state_summary(self) -> Dict[str, Any]:
        """
        Vrací shrnutí aktuálního stavu pro debugging a monitoring.

        Returns:
            Dict[str, Any]: Slovník s klíčovými stavy aplikace
        """
        return {
            # Základní stavy
            "voicing_type": self.voicing_type,
            "midi_enabled": self.midi_enabled,
            "midi_velocity": self.midi_velocity,

            # Akord stav
            "last_displayed_chord": self.last_displayed_chord,
            "last_played_chord": self.last_played_chord,
            "has_current_analysis": bool(self.current_analysis),

            # Progrese stav
            "current_chord": self.get_current_chord(),
            "progression_length": len(self.current_progression_chords),
            "progression_index": self.current_progression_index,
            "progression_source": self.current_progression_source,

            # MIDI a voicing stav
            "has_previous_midi": bool(self.previous_chord_midi),
            "previous_chord_midi_count": len(self.previous_chord_midi),
            "should_use_smooth": self.should_use_previous_chord_for_smooth(),

            # Log stav
            "log_entries_count": len(self.log_messages),
            "log_last_entry": self.log_messages[-1] if self.log_messages else None,
        }

    def validate_state(self) -> Dict[str, Any]:
        """
        Validuje konzistenci stavu aplikace.

        Returns:
            Dict[str, Any]: Výsledky validace s případnými problémy
        """
        issues = []
        warnings = []

        # Validace voicing typu
        if self.voicing_type not in ["root", "smooth", "drop2"]:
            issues.append(f"Neplatný voicing_type: {self.voicing_type}")

        # Validace MIDI velocity
        if not (0 <= self.midi_velocity <= 127):
            issues.append(f"MIDI velocity mimo rozsah: {self.midi_velocity}")

        # Validace indexu progrese
        if self.current_progression_chords:
            if not (0 <= self.current_progression_index < len(self.current_progression_chords)):
                issues.append(f"Index progrese mimo rozsah: {self.current_progression_index}")
        elif self.current_progression_index != 0:
            warnings.append("Index progrese není 0 i když není progrese")

        # Validace MIDI not
        for note in self.previous_chord_midi:
            if not (21 <= note <= 108):  # 88-klávesy rozsah
                warnings.append(f"MIDI nota mimo standardní rozsah: {note}")

        # Validace konzistence smooth voicingu
        if self.voicing_type == "smooth" and not self.previous_chord_midi and self.last_played_chord:
            warnings.append("Smooth voicing je aktivní ale chybí předchozí MIDI noty")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "validation_time": datetime.now().isoformat()
        }

    def _notify_state_changed(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """
        Interní metoda pro notifikace o změnách stavu.

        Args:
            property_name: Název změněné vlastnosti
            old_value: Stará hodnota
            new_value: Nová hodnota
        """
        if self.on_state_changed:
            try:
                self.on_state_changed(property_name, old_value, new_value)
            except Exception as e:
                logger.error(f"Chyba v callback on_state_changed: {e}")

    def backup_state(self) -> Dict[str, Any]:
        """
        Vytvoří zálohu aktuálního stavu pro případné obnovení.

        Returns:
            Dict[str, Any]: Serializovatelná záloha stavu
        """
        return {
            "voicing_type": self.voicing_type,
            "midi_enabled": self.midi_enabled,
            "midi_velocity": self.midi_velocity,
            "last_displayed_chord": self.last_displayed_chord,
            "current_progression_chords": self.current_progression_chords.copy(),
            "current_progression_index": self.current_progression_index,
            "current_progression_source": self.current_progression_source,
            "previous_chord_midi": self.previous_chord_midi.copy(),
            "last_played_chord": self.last_played_chord,
            "log_messages": self.log_messages.copy(),
            "backup_timestamp": datetime.now().isoformat()
        }

    def restore_state(self, backup: Dict[str, Any]) -> bool:
        """
        Obnoví stav ze zálohy.

        Args:
            backup: Záloha stavu z backup_state()

        Returns:
            bool: True při úspěšném obnovení
        """
        try:
            # Obnoví základní nastavení
            self.voicing_type = backup.get("voicing_type", "root")
            self.midi_enabled = backup.get("midi_enabled", False)
            self.midi_velocity = backup.get("midi_velocity", AppConfig.DEFAULT_MIDI_VELOCITY)

            # Obnoví stav akordů
            self.last_displayed_chord = backup.get("last_displayed_chord")
            self.last_played_chord = backup.get("last_played_chord")
            self.previous_chord_midi = backup.get("previous_chord_midi", []).copy()

            # Obnoví progrese
            self.current_progression_chords = backup.get("current_progression_chords", []).copy()
            self.current_progression_index = backup.get("current_progression_index", 0)
            self.current_progression_source = backup.get("current_progression_source")

            # Obnoví log (volitelně)
            if "log_messages" in backup:
                self.log_messages = backup["log_messages"].copy()

            backup_time = backup.get("backup_timestamp", "unknown")
            self.log(f"Stav obnoven ze zálohy z {backup_time}")

            return True

        except Exception as e:
            logger.error(f"Chyba při obnově stavu: {e}")
            return False

    def get_settings_dict(self) -> Dict[str, Any]:
        """
        Vrací pouze uživatelská nastavení pro uložení do konfigurace.

        Returns:
            Dict[str, Any]: Slovník s nastavením uživatele
        """
        return {
            "voicing_type": self.voicing_type,
            "midi_enabled": self.midi_enabled,
            "midi_velocity": self.midi_velocity
        }

    def load_settings_dict(self, settings: Dict[str, Any]) -> None:
        """
        Načte uživatelská nastavení ze slovníku.

        Args:
            settings: Slovník s nastavením uživatele
        """
        if "voicing_type" in settings:
            self.set_voicing_type(settings["voicing_type"])

        if "midi_enabled" in settings:
            self.set_midi_enabled(settings["midi_enabled"])

        if "midi_velocity" in settings:
            self.set_midi_velocity(settings["midi_velocity"])

        self.log("Uživatelská nastavení načtena")


class StateManager:
    """
    Statický manager pro práci s globálním stavem aplikace.
    Užitečné pro situace kdy potřebujeme přístup ke stavu z různých částí aplikace.
    """

    _instance: Optional[ApplicationState] = None

    @classmethod
    def get_instance(cls) -> ApplicationState:
        """
        Vrací singleton instanci ApplicationState.

        Returns:
            ApplicationState: Globální instance stavu
        """
        if cls._instance is None:
            cls._instance = ApplicationState()
            logger.info("Vytvořena globální instance ApplicationState")

        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resetuje singleton instanci - užitečné pro testy."""
        cls._instance = None
        logger.info("Globální instance ApplicationState resetována")


if __name__ == "__main__":
    # Jednoduché testování ApplicationState
    print("=== Test ApplicationState ===")

    # Test základních funkcí
    print("\n1. Inicializace a základní funkce:")
    state = ApplicationState()
    print(f"Výchozí voicing: {state.get_voicing_type()}")
    print(f"MIDI zapnuto: {state.midi_enabled}")

    # Test změn stavu
    print("\n2. Test změn stavu:")
    state.set_voicing_type("smooth")
    state.set_midi_enabled(True)
    state.set_midi_velocity(80)
    print(f"Nový voicing: {state.get_voicing_type()}")
    print(f"MIDI velocity: {state.midi_velocity}")

    # Test progrese
    print("\n3. Test progrese:")
    test_chords = ["Cmaj7", "Am7", "Dm7", "G7"]
    state.load_progression(test_chords, "Test progrese")
    print(f"Načtena progrese: {len(state.current_progression_chords)} akordů")
    print(f"Aktuální akord: {state.get_current_chord()}")

    state.step_progression(1)
    print(f"Po kroku: {state.get_current_chord()}")

    state.jump_to_chord_index(3)
    print(f"Po skoku na index 3: {state.get_current_chord()}")

    # Test validace
    print("\n4. Test validace:")
    validation = state.validate_state()
    print(f"Stav je platný: {validation['is_valid']}")
    if validation['warnings']:
        print(f"Varování: {validation['warnings']}")

    # Test zálohy
    print("\n5. Test zálohy a obnovy:")
    backup = state.backup_state()
    print(f"Záloha vytvořena v: {backup['backup_timestamp']}")

    # Změna stavu
    state.set_voicing_type("drop2")
    print(f"Změněn voicing na: {state.get_voicing_type()}")

    # Obnova
    state.restore_state(backup)
    print(f"Obnovený voicing: {state.get_voicing_type()}")

    # Test logu
    print("\n6. Test logu:")
    print(f"Počet log záznamů: {len(state.log_messages)}")
    recent = state.get_recent_log_entries(3)
    print("Poslední 3 záznamy:")
    for entry in recent:
        print(f"  {entry}")

    # Test singleton
    print("\n7. Test StateManager singleton:")
    global_state = StateManager.get_instance()
    global_state2 = StateManager.get_instance()
    print(f"Singleton funguje: {global_state is global_state2}")

    print("\n=== Test dokončen ===")
