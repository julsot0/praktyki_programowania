import os

if os.path.exists("database.db"):
    os.remove("database.db")
    os.remove("tasks/tasks_log.csv")
    print("Removed old database.")

os.system("python load_db.py")

# generating tasks
print("Generating 100 tasks...")
for i in range(100):
    os.system("python producer.py")
print("100 tasks have been generated.")