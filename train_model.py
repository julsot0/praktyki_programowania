from ultralytics import YOLO
import os

def train():
    model = YOLO('yolov8n.pt')     

    results = model.train(
        data='data.yaml',
        epochs=50,
        imgsz=640,
        batch=8,
        name='yolo_plate_detect',
        exist_ok=True
    )
    print(f"model zapisano w {results.save_dir}/weights/best.pt")
    
def check_photos_folder():
    folder = 'photos'
    if not os.path.exists(folder):
        print(f"Nie znaleziono folderu '{folder}'")
        return False
    else:
        print(f"Folder '{folder}' istnieje.")
        pliki = os.listdir(folder)
        print(f"Znaleziono {len(pliki)} plików.")
        train()

if __name__ == "__main__":
    check_photos_folder()