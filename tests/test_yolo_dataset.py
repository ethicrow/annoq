import os
import tempfile
from yolo_dataset import YoloDataset

def test_set_index():
    with tempfile.TemporaryDirectory() as tmpdir:
        img_dir = os.path.join(tmpdir, 'images')
        lbl_dir = os.path.join(tmpdir, 'labels')
        os.makedirs(img_dir)
        os.makedirs(lbl_dir)
        for i in range(5):
            open(os.path.join(img_dir, f'image_{i}.jpg'), 'w').close()
            open(os.path.join(lbl_dir, f'image_{i}.txt'), 'w').close()
        dataset = YoloDataset(img_dir, lbl_dir, [])
        assert dataset.total_images() == 5
        dataset.set_index(3)
        assert dataset.current_index() == 3
        dataset.set_index(10)
        assert dataset.current_index() == 3
        dataset.set_index(-1)
        assert dataset.current_index() == 3

def test_delete_current():
    with tempfile.TemporaryDirectory() as tmpdir:
        img_dir = os.path.join(tmpdir, 'images')
        lbl_dir = os.path.join(tmpdir, 'labels')
        os.makedirs(img_dir)
        os.makedirs(lbl_dir)
        for i in range(3):
            open(os.path.join(img_dir, f'image_{i}.jpg'), 'w').close()
            open(os.path.join(lbl_dir, f'image_{i}.txt'), 'w').close()
        dataset = YoloDataset(img_dir, lbl_dir, [])
        dataset.set_index(1)
        dataset.delete_current()
        assert dataset.total_images() == 2
        assert dataset.current_index() == 1
        deleted_dir = os.path.join(tmpdir, '.deleted')
        assert os.path.isdir(deleted_dir)
        assert os.path.exists(os.path.join(deleted_dir, 'image_1.jpg'))
        assert os.path.exists(os.path.join(deleted_dir, 'image_1.txt'))
        assert not os.path.exists(os.path.join(img_dir, 'image_1.jpg'))
        assert not os.path.exists(os.path.join(lbl_dir, 'image_1.txt'))
