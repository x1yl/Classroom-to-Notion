import os
import os.path
from datetime import datetime, timezone, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# If modifying these scopes, delete the file token.json.


class Authenticator:
    def __init__(self, credentials_file="credentials.json", token_file="token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def get_credentials(self):
        load_dotenv()

        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        now = datetime.now(timezone.utc)

        try:
            early_refresh_minutes = int(os.getenv("TOKEN_EARLY_REFRESH_MINUTES", "0") or 0)
        except ValueError:
            early_refresh_minutes = 0

        max_age_days_raw = os.getenv("TOKEN_MAX_AGE_DAYS")
        try:
            max_age_days = int(max_age_days_raw) if max_age_days_raw else None
        except ValueError:
            max_age_days = None

        force_reauth_on_max_age = (
            os.getenv("TOKEN_FORCE_REAUTH_ON_MAX_AGE", "true").lower() in ("1", "true", "yes", "y")
        )

        need_early_refresh = False
        max_age_exceeded = False

        if creds and creds.expiry and early_refresh_minutes > 0:
            expiry = creds.expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            effective_expiry = expiry - timedelta(minutes=early_refresh_minutes)
            if now >= effective_expiry:
                need_early_refresh = True

        if max_age_days is not None and os.path.exists(self.token_file):
            token_mtime = datetime.fromtimestamp(os.path.getmtime(self.token_file), tz=timezone.utc)
            if now >= token_mtime + timedelta(days=max_age_days):
                max_age_exceeded = True

        if not creds or not creds.valid or need_early_refresh or max_age_exceeded:
            if max_age_exceeded and force_reauth_on_max_age:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            elif creds and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            try:
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
            except Exception:
                pass
        return creds