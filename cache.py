import json
import os

CACHE_PATH = os.path.join(os.path.expanduser("~"), ".annoq_cache.json")
MAX_ENTRIES = 10


def _read_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def _write_cache(entries):
    with open(CACHE_PATH, "w") as f:
        json.dump(entries, f)


def get_cached_index(yaml_path):
    yaml_path = os.path.abspath(yaml_path)
    entries = _read_cache()
    for entry in entries:
        if entry.get("yaml") == yaml_path:
            return entry.get("index")
    return None


def update_cache(yaml_path, index):
    yaml_path = os.path.abspath(yaml_path)
    entries = _read_cache()
    entries = [e for e in entries if e.get("yaml") != yaml_path]
    entries.append({"yaml": yaml_path, "index": index})
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    _write_cache(entries)
