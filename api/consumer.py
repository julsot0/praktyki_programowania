import json
import time
import pika
from analyze_image import count_people


def callback(channel, delivery, props, payload):
    message = json.loads(payload.decode("utf-8"))

    task_name = message.get("name", "Unnamed task")
    image_url = message.get("url")

    print(f"\nTask received → {task_name}")
    print(f"Source image: {image_url}")
    print("Processing...")

    t0 = time.perf_counter()
    detected = count_people(image_url)
    elapsed = time.perf_counter() - t0

    if detected:
        print(f"People detected: {detected}")
    else:
        print("No people detected")

    print(f"Processing time: {elapsed:.2f}s")

    channel.basic_ack(delivery_tag=delivery.delivery_tag)


def start():
    params = pika.ConnectionParameters(host="localhost")
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue="image_queue", durable=False)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue="image_queue",
        on_message_callback=callback,
        auto_ack=False
    )

    print("-" * 48)
    print("Image consumer started")
    print("Waiting for messages...")
    print("-" * 48)

    channel.start_consuming()


if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print("\nConsumer terminated manually")
