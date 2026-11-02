from mcp.server.fastmcp import FastMCP
import asyncio
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

mcp = FastMCP("google-sheets-server")

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', 'YOUR_SPREADSHEET_ID_HERE')

def get_credentials():
    """Gets valid user credentials from storage."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("credentials.json not found. Please follow the instructions to download it from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Use run_local_server carefully; in headless mode it might not work directly without port forwarding
            # But standard google auth flow requires it. We assume user runs this once locally.
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

@mcp.tool()
async def append_to_sheet(sender: str, subject: str, snippet: str) -> str:
    """
    Append email details to a Google Sheet.
    Expects SPREADSHEET_ID in environment and credentials.json/token.json in working directory.
    """
    creds = get_credentials()
    if not creds:
        return f"Mock mode (no credentials.json found): Appended {sender} | {subject} to Google Sheet."
        
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        # We append to the first sheet, assuming columns A, B, C
        values = [[sender, subject, snippet]]
        body = {'values': values}
        
        # Append data
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="A1",
            valueInputOption="RAW",
            body=body
        ).execute()
        
        updates = result.get('updates', {})
        updated_cells = updates.get('updatedCells')
        return f"Successfully appended to Google Sheet. Updated {updated_cells} cells."
    except Exception as e:
        return f"Error appending to Google Sheet: {e}"

if __name__ == "__main__":
    mcp.run()
