import os
#os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
#os.environ['OMP_NUM_THREADS'] = '1'

import time
import pandas as pd
import sys
import difflib
from src.load_data import load_dataset, split_dataset
from src.process import ALPRPipeline
from src.metrics import calculate_iou, calculate_final_grade

# dziala

PHOTOS_DIR = os.path.join(os.getcwd(), 'photos')
ANNOTATIONS_FILE = os.path.join(os.getcwd(), 'annotations.xml')

MODEL_NAME = 'best.pt'
TEST_SPLIT = 0.6

def get_similarity_score(gt, pred):
    if not gt or not pred: return 0.0
    gt = gt.upper().replace(" ", "").replace("-", "")
    pred = pred.upper().replace(" ", "").replace("-", "")
    return difflib.SequenceMatcher(None, gt, pred).ratio()

def main():
    print("=" * 50)
    print("SYSTEM ROZPOZNAWANIA TABLIC")
    print("=" * 50)
    
    model_path = f"runs/detect/yolo_plate_detect/weights/{MODEL_NAME}"
    if not os.path.exists(model_path):
        print("Brak modelu 'best.pt' - najpierw uruchom 'train_model.py'")
        sys.exit(1)

    full_data = load_dataset(ANNOTATIONS_FILE, PHOTOS_DIR)
    _, test_set = split_dataset(full_data, split_ratio=TEST_SPLIT, random_state=26)
    
    target_count = min(100, len(test_set))
    if target_count == 0: target_count = len(full_data)
    test_subset = test_set[:target_count]
    
    os.environ["YOLO_VERBOSE"] = "False"
    pipeline = ALPRPipeline(model_path)

    results = []
    correct_ocr_count = 0
    start_time = time.time()
    
    print(f"Przetwarzanie {target_count} obrazów...")
    print()

    for idx, data in enumerate(test_subset):
        try:
            pred_text, pred_box = pipeline.process_image(data['path'])
            is_correct = False
            similarity = 0.0
            
            if pred_box:
                iou = calculate_iou(pred_box, data['bbox'])
                if pred_text and data['text_gt']:
                    similarity = get_similarity_score(data['text_gt'], pred_text)
                    if similarity >= 0.85:
                        is_correct = True
                        correct_ocr_count += 1
            
            # wyswietlanie
            fname = os.path.basename(data['path'])
            status = "✓" if is_correct else "X"
            
            print(f"{idx+1:3d}. {fname:12} | GT: {data['text_gt']:15} | OCR: {pred_text or '-':15} | "
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
    
    # zapis do CSV
    pd.DataFrame(results).to_csv("wyniki_final.csv", index=False)
    print(f"\nWyniki zapisano do: wyniki_final.csv")

if __name__ == "__main__":
    main()