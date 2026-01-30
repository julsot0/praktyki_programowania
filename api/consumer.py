import random
import sqlite3
import time
import threading

DB_NAME = 'database.db'
WORK_TIME = 30
POLL_INTERVAL = 5
NUM_WORKERS = 3 

def process_tasks(worker_id):
    print(f"Worker {worker_id} started. Waiting for tasks...")
    
    while True:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE tasks 
                SET status = 'in_progress' 
                WHERE id = (
                    SELECT id FROM tasks 
                    WHERE status = 'pending' 
                    LIMIT 1
                )
                RETURNING id
            ''')
            
            result = cursor.fetchone()
            
            if result:
                task_id = result[0]
                conn.commit()
                conn.close()
                
                print(f"Worker {worker_id}: Task {task_id}: in progress")
                time.sleep(WORK_TIME)
                
                conn = sqlite3.connect(DB_NAME)
                conn.execute("UPDATE tasks SET status='done' WHERE id=?", (task_id,))
                conn.commit()
                conn.close()
                
                print(f"Worker {worker_id}: Success! Task {task_id}: done")
            else:
                conn.close()
                print(f"Worker {worker_id}: No tasks. Waiting {POLL_INTERVAL}s...")
                time.sleep(POLL_INTERVAL)
                
        except Exception as e:
            print(f"Worker {worker_id}: Error: {e}")
            if conn:
                conn.close()
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    workers = []
    
    for i in range(NUM_WORKERS):
        worker = threading.Thread(target=process_tasks, args=(i+1,))
        worker.daemon = True
        workers.append(worker)
        worker.start()
    
    # stopping
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping workers...")