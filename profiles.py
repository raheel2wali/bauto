import os
import sys
import json
import glob

def get_chrome_user_data_dir():
    if sys.platform == 'win32':
        return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data')
    elif sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/Google/Chrome')
    else:
        # Default for Linux
        return os.path.expanduser('~/.config/google-chrome')

def get_chrome_profiles():
    """
    Returns a dictionary of profile directories and their human-readable names.
    e.g. {'Default': 'Default', 'Profile 1': 'Work', ...}
    """
    user_data_dir = get_chrome_user_data_dir()
    local_state_path = os.path.join(user_data_dir, 'Local State')
    
    profiles = {}
    
    # Try parsing Local State first
    if os.path.exists(local_state_path):
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
                info_cache = local_state.get('profile', {}).get('info_cache', {})
                for profile_dir, info in info_cache.items():
                    name = info.get('name', profile_dir)
                    profiles[profile_dir] = name
            return profiles, user_data_dir
        except Exception as e:
            pass # Fall back to directory scanning
            
    # Fallback: manually scan directories
    if os.path.exists(user_data_dir):
        # Default profile
        if os.path.isdir(os.path.join(user_data_dir, 'Default')):
            profiles['Default'] = 'Default'
        # Other profiles (Profile 1, Profile 2, etc.)
        for path in glob.glob(os.path.join(user_data_dir, 'Profile *')):
            if os.path.isdir(path):
                profile_dir = os.path.basename(path)
                profiles[profile_dir] = profile_dir
                
    return profiles, user_data_dir

if __name__ == '__main__':
    profiles, base_dir = get_chrome_profiles()
    print(f"Base Directory: {base_dir}")
    print("Found Profiles:", profiles)
