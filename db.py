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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile_tasks (
            profile_dir TEXT PRIMARY KEY,
            task_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

def set_profile_task(profile_dir, task_url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profile_tasks (profile_dir, task_url)
        VALUES (?, ?)
        ON CONFLICT(profile_dir) DO UPDATE SET task_url=excluded.task_url
    ''', (profile_dir, task_url))
    conn.commit()
    conn.close()

def get_profile_task(profile_dir):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT task_url FROM profile_tasks WHERE profile_dir = ?', (profile_dir,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return "https://mail.google.com/mail/u/0/#inbox"

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
