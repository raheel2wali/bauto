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
