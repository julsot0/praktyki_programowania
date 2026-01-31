CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.25

# wip

def calculate_iou(boxA, boxB):
    if len(boxA) != 4 or len(boxB) != 4:
        return 0.0
    
    if (boxA[2] <= boxA[0] or boxA[3] <= boxA[1] or 
        boxB[2] <= boxB[0] or boxB[3] <= boxB[1]):
        return 0.0
    
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    
    inter_width = max(0, xB - xA)
    inter_height = max(0, yB - yA)
    inter_area = inter_width * inter_height
    
    boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    
    union_area = boxA_area + boxB_area - inter_area
    
    if union_area <= 0:
        return 0.0
    
    iou = inter_area / union_area
    return iou

# nie zmieniac
def calculate_final_grade(accuracy_percent: float, processing_time_sec: float) -> float:
    """
    Calculates the final grade based on license plate OCR accuracy and processing time.
    
    Parameters:
    - accuracy_percent: OCR accuracy as a percentage (0–100)
    - processing_time_sec: total time to process 100 images in seconds
    
    Returns:
    - Grade on a scale from 2.0 to 5.0 (rounded to the nearest 0.5)
    """
    # Check minimum requirements
    if accuracy_percent < 60 or processing_time_sec > 60:
        return 2.0
    
    # Normalize accuracy: 60% → 0.0, 100% → 1.0
    accuracy_norm = (accuracy_percent - 60) / 40
    
    # Normalize time: 60s → 0.0, 10s → 1.0
    time_norm = (60 - processing_time_sec) / 50
    
    # Compute weighted score
    score = 0.7 * accuracy_norm + 0.3 * time_norm
    
    # Convert score to grade scale
    grade = 2.0 + 3.0 * score
    
    # Round to the nearest 0.5
    return round(grade * 2) / 2