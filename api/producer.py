import uuid
import pika
import json
import time

def publish_messages(test_data):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue='image_queue')
    
    print(f"Publishing {len(test_data)} tasks to worker...")
    
    for name, url in test_data:
        message = {
            'id': str(uuid.uuid4()),
            'url': url,
            'name': name
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='image_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        
        print(f"Published: {name}")
        time.sleep(0.1)  # delay
    
    connection.close()
    print(f"\nAll {len(test_data)} tasks sent to worker queue")