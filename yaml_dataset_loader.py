import os
import yaml

class YamlDatasetLoader:
    def __init__(self, yaml_path):
        self.yaml_path = yaml_path
        self.root_dir = os.path.dirname(yaml_path)
        print(f"file dir: {self.root_dir}")
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        self.class_names = data['names']
        print(f"class names: {self.class_names}")
        self.datasets = {}

        for split in ['train', 'val', 'test']:
            if split in data:
                split_path = data[split]
                if os.path.isabs(split_path):
                    images_path = os.path.abspath(split_path)
                else:
                    images_path = os.path.abspath(os.path.join(self.root_dir, split_path))
                labels_path = images_path.replace("images", "labels")
                print(f"datasets:{split} -> {split_path} / {images_path} / {labels_path}")
                if os.path.isdir(images_path) and os.path.isdir(labels_path):
                    print("Adding dataset keys")
                    self.datasets[split] = {
                        "images": images_path,
                        "labels": labels_path
                    }
        print(f"datasets: {self.datasets}")

    def get_dataset_splits(self):
        return list(self.datasets.keys())

    def get_class_names(self):
        return self.class_names

    def get_paths(self, split):
        return self.datasets.get(split)
