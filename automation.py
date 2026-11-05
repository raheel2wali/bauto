from playwright.sync_api import sync_playwright
import os
import sys
import time
import shutil
import subprocess


def _find_chrome_exe():
    """Locate the Chrome executable on this machine."""
    candidates = []
    if sys.platform == 'win32':
        for env in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
            base = os.environ.get(env)
            if base:
                candidates.append(os.path.join(base, 'Google', 'Chrome', 'Application', 'chrome.exe'))
    elif sys.platform == 'darwin':
        candidates.append('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    for c in candidates:
        if os.path.exists(c):
            return c
    for name in ('chrome', 'google-chrome', 'google-chrome-stable', 'chromium'):
        found = shutil.which(name)
        if found:
            return found
    return None


def _is_chrome_running():
    """Return True if a Chrome process is already running."""
    try:
        if sys.platform == 'win32':
            out = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq chrome.exe', '/NH'],
                capture_output=True, text=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            ).stdout
            return 'chrome.exe' in out.lower()
        out = subprocess.run(['pgrep', '-f', 'chrome'], capture_output=True, text=True).stdout
        return bool(out.strip())
    except Exception:
        return False


def _open_in_existing_chrome(user_data_dir, profile_dir, url):
    """
    Opens the URL as a new tab in the already-running Chrome session
    (for the given profile). Chrome forwards the request to the running
    instance, so a new tab appears in the existing window.
    """
    chrome = _find_chrome_exe()
    if not chrome:
        raise RuntimeError("Chrome executable not found")
    cmd = [chrome]
    if user_data_dir:
        cmd.append(f'--user-data-dir={user_data_dir}')
    if profile_dir:
        cmd.append(f'--profile-directory={profile_dir}')
    cmd.append(url)
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _existing_browser_result(user_data_dir, profile_dir, task_url):
    _open_in_existing_chrome(user_data_dir, profile_dir, task_url)
    result = {
        "type": "custom",
        "status": "success",
        "url": task_url,
    }
    if "mail.google.com" in task_url:
        result["note"] = ("Chrome was already open, so the URL was opened in a new tab. "
                          "Close Chrome completely to allow fetching the latest email.")
    return result


def run_automation(user_data_dir, profile_dir, task_url):
    """
    Launches Chrome using a persistent context to utilize the existing logged-in session,
    navigates to the task_url.
    If task_url is Gmail, it attempts to fetch the latest email's details if logged in.
    Otherwise, it simply opens the website.
    If Chrome is already running, the URL is opened in a new tab of the existing window.
    
    Returns a dict with 'type', 'status', and other data if applicable.
    """
    # Format url correctly
    if not task_url.startswith('http://') and not task_url.startswith('https://'):
        task_url = 'https://' + task_url

    # Playwright cannot attach to a Chrome that is already using this User Data dir
    # ("Opening in existing browser session"). Open a new tab in that window instead.
    if _is_chrome_running():
        try:
            return _existing_browser_result(user_data_dir, profile_dir, task_url)
        except Exception as e:
            return {"type": "error", "status": "error", "message": str(e)}

    try:
        with sync_playwright() as p:
            args = []
            if profile_dir and profile_dir != 'Default':
                 args.append(f'--profile-directory={profile_dir}')
                 
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    channel="chrome",
                    headless=False,
                    args=args,
                    no_viewport=True,
                )
            except Exception as launch_err:
                # Chrome may have been started in the meantime – fall back to a new tab
                if "existing browser session" in str(launch_err).lower() or _is_chrome_running():
                    return _existing_browser_result(user_data_dir, profile_dir, task_url)
                raise
            
            # Use the existing page to prevent an about:blank tab from hiding our work
            page = browser.pages[0] if browser.pages else browser.new_page()
                
            # If not a specific gmail inbox url, just go there and we are done
            if "mail.google.com" not in task_url:
                page.goto(task_url)
                page.wait_for_load_state('domcontentloaded')
                # Keep it open for a bit or just return success
                time.sleep(2) 
                return {
                    "type": "custom",
                    "status": "success",
                    "url": task_url
                }

            # Go to Gmail
            page.goto("https://mail.google.com/")
            page.wait_for_load_state('domcontentloaded')
            time.sleep(2) # Wait for potential redirect if not logged in
            
            if "accounts.google.com" in page.url or "v2/identifier" in page.url:
                # Not logged in
                return {
                    "type": "gmail",
                    "status": "not_logged_in"
                }
            
            # We can wait for the table row that contains emails.
            try:
                page.wait_for_selector("table.F.cf.zt tbody tr", timeout=15000)
            except Exception:
                # Check again if redirected to login
                if "accounts.google.com" in page.url:
                    return {
                        "type": "gmail",
                        "status": "not_logged_in"
                    }
                return {
                    "type": "gmail",
                    "status": "error",
                    "message": "Inbox not found"
                }
            
            # We add a small sleep to ensure dynamic elements have settled.
            time.sleep(2)
            
            # Extract the first row (latest email)
            latest_email_row = page.locator("table.F.cf.zt tbody tr").first
            
            if latest_email_row:
                # In Gmail, 'yX xY' class span contains the sender
                sender_el = latest_email_row.locator("span.bA4 span.yP, span.bA4 span.zF").first
                sender = sender_el.inner_text() if sender_el.count() > 0 else "Unknown Sender"
                
                # 'bog' class span inside 'xY a4W' contains the subject
                subject_el = latest_email_row.locator("span.bog").first
                subject = subject_el.inner_text() if subject_el.count() > 0 else "No Subject"
                
                # 'y2' class span contains the snippet
                snippet_el = latest_email_row.locator("span.y2").first
                snippet = snippet_el.inner_text() if snippet_el.count() > 0 else "No Snippet"
                
                browser.close()
                return {
                    "type": "gmail",
                    "status": "success",
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet
                }
            else:
                browser.close()
                return {
                    "type": "gmail",
                    "status": "error",
                    "message": "No emails found"
                }
                
    except Exception as e:
        print(f"Error during automation: {e}")
        return {
            "type": "error",
            "status": "error",
            "message": str(e)
        }

if __name__ == '__main__':
    # Simple test placeholder
    print("Automation module ready.")
