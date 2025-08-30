# piano_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional

from constants import MusicalConstants, ChordLibrary
from piano_keyboard import ArchetypeKeyboard
from harmony_analyzer import HarmonyAnalyzer
from jazz_database import JazzStandardsDatabase

# --- DEBUG ---
DEBUG = True


class PianoGUI:
    """Hlavni trida pro GUI aplikace Piano Harmony Analyzer."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Piano Chord Analyzer")
        self.root.geometry("1000x750")

        self.current_analysis: Dict[str, Any] = {}
        self.prev_chord_midi: List[int] = []
        self.current_progression_chords: List[str] = []
        self.current_progression_index = 0
        self.last_displayed_chord_name: Optional[str] = None
        self.prog_tree_data: Dict[str, Dict] = {}
        self.smooth_var = tk.IntVar(value=0)

        self.root.rowconfigure(0, weight=2)
        self.root.rowconfigure(1, weight=0)
        self.root.rowconfigure(2, weight=3)
        self.root.columnconfigure(0, weight=1)

        self._init_keyboard_frame()
        self._init_input_frame()
        self._init_output_notebook()

        self.root.bind('<Return>', lambda e: self._analyze_harmony())
        self.root.bind('<Left>', lambda e: self._step_progression(-1))
        self.root.bind('<Right>', lambda e: self._step_progression(1))

    def run(self):
        self.root.mainloop()

    # ZMENA: Tato metoda byla upravena pro vystředění klávesnice.
    def _init_keyboard_frame(self):
        """Inicializuje horni cast s klaviaturou, ktera je nyni vzdy vystredena."""
        keyboard_frame = ttk.Frame(self.root, padding=10)
        keyboard_frame.grid(row=0, column=0, sticky="ew")  # Rámeček se roztahuje

        # Konfigurace sloupce v rámečku, aby se jeho obsah (plátno) centroval
        keyboard_frame.columnconfigure(0, weight=1)

        # Vypočet přesné šířky klaviatury (88 kláves má 52 bílých)
        keyboard_width = 52 * MusicalConstants.WHITE_KEY_WIDTH
        keyboard_height = 100  # Dostatečná výška

        # Vytvoření plátna s fixní šířkou
        canvas = tk.Canvas(keyboard_frame, width=keyboard_width, height=keyboard_height, bg="lightgray")

        # Plátno se umístí doprostřed svého rámečku (sticky NENÍ "ew")
        canvas.grid(row=0, column=0, pady=10)

        # Odstraněn posuvník (Scrollbar)

        self.keyboard = ArchetypeKeyboard(canvas, MusicalConstants.ARCHETYPE_SIZE)
        self.keyboard.draw()
        self.canvas = canvas

    def _init_input_frame(self):
        input_frame = ttk.Labelframe(self.root, text="Ovládání", padding=10)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        ttk.Label(input_frame, text="Akord:").pack(side=tk.LEFT, padx=(0, 5))
        self.chord_entry = ttk.Entry(input_frame, width=15)
        self.chord_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Analyzovat", command=self._analyze_harmony).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(input_frame, text="Smooth Voicings", variable=self.smooth_var,
                        command=self._on_smooth_voicing_toggle).pack(side=tk.LEFT, padx=10)
        separator = ttk.Separator(input_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill='y', padx=15, pady=5)
        ttk.Button(input_frame, text="Reset", command=self._reset_gui).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Exportovat Log", command=self._export_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Kopírovat Log", command=self._copy_results).pack(side=tk.LEFT, padx=5)
        pass

    def _on_smooth_voicing_toggle(self):
        if self.last_displayed_chord_name:
            if DEBUG:
                state = "ON" if self.smooth_var.get() == 1 else "OFF"
                self._log(f"Smooth Voicing prepnuto na: {state}. Prekresluji akord.")
            self._display_chord(self.last_displayed_chord_name)
        pass

    def _init_output_notebook(self):
        notebook_frame = ttk.Frame(self.root, padding=10)
        notebook_frame.grid(row=2, column=0, sticky="nsew")
        notebook_frame.rowconfigure(0, weight=1)
        notebook_frame.columnconfigure(0, weight=1)
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        analysis_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(analysis_tab, text="Analysis")
        self._create_analysis_tab(analysis_tab)
        prog_player_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(prog_player_tab, text="Progression Player")
        self._create_prog_player_tab(prog_player_tab)
        log_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_tab, text="Log")
        self._create_log_tab(log_tab)
        pass

    def _create_analysis_tab(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)
        chord_info_frame = ttk.Labelframe(parent, text="Chord Info", padding=10)
        chord_info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.chord_name_label = ttk.Label(chord_info_frame, text="Akord: -", font=("Segoe UI", 10, "bold"))
        self.chord_name_label.pack(anchor="w")
        self.chord_notes_label = ttk.Label(chord_info_frame, text="Noty: -")
        self.chord_notes_label.pack(anchor="w")
        prog_frame = ttk.Labelframe(parent, text="Real Progressions (from Jazz Standards)", padding=10)
        prog_frame.grid(row=1, column=0, sticky="nsew")
        prog_frame.rowconfigure(0, weight=1)
        prog_frame.columnconfigure(0, weight=1)
        # NOVÉ: Přidán sloupec "Transposed"
        cols = ("Progression", "Description", "Song", "Transposed")
        self.prog_tree = ttk.Treeview(prog_frame, columns=cols, show="headings")
        for col in cols:
            self.prog_tree.heading(col, text=col)
            self.prog_tree.column(col, width=150 if col == "Progression" else 100, anchor="w")
        self.prog_tree.grid(row=0, column=0, sticky="nsew")
        self.prog_tree.bind("<<TreeviewSelect>>", self._on_prog_select)
        pass

    def _create_prog_player_tab(self, parent):
        parent.rowconfigure(0, weight=0)
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)
        select_frame = ttk.Frame(parent, padding=5)
        select_frame.grid(row=0, column=0, sticky="ew")
        self.song_combo = ttk.Combobox(select_frame, values=JazzStandardsDatabase.get_all_songs(), width=30)  # NOVÉ: Zahrne transponované
        self.song_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="Nahrát celou píseň", command=self._load_progression_from_combo).pack(side=tk.LEFT, padx=5)
        self.prog_chord_frame = ttk.Frame(parent, padding=10)
        self.prog_chord_frame.grid(row=1, column=0, sticky="nsew")
        pass

    def _create_log_tab(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.log_text = tk.Text(parent, wrap="word", height=10)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(parent, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)
        pass

    def _reset_gui(self):
        self.keyboard.clear_highlights()
        self.chord_entry.delete(0, tk.END)
        self.chord_name_label.config(text="Akord: -")
        self.chord_notes_label.config(text="Noty: -")
        for item in self.prog_tree.get_children():
            self.prog_tree.delete(item)
        self.prog_tree_data.clear()
        self.current_analysis = {}
        self.prev_chord_midi = []
        self.current_progression_chords = []
        self.current_progression_index = 0
        self.last_displayed_chord_name = None
        for widget in self.prog_chord_frame.winfo_children():
            widget.destroy()
        self.log_text.delete(1.0, tk.END)
        self.smooth_var.set(0)
        self._log("GUI resetováno.")
        pass

    def _log(self, message: str):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        if DEBUG:
            print(message)
        pass

    def _analyze_harmony(self):
        chord_full_name = self.chord_entry.get().strip()
        if not chord_full_name:
            messagebox.showwarning("Vstup", "Zadejte název akordu (např. Cm7 nebo G).")
            return
        try:
            # NOVÉ: Parsování chord_full_name před voláním analyze pro správné argumenty
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_full_name)
            self.current_analysis = HarmonyAnalyzer.analyze(base_note, chord_type)
            self._update_analysis_tab(self.current_analysis)
            self._display_chord(chord_full_name)
            self._log(f"Analýza dokončena pro akord: {chord_full_name}")
        except ValueError as e:
            # NOVÉ: Lepší handling chyb parsování (pro čitelnost a uživatelskou přívětivost)
            messagebox.showerror("Chyba analýzy", f"Neplatný akord: {str(e)}")
            self._log(f"CHYBA parsování/analýzy: {e}")
        except TypeError as e:
            messagebox.showerror("Chyba analýzy", str(e))
            self._log(f"CHYBA analýzy: {e}")
        pass

    def _update_analysis_tab(self, analysis: Dict[str, Any]):
        self.chord_name_label.config(text=f"Akord: {analysis['chord_name']}")
        self.chord_notes_label.config(text=f"Noty: {' - '.join(analysis['chord_notes'])}")
        for item in self.prog_tree.get_children():
            self.prog_tree.delete(item)
        self.prog_tree_data.clear()
        real_progs = analysis.get("real_progressions", [])
        if real_progs:
            for prog in real_progs:
                prog_chords_str = " -> ".join(prog['chords'])
                transposed_by = prog.get('transposed_by', 0)
                transposed_info = "Original" if transposed_by == 0 else f"By +{transposed_by} (key: {prog.get('transposed_key', '')})"
                # NOVÉ: Přidání transposed_info do values
                values = (prog_chords_str, prog['description'], prog['song'], transposed_info)
                iid = self.prog_tree.insert("", "end", values=values)
                self.prog_tree_data[iid] = prog
        else:
            self._log("Žádné reálné progrese nebyly nalezeny.")
        pass

    def _on_prog_select(self, event):
        selected = self.prog_tree.selection()
        if not selected:
            return
        iid = selected[0]
        prog_data = self.prog_tree_data.get(iid)
        if prog_data:
            self._load_specific_progression(prog_data['chords'], prog_data['song'])
        pass

    def _load_specific_progression(self, chords: List[str], song_name: str):
        self.current_progression_chords = chords
        self.current_progression_index = 0
        self._create_progression_buttons()
        self._update_progression_display()
        self._log(f"Nahrána progrese z písně: {song_name} (chords: {chords})")
        pass

    def _load_progression_from_combo(self):
        song_name = self.song_combo.get()
        if not song_name or song_name.startswith("Nahráno:"):
            messagebox.showinfo("Výběr", "Vyberte píseň ze seznamu pro nahrání celé skladby.")
            return
        song_data = JazzStandardsDatabase.get_song_info(song_name)
        if not song_data: return
        all_chords = [chord for prog in song_data["progressions"] for chord in prog["chords"]]
        self._load_specific_progression(all_chords, song_name)
        pass

    def _create_progression_buttons(self):
        for widget in self.prog_chord_frame.winfo_children(): widget.destroy()
        if not self.current_progression_chords: return
        control_frame = ttk.Frame(self.prog_chord_frame)
        control_frame.pack(fill="x", pady=5)
        ttk.Button(control_frame, text="<< Prev", command=lambda: self._step_progression(-1)).pack(side=tk.LEFT, padx=5)
        self.current_chord_label = ttk.Label(control_frame, text="-", font=("Segoe UI", 12, "bold"), width=15,
                                             anchor="center")
        self.current_chord_label.pack(side=tk.LEFT, expand=True, fill="x")
        ttk.Button(control_frame, text="Next >>", command=lambda: self._step_progression(1)).pack(side=tk.LEFT, padx=5)
        buttons_frame = ttk.Frame(self.prog_chord_frame)
        buttons_frame.pack(fill="both", expand=True)
        self.prog_chord_buttons = []
        for i, chord in enumerate(self.current_progression_chords):
            btn = ttk.Button(buttons_frame, text=chord, command=lambda idx=i: self._jump_to_chord(idx))
            btn.grid(row=i // 8, column=i % 8, padx=2, pady=2, sticky="ew")
            self.prog_chord_buttons.append(btn)
        pass

    def _step_progression(self, step: int):
        if not self.current_progression_chords: return
        new_index = self.current_progression_index + step
        if 0 <= new_index < len(self.current_progression_chords):
            self.current_progression_index = new_index
            self._update_progression_display()
        elif new_index >= len(self.current_progression_chords):
            self._log("Konec progrese.")
        else:
            self._log("Začátek progrese.")
        pass

    def _jump_to_chord(self, index: int):
        self.current_progression_index = index
        self._update_progression_display()
        pass

    def _update_progression_display(self):
        if not self.current_progression_chords: return
        style_name = "Accent.TButton"
        style = ttk.Style()
        style.configure(style_name, foreground="blue", font=('Segoe UI', 9, 'bold'))
        for i, btn in enumerate(self.prog_chord_buttons):
            btn.configure(style=style_name if i == self.current_progression_index else "TButton")
        current_chord = self.current_progression_chords[self.current_progression_index]
        self.current_chord_label.config(text=current_chord)
        self._display_chord(current_chord)
        self._log(f"Zobrazen akord: {current_chord}")
        pass

    def _display_chord(self, chord_full_name: str):
        try:
            self.last_displayed_chord_name = chord_full_name
            base_note, chord_type = HarmonyAnalyzer.parse_chord_name(chord_full_name)
            smooth = self.smooth_var.get() == 1

            if smooth:
                midi_notes = ChordLibrary.get_smooth_voicing(base_note, chord_type, self.prev_chord_midi)
            else:
                midi_notes = ChordLibrary.get_root_voicing(base_note, chord_type)

            self.prev_chord_midi = sorted(midi_notes)
            keys_to_highlight = [ChordLibrary.midi_to_key_nr(note) for note in midi_notes]
            color = "green" if smooth else "red"
            self.keyboard.draw(keys_to_highlight, color=color)

            # ZMENA: Odstraněno posouvání pohledu, protože již není potřeba
            # if keys_to_highlight:
            #     first_key_x = self.keyboard.keys[min(keys_to_highlight)].bbox[0]
            #     self.canvas.xview_moveto(...)

        except (ValueError, IndexError) as e:
            self.last_displayed_chord_name = None
            messagebox.showerror("Chyba zobrazení", str(e))
            self._log(f"CHYBA zobrazení: {e}")
            self.keyboard.clear_highlights()

    def _export_results(self):
        content = self.log_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Export", "Není co exportovat z logu.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Export", f"Log byl úspěšně uložen do: {file_path}")
            except IOError as e:
                messagebox.showerror("Chyba při ukládání", str(e))
        pass

    def _copy_results(self):
        content = self.log_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Kopírování", "Není co kopírovat z logu.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Kopírování", "Obsah logu byl zkopírován do schránky.")
        pass