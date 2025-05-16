import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth import default

from ..config import logger

class CredentialsManager:
    """Centralized credentials management for Google services."""
    
    def __init__(self, token_path='token.pickle', client_secrets_path='client_secret.json'):
        self.token_path = token_path
        self.client_secrets_path = client_secrets_path
        self._credentials = {}  # Cache for different scopes
    
    def get_credentials(self, service, scopes=None):
        """Get cached credentials or authenticate for specific Google service."""
        if service == 'drive':
            scopes = scopes or ['https://www.googleapis.com/auth/drive.readonly']
            return self._get_oauth_credentials(scopes)
        elif service in ['gcs', 'bigquery', 'vertex']:
            # For GCP services, we can use application default credentials
            # or the service account specified in GOOGLE_APPLICATION_CREDENTIALS
            
            # Check if a service account file is specified
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                return service_account.Credentials.from_service_account_file(
                    os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                    scopes=scopes
                )
            else:
                # Use application default credentials
                credentials, _ = default(scopes=scopes)
                return credentials
        
        raise ValueError(f"Unknown service: {service}")
    
    def _get_oauth_credentials(self, scopes):
        """Get OAuth credentials for user-facing services like Drive."""
        # Create a scope-specific key for caching
        scope_key = ','.join(sorted(scopes))
        
        # Return cached credentials if already loaded and valid
        if scope_key in self._credentials and self._credentials[scope_key].valid:
            return self._credentials[scope_key]
            
        creds = None
        # Load token from pickle file if it exists
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.error(f"Error loading credentials from token file: {str(e)}")
                
        # Refresh or create new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {str(e)}")
                    creds = None
            else:
                if not os.path.exists(self.client_secrets_path):
                    raise FileNotFoundError(
                        f"Client secrets file not found: {self.client_secrets_path}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_path, scopes)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for future use
            if creds:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
        
        # Cache the credentials
        self._credentials[scope_key] = creds
        return creds

# Create a singleton instance
credentials_manager = CredentialsManager()