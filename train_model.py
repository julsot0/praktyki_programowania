from ultralytics import YOLO
import os

# w miare dziala

def train():
    print("trening modelu YOLOv8")
    model = YOLO('yolov8n.pt')     

    results = model.train(
        data='data.yaml',
        epochs=30,
        imgsz=640,
        batch=16,
        name='yolo_plate_detect',
        exist_ok=True
    )
    
    print("\nKoniec treningu")
    print(f"Model zapisano w: {results.save_dir}/weights/best.pt")
    
    #model.export(format='onnx')

def check_photos_folder():
    folder = 'photos'
    if not os.path.exists(folder):
        print(f"Nie znaleziono folderu '{folder}'")
        return False
    else:
        print(f"Folder '{folder}' istnieje.")
        pliki = os.listdir(folder)
        print(f"   Znaleziono {len(pliki)} plików.")
        train()

if __name__ == "__main__":
    check_photos_folder()