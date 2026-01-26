import pika
import json
import os
from fastapi import FastAPI, HTTPException
from shared_models import ImageURL, ImageTask

"""
docker run -d --hostname my-rabbit --name some-rabbit -p 8080:15672 rabbitmq:3-management
"""

# Konfiguracja RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = "image_processing_queue"

app = FastAPI()
task_store = {}

class RabbitMQProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    
    def publish(self, task: ImageTask):
        self.channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(task.dict()),
            properties=pika.BasicProperties(delivery_mode=2)
        )

producer = RabbitMQProducer()

@app.post("/analyze")
async def analyze_image(image_data: ImageURL):
    task = ImageTask(image_url=image_data.url)
    task_store[task.task_id] = task.dict()
    
    try:
        producer.publish(task)
        task_store[task.task_id]["status"] = "queued"
    except Exception as e:
        task_store[task.task_id]["status"] = "failed"
        task_store[task.task_id]["error"] = str(e)
        raise HTTPException(500, "Queue error")
    
    return {"task_id": task.task_id, "status": "queued"}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in task_store:
        raise HTTPException(404, "Task not found")
    return task_store[task_id]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "producer"}