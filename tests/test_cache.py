import json
import cache

def test_cache_max_entries(tmp_path, monkeypatch):
    tmp_file = tmp_path / "cache.json"
    monkeypatch.setattr(cache, "CACHE_PATH", str(tmp_file))
    # ensure starting empty
    assert cache.get_cached_index("a.yaml") is None
    cache.update_cache("a.yaml", 1)
    assert cache.get_cached_index("a.yaml") == 1
    # add 11 more entries to exceed limit
    for i in range(11):
        cache.update_cache(f"file{i}.yaml", i)
    with open(tmp_file) as f:
        data = json.load(f)
    assert len(data) == 10
    # 'a.yaml' should be evicted
    assert cache.get_cached_index("a.yaml") is None
    # latest entry should be present
    assert cache.get_cached_index("file10.yaml") == 10
