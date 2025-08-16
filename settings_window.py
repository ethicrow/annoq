import json
import os
import tkinter as tk

SETTINGS_DIR = os.path.join(os.path.dirname(__file__), '.settings')
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'keybindings.json')

# Default mappings use Tk's event notation for both keys and mouse buttons.
DEFAULT_BINDINGS = {
    'prev_image': ['<Left>'],
    'next_image': ['<Right>'],
    'save_labels': ['<Control-s>'],
}

def ensure_settings_dir():
    os.makedirs(SETTINGS_DIR, exist_ok=True)

def load_keybindings():
    """Load key or mouse-button bindings from the settings file."""
    ensure_settings_dir()
    bindings = {action: keys[:] for action, keys in DEFAULT_BINDINGS.items()}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            for action, defaults in DEFAULT_BINDINGS.items():
                extra = data.get(action, [])
                bindings[action] = list(dict.fromkeys(defaults + extra))
            for action, extra in data.items():
                if action not in bindings:
                    bindings[action] = extra
        except Exception:
            pass
    return bindings

def save_keybindings(bindings):
    """Save key or mouse-button bindings to the settings file."""
    ensure_settings_dir()
    merged = {}
    for action, defaults in DEFAULT_BINDINGS.items():
        extra = bindings.get(action, [])
        merged[action] = list(dict.fromkeys(defaults + extra))
    for action, extra in bindings.items():
        if action not in merged:
            merged[action] = extra
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(merged, f, indent=2)
    return merged

class SettingsWindow(tk.Toplevel):
    """A simple settings window to edit key/mouse bindings."""
    def __init__(self, master, bindings, callback=None):
        super().__init__(master)
        self.title('Settings')
        self.callback = callback
        self.entries = {}

        row = 0
        for action, keys in bindings.items():
            tk.Label(self, text=action).grid(row=row, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(self, width=25)
            entry.insert(0, ', '.join(keys))
            entry.grid(row=row, column=1, padx=5, pady=5)
            self.entries[action] = entry
            row += 1

        tk.Button(self, text='Save', command=self.save).grid(
            row=row, column=0, columnspan=2, pady=10
        )

    def save(self):
        new_bindings = {}
        for action, entry in self.entries.items():
            keys = [k.strip() for k in entry.get().split(',') if k.strip()]
            new_bindings[action] = keys
        merged = save_keybindings(new_bindings)
        if self.callback:
            self.callback(merged)
        self.destroy()
