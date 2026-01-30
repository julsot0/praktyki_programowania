from fastapi import FastAPI
from pydantic import BaseModel
import pika
import json

app = FastAPI()

class ImageRequest(BaseModel):
    url: str

def send_to_queue(url: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='image_queue')

    channel.basic_publish(
        exchange='',
        routing_key='image_queue',
        body=json.dumps({'url': url})
    )
    print(f" [x] Wysłano do kolejki: {url}")
    connection.close()

@app.post("/analyze_img")
def analyze_image_endpoint(request: ImageRequest):
    """
    Endpoint przyjmuje URL, wrzuca go na kolejkę i od razu zwraca potwierdzenie.
    """
    send_to_queue(request.url)
    return {"message": "Zadanie przyjęte do realizacji", "url": request.url}