from flask import Flask
import os
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# Database configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'users.db')

# Function to execute queries
def execute_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

# Function to check if a table exists
def table_exists(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Function to initialize database
def initialize_database():
    if not os.path.exists(DB_PATH) or not table_exists('user'):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print("Existing database removed.")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        conn.commit()
        conn.close()
        print("Database initialized successfully with updated schema!")
    else:
        print("Database already exists and is up-to-date.")

# Run database initialization
if __name__ == "__main__":
    initialize_database()