import cv2
import numpy as np
import urllib.request

def count_people_in_image(url: str) -> int:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        arr = np.asarray(bytearray(response.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1) 

        if img is None:
            return 0
    
        max_width = 800
        if img.shape[1] > max_width:
            scale_ratio = max_width / img.shape[1]
            new_height = int(img.shape[0] * scale_ratio)
            img = cv2.resize(img, (max_width, new_height))
      
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        boxes, weights = hog.detectMultiScale(img, winStride=(8, 8), padding=(8, 8), scale=1.05)
        return len(boxes)
        
    except Exception as e:
        print(f"Błąd analizy: {e}")
        return 0