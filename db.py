import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'emails.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_dir TEXT,
            sender TEXT,
            subject TEXT,
            snippet TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def insert_email(profile_dir, sender, subject, snippet):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO emails (profile_dir, sender, subject, snippet, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (profile_dir, sender, subject, snippet, timestamp))
    email_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return email_id

def get_all_emails():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM emails ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
