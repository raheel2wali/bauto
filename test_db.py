import pytest
import sqlite3
import os
import db

@pytest.fixture
def test_db(monkeypatch, tmp_path):
    # Use a temporary database for testing
    db_path = tmp_path / "test_emails.db"
    monkeypatch.setattr(db, 'DB_PATH', str(db_path))
    db.init_db()
    return db_path

def test_init_db(test_db):
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
    table_exists = cursor.fetchone()
    conn.close()
    assert table_exists is not None

def test_insert_and_get_emails(test_db):
    email_id = db.insert_email("Default", "test@example.com", "Test Subject", "Test Snippet")
    assert email_id == 1
    
    emails = db.get_all_emails()
    assert len(emails) == 1
    
    email = emails[0]
    # Check the fields
    assert email[1] == "Default"
    assert email[2] == "test@example.com"
    assert email[3] == "Test Subject"
    assert email[4] == "Test Snippet"

def test_profile_tasks(test_db):
    # Default task
    default_task = db.get_profile_task("Default")
    assert default_task["url"] == "https://mail.google.com/mail/u/0/#inbox"
    assert default_task["timer"] == 0
    
    # Set and get task
    db.set_profile_task("Default", "https://example.com", 15)
    updated_task = db.get_profile_task("Default")
    assert updated_task["url"] == "https://example.com"
    assert updated_task["timer"] == 15
    
    # Update task (UPSERT test)
    db.set_profile_task("Default", "https://test.com", 30)
    updated_task = db.get_profile_task("Default")
    assert updated_task["url"] == "https://test.com"
    assert updated_task["timer"] == 30

def test_due_tasks(test_db):
    # Setup some tasks
    db.set_profile_task("Default", "https://example.com", 15)
    db.set_profile_task("Profile 1", "https://test.com", 0) # No timer
    
    due = db.get_due_tasks()
    # Default should be due immediately since last_run is null
    assert len(due) == 1
    assert due[0][0] == "Default"
    assert due[0][1] == "https://example.com"
    
    # Update last run
    db.update_last_run("Default")
    due_after_update = db.get_due_tasks()
    # Shouldn't be due immediately after update
    assert len(due_after_update) == 0
