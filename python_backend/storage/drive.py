import os
import io
import re
import pickle
import tempfile
import mimetypes
from typing import Optional, Dict, List
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from ..config import logger

_drive_service = None

def get_drive_service():
    """Get authenticated Google Drive service client."""
    global _drive_service
    if _drive_service is None:
        try:
            _drive_service = _authenticate_drive_api()
            logger.info("Google Drive service initialized")
        except Exception as e:
            logger.error(f"Error initializing Drive service: {str(e)}")
            return None
    return _drive_service

def download_file(file_link: str) -> Optional[str]:
    """
    Download a file from Google Drive and return the temporary file path.
    
    Args:
        file_link: The Google Drive URL to download.
        
    Returns:
        Optional[str]: Path to the downloaded file, or None if download failed.
    """
    # Extract file ID from various Google Drive URL formats
    file_id = extract_file_id(file_link)
    if not file_id:
        logger.error(f"Unsupported Google Drive URL format: {file_link}")
        return None

    # Authenticate and build Drive API client
    drive_service = get_drive_service()
    if not drive_service:
        return None

    try:
        # Get file metadata
        file_metadata = get_file_metadata(drive_service, file_id)
        if not file_metadata:
            return None

        file_name = file_metadata.get('name', 'unknown_file')
        mime_type = file_metadata.get('mimeType', 'application/octet-stream')

        # Handle Google Workspace documents and regular files
        GOOGLE_WORKSPACE_MIME_TYPES = {
            'application/vnd.google-apps.document': (
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'
            ),
            'application/vnd.google-apps.spreadsheet': (
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'
            ),
            'application/vnd.google-apps.presentation': (
                'application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx'
            ),
        }

        if mime_type in GOOGLE_WORKSPACE_MIME_TYPES:
            export_mime_type, file_extension = GOOGLE_WORKSPACE_MIME_TYPES[mime_type]
            request = drive_service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            log_message = f"Exported {file_name} as {file_extension}"
        else:
            file_extension = mimetypes.guess_extension(mime_type) or '.bin'
            request = drive_service.files().get_media(fileId=file_id)
            log_message = f"Downloaded {file_name}"

        # Download to a temporary file
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name

        fh = io.FileIO(temp_file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f"Download progress: {int(status.progress() * 100)}%")
        fh.close()

        logger.info(f"{log_message} to {temp_file_path}")
        return temp_file_path

    except Exception as e:
        logger.error(f"Error downloading from Google Drive: {str(e)}")
        return None

def extract_file_id(url: str) -> Optional[str]:
    """
    Extract the file ID from a Google Drive URL.
    
    Supports various formats:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://docs.google.com/document/d/FILE_ID/edit
    
    Args:
        url: The Google Drive URL.
        
    Returns:
        Optional[str]: The extracted file ID, or None if no match.
    """
    if not url:
        return None
        
    # Standard Drive URL format
    match = re.search(r'/file/d/([^/]+)', url)
    if match:
        return match.group(1)
        
    # Open link format
    match = re.search(r'[?&]id=([^&]+)', url)
    if match:
        return match.group(1)
        
    # Google Docs, Sheets, etc.
    match = re.search(r'/(document|spreadsheets|presentation)/d/([^/]+)', url)
    if match:
        return match.group(2)
        
    return None

def get_file_metadata(drive_service, file_id: str):
    """
    Retrieve file metadata from Google Drive.
    
    Args:
        drive_service: The Drive API service instance.
        file_id: The ID of the file to retrieve metadata for.
        
    Returns:
        dict: The file metadata, or None if retrieval failed.
    """
    try:
        # Try direct access first
        return drive_service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
    except Exception as e:
        logger.warning(f"Error retrieving file metadata directly: {str(e)}")
        
        # Try searching for the file
        try:
            results = drive_service.files().list(
                q=f"id='{file_id}'",
                spaces='drive',
                fields='files(id,name,mimeType)',
                pageToken=None
            ).execute()
            
            items = results.get('files', [])
            if items:
                return items[0]
            else:
                logger.error(f"File with ID {file_id} not found")
                return None
        except Exception as search_error:
            logger.error(f"Error searching for file: {str(search_error)}")
            return None