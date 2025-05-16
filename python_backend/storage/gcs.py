import os
import tempfile
import mimetypes
from typing import Optional
from google.cloud import storage

from ..auth.credentials import credentials_manager
from ..config import logger, DOCUMENTS_BUCKET

_storage_client = None


def get_storage_client():
    """Get authenticated Google Cloud Storage client."""
    global _storage_client
    if _storage_client is None:
        try:
            credentials = credentials_manager.get_credentials('gcs')
            _storage_client = storage.Client(credentials=credentials)
            logger.info("GCS client initialized")
        except Exception as e:
            logger.error(f"Error initializing GCS client: {str(e)}")
            return None
    return _storage_client

def ensure_bucket_exists(bucket_name):
    """
    Create a bucket if it doesn't exist.
    
    Args:
        bucket_name: Name of the GCS bucket.
        
    Returns:
        The bucket object if it exists, None otherwise.
    """
    if not bucket_name:
        logger.error("Bucket name not provided")
        return None
        
    storage_client = get_storage_client()
    if not storage_client:
        return None
        
    try:
        bucket = storage_client.bucket(bucket_name)
        return bucket
    except Exception as e:
        logger.error(f"Error ensuring bucket {bucket_name} exists: {str(e)}")
        return None

def download_file(file_link: str) -> Optional[str]:
    """
    Download a file from Google Cloud Storage and return the temporary file path.
    
    Args:
        file_link: The GCS URI (gs://bucket-name/blob-name).
        
    Returns:
        Optional[str]: Path to the downloaded file, or None if download failed.
    """
    storage_client = get_storage_client()
    if not storage_client:
        return None

    # Extract bucket and blob name
    parts = file_link[5:].split('/', 1)
    if len(parts) < 2:
        logger.error(f"Invalid GCS URI: {file_link}")
        return None
    bucket_name, blob_name = parts

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content_type = blob.content_type or 'application/octet-stream'
        file_extension = mimetypes.guess_extension(content_type) or '.bin'

        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
            blob.download_to_filename(temp_file_path)

        logger.info(f"Downloaded {blob_name} to {temp_file_path}")
        return temp_file_path
    except Exception as e:
        logger.error(f"Error downloading from GCS: {str(e)}")
        return None

def upload_file(local_file_path: str, destination_folder: str, destination_filename: str = None) -> Optional[str]:
    """
    Upload a file to Google Cloud Storage.
    
    Args:
        local_file_path: Path to the local file.
        destination_folder: Folder in GCS to upload to (without bucket name).
        destination_filename: Name to use in GCS. If None, uses the basename of local_file_path.
        
    Returns:
        Optional[str]: GCS URI of the uploaded file, or None if upload failed.
    """
    if not os.path.exists(local_file_path):
        logger.error(f"Local file does not exist: {local_file_path}")
        return None
        
    storage_client = get_storage_client()
    if not storage_client:
        return None
        
    if not destination_filename:
        destination_filename = os.path.basename(local_file_path)
        
    blob_path = os.path.join(destination_folder, destination_filename).replace('\\', '/')
    
    try:
        bucket = storage_client.bucket(DOCUMENTS_BUCKET)
        blob = bucket.blob(blob_path)
        
        # Set content type based on file extension
        content_type, _ = mimetypes.guess_type(local_file_path)
        if content_type:
            blob.content_type = content_type
            
        blob.upload_from_filename(local_file_path)
        logger.info(f"Uploaded {local_file_path} to gs://{DOCUMENTS_BUCKET}/{blob_path}")
        
        return f"gs://{DOCUMENTS_BUCKET}/{blob_path}"
    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        return None

def list_files(folder_path: str):
    """
    List all files in a GCS folder.
    
    Args:
        folder_path: Path to the folder in GCS (without bucket name).
        
    Returns:
        List of blob objects, or None if listing failed.
    """
    storage_client = get_storage_client()
    if not storage_client:
        return None
        
    try:
        bucket = storage_client.bucket(DOCUMENTS_BUCKET)
        blobs = list(bucket.list_blobs(prefix=folder_path))
        return [blob for blob in blobs if not blob.name.endswith('/')]
    except Exception as e:
        logger.error(f"Error listing files in GCS folder {folder_path}: {str(e)}")
        return None