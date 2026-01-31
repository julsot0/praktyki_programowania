import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import re

# wip

class ALPRPipeline:
    def __init__(self, model_path, conf_thres=0.25):
        self.detector = YOLO(model_path) 
        self.conf_thres = conf_thres
        self.reader = easyocr.Reader(['pl'], gpu=False, verbose=False)

    # detection
    def detect_plate(self, img):
        """
        Zwraca najlepszy bounding box tablicy [x1,y1,x2,y2]
        """
        results = self.detector.predict(
            img,
            conf=self.conf_thres,
            verbose=False
        )[0]

        best_box = None
        max_conf = 0.0

        for x1, y1, x2, y2, conf, _ in results.boxes.data.tolist():
            if conf > max_conf:
                max_conf = conf
                best_box = list(map(int, (x1, y1, x2, y2)))

        return best_box

    # crop & geometry
    def extract_plate_crop(self, img, box):
        """
        Przycinanie z korektą marginesów
        """
        x1, y1, x2, y2 = box
        h, w, _ = img.shape

        bw = x2 - x1
        bh = y2 - y1

        x1 = int(x1 + bw * 0.12)
        y1 = int(y1 + bh * 0.05)
        x2 = int(x2 - bw * 0.02)
        y2 = int(y2 - bh * 0.20)

        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x1 >= x2 or y1 >= y2:
            return None

        return img[y1:y2, x1:x2]

    # preprocessing
    def preprocess_plate(self, img):
        """
        Szybki preprocessing pod OCR
        """
        img = cv2.resize(img, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            19,
            9
        )

        binary = cv2.copyMakeBorder(
            binary, 15, 15, 15, 15,
            cv2.BORDER_CONSTANT,
            value=255
        )
        return binary

    # ocr
    def run_ocr(self, plate_img):
        """
        OCR z fallbackiem
        """
        processed = self.preprocess_plate(plate_img)
        text = "".join(self.reader.readtext(processed, detail=0))

        # fallback – surowy gray
        if len(text) < 4:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            text = "".join(self.reader.readtext(gray, detail=0))

        return text

    # pl
    def heuristic_polish_fix(self, text):
        if not text:
            return text

        chars = list(text)

        first_map = {
            '0': 'O', '1': 'I', '2': 'Z', '3': 'S',
            '4': 'A', '5': 'S', '6': 'G', 'X': 'K',
            '7': 'Z', '8': 'B', '9': 'S'
        }

        rest_map = {
            'O': '0', 'I': '1', 'L': '1', 'J': '1',
            'S': '5', 'B': '8', 'G': '6', 'Z': '7'
        }

        for i in range(min(2, len(chars))):
            chars[i] = first_map.get(chars[i], chars[i])

        for i in range(2, len(chars)):
            chars[i] = rest_map.get(chars[i], chars[i])

        return "".join(chars)

    # postprocess
    def postprocess_text(self, text):
        text = text.upper()
        text = re.sub(r'[^A-Z0-9]', '', text)

        if text.startswith("I"):
            text = text[1:]

        pl_anchor = re.search(r'^.{0,3}PL', text)
        if pl_anchor:
            text = text[pl_anchor.end():]

        text = text[:8]
        return self.heuristic_polish_fix(text)

    # process image
    def process_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None, None

        box = self.detect_plate(img)
        if box is None:
            return None, None

        crop = self.extract_plate_crop(img, box)
        if crop is None:
            return "", box

        raw_text = self.run_ocr(crop)
        final_text = self.postprocess_text(raw_text)

        return final_text, box
