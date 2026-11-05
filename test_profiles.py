import pytest
import sys
import os
import profiles

def test_get_chrome_user_data_dir(monkeypatch):
    # Test for Windows
    monkeypatch.setattr(sys, 'platform', 'win32')
    monkeypatch.setenv('LOCALAPPDATA', 'C:\\Users\\Test\\AppData\\Local')
    win_dir = profiles.get_chrome_user_data_dir()
    # On linux, os.path.join uses /
    # The actual output might be 'C:\\Users\\Test\\AppData\\Local/Google/Chrome/User Data'
    # We replace all \\ with / for comparison
    assert win_dir.replace('\\', '/') == 'C:/Users/Test/AppData/Local/Google/Chrome/User Data'
    
    # Test for Mac
    monkeypatch.setattr(sys, 'platform', 'darwin')
    # Mock expanduser to make it deterministic
    def mock_expanduser(path):
        if path.startswith('~/'):
            return '/Users/Test/' + path[2:]
        return path
    monkeypatch.setattr('os.path.expanduser', mock_expanduser)
    
    mac_dir = profiles.get_chrome_user_data_dir()
    assert mac_dir == '/Users/Test/Library/Application Support/Google/Chrome'
    
    # Test for Linux
    monkeypatch.setattr(sys, 'platform', 'linux')
    linux_dir = profiles.get_chrome_user_data_dir()
    assert linux_dir == '/Users/Test/.config/google-chrome'
