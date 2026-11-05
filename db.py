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
            task_url TEXT,
            timer_minutes INTEGER DEFAULT 0,
            last_run DATETIME
        )
    ''')
    # For backward compatibility if the table already exists without new columns
    try:
        cursor.execute('ALTER TABLE profile_tasks ADD COLUMN timer_minutes INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE profile_tasks ADD COLUMN last_run DATETIME')
    except sqlite3.OperationalError:
        pass # Columns already exist
        
    conn.commit()
    conn.close()

def set_profile_task(profile_dir, task_url, timer_minutes=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profile_tasks (profile_dir, task_url, timer_minutes)
        VALUES (?, ?, ?)
        ON CONFLICT(profile_dir) DO UPDATE SET task_url=excluded.task_url, timer_minutes=excluded.timer_minutes
    ''', (profile_dir, task_url, timer_minutes))
    conn.commit()
    conn.close()

def get_profile_task(profile_dir):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT task_url, timer_minutes FROM profile_tasks WHERE profile_dir = ?', (profile_dir,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"url": row[0], "timer": row[1] or 0}
    return {"url": "https://mail.google.com/mail/u/0/#inbox", "timer": 0}

def update_last_run(profile_dir):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute('UPDATE profile_tasks SET last_run = ? WHERE profile_dir = ?', (timestamp, profile_dir))
    conn.commit()
    conn.close()

def get_due_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT profile_dir, task_url, timer_minutes, last_run FROM profile_tasks WHERE timer_minutes > 0')
    rows = cursor.fetchall()
    conn.close()
    
    due_tasks = []
    now = datetime.datetime.now()
    for row in rows:
        profile_dir, task_url, timer_minutes, last_run = row
        
        if not last_run:
            due_tasks.append((profile_dir, task_url))
            continue
            
        try:
            last_run_time = datetime.datetime.fromisoformat(last_run)
            if now - last_run_time >= datetime.timedelta(minutes=timer_minutes):
                due_tasks.append((profile_dir, task_url))
        except ValueError:
            due_tasks.append((profile_dir, task_url))
            
    return due_tasks

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
