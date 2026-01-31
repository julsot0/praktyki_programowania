import sqlite3
import csv
import uuid
from datetime import datetime

DATABASE = "database.db"
CSV_PATH = "tasks/tasks_log.csv"


def produce():
    uid = str(uuid.uuid4())
    status = "pending"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        connection = sqlite3.connect(DATABASE)
        cur = connection.cursor()
        cur.execute(
            "INSERT INTO tasks (id, status) VALUES (?, ?)",
            (uid, status)
        )
        connection.commit()
        print(f"Task stored: {uid} [{status}]")
    except sqlite3.Error as err:
        print(f"Database error: {err}")
        return
    finally:
        if 'connection' in locals():
            connection.close()

    try:
        with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(("task_id", "status", "timestamp"))
            writer.writerow((uid, status, created_at))

        print(f"CSV updated: {CSV_PATH}")
    except Exception as err:
        print(f"CSV write error: {err}")


if __name__ == "__main__":
    produce()