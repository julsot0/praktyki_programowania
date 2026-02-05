import os
import time
import pandas as pd
import sys
import difflib
from src.load_data import load_dataset
from src.process import ALPRPipeline
from src.metrics import calculate_iou, calculate_final_grade
from sklearn.model_selection import train_test_split

iou_thres = 0.5
photos_dir = os.path.join(os.getcwd(), 'photos')
annotations_file = os.path.join(os.getcwd(), 'annotations.xml')
model_name = 'best.pt'

def get_similarity_score(gt, pred):
    if not gt or not pred: return 0.0
    gt = gt.upper().replace(" ", "").replace("-", "")
    pred = pred.upper().replace(" ", "").replace("-", "")
    return difflib.SequenceMatcher(None, gt, pred).ratio()

def main():
    print("=" * 50)
    print("SYSTEM ROZPOZNAWANIA TABLIC")
    print("=" * 50)
    
    model_path = f"runs/detect/yolo_plate_detect/weights/{model_name}"
    if not os.path.exists(model_path):
        print("Brak modelu 'best.pt' - najpierw uruchom 'train_model.py'")
        sys.exit(1)

    full_data = load_dataset(annotations_file, photos_dir)
    _, test_set = train_test_split(
        full_data,
        test_size=0.3, 
        random_state=42)
    
    target_count = min(100, len(test_set))
    if target_count == 0: target_count = len(full_data)
    
    os.environ["YOLO_VERBOSE"] = "False"
    pipeline = ALPRPipeline(model_path)

    results = []
    correct_ocr_count = 0
    start_time = time.time()
    
    print(f"Przetwarzanie {target_count} obrazów...")
    print()
    
    for idx, data in enumerate(test_set):
        try:
            raw_text, pred_text, pred_box = pipeline.process_image(data['path'])
            is_correct = False
            similarity = 0.0
            
            if pred_box:
                iou = calculate_iou(pred_box, data['bbox'])

                if iou >= iou_thres:
                    if pred_text and data['text_gt']:
                        similarity = get_similarity_score(data['text_gt'], pred_text)
                        if similarity >= 1:
                            is_correct = True
                            correct_ocr_count += 1
            
            # wyswietlanie
            fname = os.path.basename(data['path'])
            status = "✓" if is_correct else "X"
            
            print(f"{idx+1:3d}. {fname:12} | GT: {data['text_gt']:15} | OCR1: {raw_text or '-':15} | OCR2: {pred_text or '-':15} | "
                  f"{status}")

            results.append({
                "File": fname,
                "GT": data['text_gt'],
                "Pred": pred_text,
                "OK": is_correct
            })
        except Exception as e:
            print(f"Błąd dla {data.get('path', '???')}: {e}")

    total_time = time.time() - start_time
    accuracy_percent = (correct_ocr_count / target_count) * 100
    final_grade = calculate_final_grade(accuracy_percent, total_time)
    
    # wyniki
    print()
    print("PODSUMOWANIE")
    print("─" * 30)
    print(f"Ocena końcowa = {final_grade}")
    
    stats = [
        ["Przetworzone obrazy", f"{target_count}"],
        ["Poprawne rozpoznania", f"{correct_ocr_count}"],
        ["Dokładność", f"{accuracy_percent:.1f}%"],
        ["Czas całkowity", f"{total_time:.2f}s"],
        ["Średni czas/obraz", f"{total_time/target_count:.3f}s"],
        ["OCENA KOŃCOWA", f"{final_grade}"]
    ]
    
    for label, value in stats:
        if label:
            print(f"{label:20} : {value}")
    
    print("─" * 30)


if __name__ == "__main__":
    main()