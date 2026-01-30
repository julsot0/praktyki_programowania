import requests
import threading
import time
from producer import publish_messages

API_URL = "http://127.0.0.1:8000/analyze_img"

TEST_DATA = [
    ("One woman", "https://images.pexels.com/photos/6975472/pexels-photo-6975472.jpeg"),
    ("Two people", "https://images.pexels.com/photos/6787498/pexels-photo-6787498.jpeg"),
    ("Four people", "https://images.pexels.com/photos/33435591/pexels-photo-33435591.jpeg"),
]

def send_request(name, url):
    print(f"Sending: {name}...")
    try:
        start = time.time()
        response = requests.post(API_URL, json={"url": url}, timeout=5)
        duration = time.time() - start
        
        if response.status_code == 200:
            print(f"Success: {name} (duration: {duration:.2f}s)")
        else:
            print(f"Got error for {name}: {response.status_code}")
            
    except Exception as e:
        print(f"Error for {name}: {e}")

print(f"Test for {len(TEST_DATA)} photos")

threads = []
for name, url in TEST_DATA:
    t = threading.Thread(target=send_request, args=(name, url))
    threads.append(t)
    t.start()
    time.sleep(0.1) 

for t in threads:
    t.join()

publish_messages(TEST_DATA)
print("All tasks sent to RabbitMQ queue")