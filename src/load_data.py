import xml.etree.ElementTree as ET
import os
import random

# wip

def load_dataset(xml_file, images_dir):
    if not os.path.exists(xml_file):
        raise FileNotFoundError(f"Brak pliku XML: {xml_file}")
    else:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        data_points = []
        missing_files = 0

        print(f"Ścieżki w: {images_dir}")
        
        for img_element in root.findall('image'):
            img_filename  = img_element.get('name')
            
            image_full_path = os.path.join(images_dir, img_filename)
            
            if not os.path.exists(image_full_path):
                alternative_location = os.path.join(images_dir, 'images', img_filename)
                if os.path.exists(alternative_location):
                    image_full_path = alternative_location
                else:
                    missing_files += 1
                    continue 
            
            # szukanie elementu <box> z atrybutem label="plate"
            plate_bbox = img_element.find("box[@label='plate']")
            if plate_bbox is None:
                continue 
            
            # pobranie wspołrzędnych bboxa
            left_x = float(plate_bbox.get('xtl'))
            top_y = float(plate_bbox.get('ytl'))
            right_x = float(plate_bbox.get('xbr'))
            bottom_y = float(plate_bbox.get('ybr'))
            
            # znajdź tekst tablicy rejestracyjnej
            text_element = plate_bbox.find("attribute[@name='plate number']")
            plate_number = text_element.text if text_element is not None else ""

            sample = {
                    "path": image_full_path,
                    "bbox": [int(left_x), int(top_y), int(right_x), int(bottom_y)],
                    "text_gt": plate_number if plate_number else ""
                }
            data_points.append(sample)
        if missing_files > 0:
            print(f"Pominięto {missing_files} plików")
    return data_points

def split_dataset(dataset, split_ratio=0.3, random_state=None):
    # losowy state
    if random_state is not None:
        random.seed(random_state)
    
    # losowe
    shuffled_data = random.sample(dataset, len(dataset))
    
    # punkt podzialu
    partition_point = int(len(shuffled_data) * split_ratio)
    
    # podział
    test_subset = shuffled_data[:partition_point]
    train_subset = shuffled_data[partition_point:]
    
    return train_subset, test_subset