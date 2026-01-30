import pika
import json
import time
from analyze_image import count_people

def callback(ch, method, properties, body):
    data = json.loads(body)
    url = data.get('url')
    name = data.get('name', 'Unnamed task')
    
    print(f"\nNew task: Name: {name} URL: {url} - Analyzing...")

    start_time = time.time()
    
    people = count_people(url)
    
    duration = time.time() - start_time

    if people > 0:
        print(f"Detected {people} people.")
    else:
        print(f"No people detected.")

    print(f"Duration: {duration:.2f}s")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='image_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='image_queue', on_message_callback=callback)

    print("=" * 50)
    print("Image Analysis Worker Ready")
    print("Listening for new image processing tasks...")
    print("=" * 50)
    channel.start_consuming()

if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print("Stopped by user.")