# AnnoQ

AnnoQ is a small desktop tool for browsing and labeling image datasets in the YOLO format. It loads a `data.yaml` file and lets you step through each split, draw boxes and save them back out to disk.

## Installation

The project uses Python 3 and Tkinter. Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the viewer and point it at a YOLO `data.yaml` file:

```bash
python main.py --yaml path/to/data.yaml
```

When the program starts you can pick a dataset split from the drop-down list. Use the arrow buttons or the keyboard arrow keys to move between images.

Drag with the left mouse button to create a box. The mouse wheel scales a selected box, and dragging a box moves it. Right-click to change the class. Use the *Save* button to write the labels and *Clear Labels* to remove all annotations for the current image. The *Show Stats* button prints a quick summary of the dataset.

Zooming, panning and a crosshair overlay are provided to make precise editing easier. Files are saved in standard YOLO text format next to the images.
