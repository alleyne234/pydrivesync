import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_authenticated_drive_service():
    """Retrieve an authenticated Google Drive service using OAuth 2.0.

    Checks for existing credentials and initiates the OAuth authentication
    process if needed. This function uses the 'credentials.json' file to store
    OAuth 2.0 credentials. If the file doesn't exist or contains invalid
    credentials, it launches the OAuth authentication process through user
    consent in a local web server.

    Returns:
        googleapiclient.discovery.Resource: Authenticated Google Drive service
        that can be used for interacting with the Drive API.

    Raises:
        FileNotFoundError: If 'token.json' or 'credentials.json' file is missing
        or inaccessible.
        Exception: If there's an unexpected error during the authentication process.
    """
    try:
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("Tokens/token.json"):
            creds = Credentials.from_authorized_user_file("Tokens/token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "Tokens/credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run.
            with open("Tokens/token.json", "w") as token_file:
                token_file.write(creds.to_json())

        try:
            service = build("drive", "v3", credentials=creds)
            print("Authentication successful")
            return service
        except HttpError as error:
            print(f"An error occurred during service build: {error}")
            return None
      
    except FileNotFoundError as file_error:
        print(f"File access error: {file_error}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None