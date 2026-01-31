import cv2
import numpy as np
import urllib.request


def count_people(url: str) -> int:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req)

        buffer = np.frombuffer(response.read(), np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if frame is None:
            return 0

        if frame.shape[1] > 800:
            scale = 800 / frame.shape[1]
            frame = cv2.resize(
                frame,
                (800, int(frame.shape[0] * scale)),
                interpolation=cv2.INTER_LINEAR
            )

        hog = cv2.HOGDescriptor(
            _winSize=(64, 128),
            _blockSize=(16, 16),
            _blockStride=(8, 8),
            _cellSize=(8, 8),
            _nbins=9
        )
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        detections, _ = hog.detectMultiScale(
            frame,
            scale=1.05,
            winStride=(4, 4),
            padding=(8, 8)
        )

        return detections.shape[0]

    except Exception as e:
        print(f"Error: {e}")
        return 0