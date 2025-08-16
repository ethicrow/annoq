import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
import settings_window as sw


def test_default_bindings_retained(tmp_path, monkeypatch):
    settings_dir = tmp_path / '.settings'
    settings_file = settings_dir / 'keybindings.json'
    monkeypatch.setattr(sw, 'SETTINGS_DIR', str(settings_dir))
    monkeypatch.setattr(sw, 'SETTINGS_FILE', str(settings_file))

    # Load when file doesn't exist -> defaults
    bindings = sw.load_keybindings()
    assert bindings == sw.DEFAULT_BINDINGS

    # Save custom binding and ensure defaults persist
    sw.save_keybindings({'prev_image': ['a']})
    bindings = sw.load_keybindings()
    assert '<Left>' in bindings['prev_image']
    assert 'a' in bindings['prev_image']

    # Attempt to remove default key; it should remain
    sw.save_keybindings({'prev_image': []})
    bindings = sw.load_keybindings()
    assert '<Left>' in bindings['prev_image']


def test_invalid_button_filtered(tmp_path, monkeypatch):
    settings_dir = tmp_path / '.settings'
    settings_file = settings_dir / 'keybindings.json'
    monkeypatch.setattr(sw, 'SETTINGS_DIR', str(settings_dir))
    monkeypatch.setattr(sw, 'SETTINGS_FILE', str(settings_file))

    sw.save_keybindings({'save_labels': ['<Button-9>']})
    bindings = sw.load_keybindings()
    assert '<Button-9>' not in bindings['save_labels']
    assert '<Control-s>' in bindings['save_labels']
