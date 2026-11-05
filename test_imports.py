import pytest
import profiles
import automation
import db
import mcp_server
import mcp_client
import app

def test_imports():
    assert profiles.get_chrome_profiles is not None
    assert automation.run_automation is not None
    assert db.init_db is not None
    assert mcp_server.append_to_sheet is not None
    assert mcp_client.append_to_google_sheet is not None

if __name__ == "__main__":
    test_imports()
    print("All imports successful!")
