from playwright.sync_api import sync_playwright
import os
import time

def run_automation(user_data_dir, profile_dir, task_url):
    """
    Launches Chrome using a persistent context to utilize the existing logged-in session,
    navigates to the task_url.
    If task_url is Gmail, it attempts to fetch the latest email's details if logged in.
    Otherwise, it simply opens the website.
    
    Returns a dict with 'type', 'status', and other data if applicable.
    """
    try:
        with sync_playwright() as p:
            args = []
            if profile_dir and profile_dir != 'Default':
                 args.append(f'--profile-directory={profile_dir}')
                 
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                args=args,
                no_viewport=True,
            )
            
            # Use the existing page to prevent an about:blank tab from hiding our work
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            # Format url correctly
            if not task_url.startswith('http://') and not task_url.startswith('https://'):
                task_url = 'https://' + task_url

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
