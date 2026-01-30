import sqlite3

DB_NAME = 'database.db'

def initialize():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' has been initialized.")

if __name__ == "__main__":
    initialize()