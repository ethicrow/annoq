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

    # Save custom key and mouse-button bindings and ensure defaults persist
    sw.save_keybindings({'prev_image': ['a', '<Button-1>']})
    bindings = sw.load_keybindings()
    assert '<Left>' in bindings['prev_image']
    assert 'a' in bindings['prev_image']
    assert '<Button-1>' in bindings['prev_image']

    # Attempt to remove default key; it should remain
    sw.save_keybindings({'prev_image': []})
    bindings = sw.load_keybindings()
    assert '<Left>' in bindings['prev_image']
    assert '<Button-1>' not in bindings['prev_image']
