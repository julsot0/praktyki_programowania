import os
import random
import shutil
import yaml
import xml.etree.ElementTree as ET
from sklearn.model_selection import train_test_split


# adnotacje i zdjecia
annotations_file = os.path.join(os.getcwd(), 'annotations.xml')
photos_dir = os.path.join(os.getcwd(), 'photos')
base_dir = os.getcwd()

def create_yolo_directory_structure(base_path: str) -> dict:
    datasets_dir = os.path.join(base_path, 'datasets')
    
    dirs = {
        'images_train': os.path.join(datasets_dir, 'images', 'train'),
        'images_val': os.path.join(datasets_dir, 'images', 'val'),
        'labels_train': os.path.join(datasets_dir, 'labels', 'train'),
        'labels_val': os.path.join(datasets_dir, 'labels', 'val'),
        'datasets': datasets_dir
    }
    
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs


def parse_xml_annotations(xml_file: str) -> list:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    data_items = []
    
    for image in root.findall('image'):
        file_name = image.get('name')
        width = float(image.get('width'))
        height = float(image.get('height'))
        
        box = image.find("box[@label='plate']")
        if box is None:
            continue
        
        left_x = float(box.get('xtl'))
        top_y = float(box.get('ytl'))
        right_x = float(box.get('xbr'))
        bottom_y = float(box.get('ybr'))
        yolo_line = convert_to_yolo_format(left_x, top_y, right_x, bottom_y, width, height)
        
        data_items.append({
            'file_name': file_name,
            'yolo_line': yolo_line
        })
    return data_items


def convert_to_yolo_format(left_x: float, top_y: float, right_x: float, bottom_y: float, 
                          width: float, height: float) -> str:
    # konwertuje bbox do formatu YOLO (normalizuje współrzędne)
    dw = 1.0 / width
    dh = 1.0 / height
    
    x_center = (left_x + right_x) / 2.0
    y_center = (top_y + bottom_y) / 2.0
    w = right_x - left_x
    h = bottom_y - top_y
    
    x_center *= dw
    width_norm = w * dw
    y_center *= dh
    height_norm = h * dh
    
    return f"0 {x_center:.6f} {y_center:.6f} {width_norm:.6f} {height_norm:.6f}"

def process_dataset_subset(dataset, images_dir, 
                          images_dest, labels_dest):
    # przetwarza podzbiór danych - kopiuje obrazy i tworzy pliki txt z etykietami
    for item in dataset:
        filename = item["file_name"]
        src_path = os.path.join(images_dir, filename)

        if src_path and os.path.exists(src_path):
            shutil.copy(src_path, os.path.join(images_dest, filename))
            txt_name = os.path.splitext(filename)[0] + ".txt"
            txt_path = os.path.join(labels_dest, txt_name)
            
            with open(txt_path, "w") as f:
                f.write(item['yolo_line'])


def create_yaml_config(datasets_dir: str) -> None:
    # tworzy plik data.yaml z konfiguracją dla YOLO
    yaml_content = {
        'path': datasets_dir,
        'train': 'images/train',
        'val': 'images/val',
        'names': {0: 'license_plate'}
    }
    with open('data.yaml', 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)


def convert_to_yolo():
    # główna funkcja konwertująca dane z XML do YOLO
    print("konwersja do YOLO")
    
    dirs = create_yolo_directory_structure(base_dir)
    data_items = parse_xml_annotations(annotations_file)
    
    if not data_items:
        print("Brak danych xml")
        return
    
    # train/val
    train_set, val_set = train_test_split(
        data_items,
        test_size=0.3, # TEST SIZE 0.3
        random_state=42)
    
    print(f"Znaleziono {len(data_items)} próbek.")
    print(f"Trening: {len(train_set)}, Walidacja: {len(val_set)}")
    
    # zbior treningowy
    process_dataset_subset(train_set, photos_dir, dirs['images_train'], dirs['labels_train'])
    # zbior walidacyjny
    process_dataset_subset(val_set, photos_dir, dirs['images_val'], dirs['labels_val'])
    
    # stworzenie YAMLa
    create_yaml_config(dirs['datasets'])
    print("Utworzono 'data.yaml' oraz folder 'datasets'.")

if __name__ == "__main__":
    convert_to_yolo()