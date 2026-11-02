from playwright.sync_api import sync_playwright
import os
import time

def fetch_latest_email(user_data_dir, profile_dir):
    """
    Launches Chrome using a persistent context to utilize the existing logged-in session,
    navigates to Gmail, and fetches the latest email's details.
    
    Returns a dict with 'sender', 'subject', 'snippet' or None if it fails.
    """
    try:
        with sync_playwright() as p:
            # We use launch_persistent_context to use the actual Chrome user data directory.
            # However, Playwright can sometimes struggle to launch Chrome if it's already running.
            # Using channel='chrome' attempts to use the system Chrome.
            
            # Since playwright doesn't support profile_dir natively as an argument to launch_persistent_context
            # unless we start from scratch or manipulate args, we specify the base dir and pass an arg.
            args = []
            if profile_dir and profile_dir != 'Default':
                 args.append(f'--profile-directory={profile_dir}')
                 
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome", # try to use installed chrome
                headless=False,
                args=args,
                no_viewport=True, # to avoid resizing issues
            )
            
            page = browser.new_page()
            
            # Go to Gmail
            page.goto("https://mail.google.com/mail/u/0/#inbox")
            
            # Wait for the inbox to load. 
            # We can wait for the table row that contains emails.
            page.wait_for_selector("table.F.cf.zt tbody tr", timeout=30000)
            
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
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet
                }
            else:
                browser.close()
                return None
                
    except Exception as e:
        print(f"Error during automation: {e}")
        return None

if __name__ == '__main__':
    # Simple test placeholder
    print("Automation module ready.")
