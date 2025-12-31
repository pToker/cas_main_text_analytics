import logging
from pathlib import Path
from typing import List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.config import CREDENTIALS_FILE, GMAIL_SCOPES

logger = logging.getLogger(__name__)


class GmailClient:
    """
    Gmail client with automatic OAuth flow, token persistence, and refresh.
    """

    def __init__(self, client_secrets_path: Optional[Path] = None, scopes: Optional[List[str]] = None):
        self.scopes = scopes or GMAIL_SCOPES
        self.client_secrets_path = Path(client_secrets_path) if client_secrets_path else CREDENTIALS_FILE
        self.token_file = self.client_secrets_path.parent / "token.json"
        self.creds = self._load_credentials()
        self.service = build("gmail", "v1", credentials=self.creds, cache_discovery=False)
        logger.info("Gmail client initialized")

    def _load_credentials(self) -> Credentials:
        creds = None

        # 1. Try loading existing token
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
                logger.debug(f"Loaded authorized credentials from {self.token_file}")
            except Exception as e:
                logger.warning("Invalid token file, running OAuth flow: %s", e)

        # 2. If missing/invalid, run OAuth flow
        if not creds or not creds.valid:
            logger.info("Running OAuth flow to authorize Gmail access...")
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_path, self.scopes)
            creds = flow.run_local_server(port=0)
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())
            logger.info(f"Saved new authorized token to {self.token_file}")

        # 3. Refresh if expired
        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token")
            creds.refresh(Request())

        return creds

    # Gmail API helpers
    def list_messages(self, user_id="me", label_ids=None, page_token=None):
        return self.service.users().messages().list(
            userId=user_id, labelIds=label_ids, pageToken=page_token
        ).execute()

    def get_message(self, msg_id, user_id="me"):
        return self.service.users().messages().get(userId=user_id, id=msg_id, format="full").execute()

    def list_labels(self, user_id="me"):
        result = self.service.users().labels().list(userId=user_id).execute()
        return result.get("labels", [])

    def get_history(self, start_history_id, user_id="me", label_ids=None):
        return self.service.users().history().list(
            userId=user_id, startHistoryId=start_history_id, labelId=label_ids
        ).execute()
