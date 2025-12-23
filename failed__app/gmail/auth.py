from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def get_credentials():
    if os.path.exists("token.json"):
        return Credentials.from_authorized_user_file("token.json", SCOPES)

    flow = InstalledAppFlow.from_client_secrets_file(
        "app/gmail/credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

    return creds
