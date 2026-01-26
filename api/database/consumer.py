"""
import pika
import json
import cv2
import numpy as np
import requests
import os
import sys
from shared_models import ImageTask

# Konfiguracja
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = "image_processing_queue"
consumer_id = sys.argv[1] if len(sys.argv) > 1 else "1"

# Inicjalizacja HOG
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def process_image(image_url: str) -> int:
    response = requests.get(image_url, timeout=10)
    image_array = np.frombuffer(response.content, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Cannot decode image")
    
    # Konwersja i skalowanie
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    height, width = image.shape[:2]
    if max(height, width) > 800:
        scale = 800 / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))
    
    # Detekcja osób
    boxes, _ = hog.detectMultiScale(image, winStride=(4,4), padding=(8,8), scale=1.05)
    return len(boxes)

def callback(ch, method, properties, body):
    task_data = json.loads(body)
    task = ImageTask(**task_data)
    
    print(f"Consumer {consumer_id} processing task {task.task_id}")
    
    try:
        people_count = process_image(task.image_url)
        task.status = "completed"
        task.result = people_count
        print(f"Task {task.task_id}: {people_count} people detected")
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        print(f"Task {task.task_id} failed: {e}")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    
    print(f"Consumer {consumer_id} started. Waiting for tasks...")
    
    channel.basic_consume(
        queue=RABBITMQ_QUEUE,
        on_message_callback=callback,
        auto_ack=False
    )
    
    channel.start_consuming()

if __name__ == "__main__":
    main()
"""