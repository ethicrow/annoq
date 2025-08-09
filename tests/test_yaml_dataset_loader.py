import os
import sys
import yaml

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from yaml_dataset_loader import YamlDatasetLoader


def test_absolute_paths(tmp_path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()
    yaml_path = tmp_path / "data.yaml"
    yaml_content = {
        "train": str(images_dir),
        "names": ["cls"],
    }
    yaml_path.write_text(yaml.dump(yaml_content))
    loader = YamlDatasetLoader(str(yaml_path))
    assert "train" in loader.get_dataset_splits()
    paths = loader.get_paths("train")
    assert paths["images"] == str(images_dir)
    assert paths["labels"] == str(labels_dir)
