import sqlite3
import uuid
import csv
from datetime import datetime

DB_NAME = 'database.db'
CSV_FILE = 'tasks/tasks_log.csv'

def produce_task():
    task_id = str(uuid.uuid4())
    initial_status = 'pending'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # zapis do bazy
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO tasks (id, status) VALUES (?, ?)", (task_id, initial_status))
        conn.commit()
        print(f"Added: {task_id} with status {initial_status}")
    except sqlite3.Error as e:
        print(f"Error adding task to database: {e}")
        conn.close()
        return
    finally:
        conn.close()
    
    # csv file
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # empty file
            if csvfile.tell() == 0:
                writer.writerow(['task_id', 'status', 'timestamp'])
            
            writer.writerow([task_id, initial_status, timestamp])
        
        print(f"Added to: {CSV_FILE}")
        
    except Exception as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    produce_task()