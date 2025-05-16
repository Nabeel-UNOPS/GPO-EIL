import os
import tempfile
from typing import Optional, Tuple, Dict, List

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.docling import DoclingReader

import sys
sys.path.append('/Users/beckyxu/Documents/GitHub/sgd-insight-engine')

from python_backend.config import logger
from python_backend.storage.drive import download_file as drive_download
from python_backend.storage.gcs import download_file as gcs_download, upload_file
from python_backend.storage.bigquery import is_document_already_processed, mark_document_as_processed
from python_backend.utils.logging import sanitize_metadata_for_chroma
from python_backend.ai.models import text_splitter, embed_model  # Import AI models

import re
import io
import pickle
import mimetypes
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import requests
import logging
# Initialize the DoclingReader (moved from global scope in doc_processing.py)
docling_reader = DoclingReader()

def create_vector_index(file_path: str, index_name: str = None) -> Tuple[Optional[VectorStoreIndex], Optional[str]]:
    """
    Create a vector index for a document.
    
    Args:
        file_path: Path to the document file.
        index_name: Optional name for the index.
        
    Returns:
        Tuple containing the index and a description (or both None if failed).
    """
    try:
        # Read file with Docling
        docs = docling_reader.load_data(file_path)
        
        if not docs:
            logger.error(f"No document content loaded from {file_path}")
            return None, None
            
        # Add metadata to documents
        document_description = f"Document: {os.path.basename(file_path)}"
        for doc in docs:
            doc.metadata = {
                "file_name": os.path.basename(file_path),
                "document_type": "Project FA",  # or whatever type
                "original_source": file_path,
            }
            doc.metadata = sanitize_metadata_for_chroma(doc.metadata)
        
        # Create a storage context with Chroma
        import chromadb
        from llama_index.vector_stores.chroma import ChromaVectorStore
        
        index_id = index_name or f"index-{os.path.basename(file_path)}"
        chroma_client = chromadb.Client()
        chroma_collection = chroma_client.get_or_create_collection(index_id)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create index from documents
        index = VectorStoreIndex.from_documents(
            documents=docs,
            transformations=[text_splitter],
            storage_context=storage_context
        )
        
        return index, document_description
        
    except Exception as e:
        logger.error(f"Error creating vector index for {file_path}: {str(e)}")
        return None, None

def process_document(file_link: str) -> Optional[Dict]:
    """
    Process a document and create complete text.
    
    Args:
        file_link: The link to the document.
        
    Returns:
        Dict with index information {"file_id": file_link used as the id, "text_doc_fa": text_doc_fa} 
    """
    
    try:
        logger.info(f"Processing document: {file_link}")
        
        # Download file
        temp_file_path = create_tempfile_path(file_link)
        if not temp_file_path:
            logger.error(f"Failed to download document: {file_link}")
            return None
            
        try:
            # Create a unique index ID for this document
            file_id = os.path.basename(file_link) # return this 
            docs = docling_reader.load_data(temp_file_path)
            text_doc_fa = ' '.join(doc.text.strip() for doc in docs) # return this 
            
            return {
                "file_id": file_link,
                "text_doc_fa": text_doc_fa
            }
            
        finally:
            # Clean up
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error processing document {file_link}: {str(e)}")
        return None

def process_document_links(file_links: List[str], 
                          index_name: str = 'project-documents-index', 
                          skip_processed_check: bool = False) -> Dict:
    """
    Process a list of document links and create indices for each document.
    
    Args:
        file_links: List of file links (Google Drive URLs or GCS URIs).
        index_name: Base name for the vector indices.
        skip_processed_check: If True, skips checking if documents have already been processed
                             (useful for bulk processing of known new documents).
        
    Returns:
        Dict mapping document descriptions to their indices.
    """
    indices_dict = {}
    processed_count = 0
    error_count = 0
    skipped_count = 0
    
    logger.info(f"Processing {len(file_links)} documents" + 
               (" (skipping processed check)" if skip_processed_check else ""))
    
    for i, link in enumerate(file_links):
        logger.info(f"Processing document {i+1}/{len(file_links)}: {link}")
        
        # Check if document has already been processed (unless skipped)
        document_index_name = f"{index_name}"
        if not skip_processed_check and is_document_already_processed(link, document_index_name):
            logger.info(f"Document already processed, skipping: {link}")
            skipped_count += 1
            continue
        
        try:
            result = process_document(
                file_link=link,
                index_name=document_index_name
            )
            
            if result:
                indices_dict[result["description"]] = {
                    "index": result["index"], 
                    "file_link": link
                }
                processed_count += 1
                # Mark as successfully processed
                mark_document_as_processed(link, document_index_name)
            else:
                error_count += 1
                # Mark as failed
                mark_document_as_processed(link, document_index_name, 
                                          status="failed", 
                                          error_message="Failed to create index")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error processing document {link}: {error_message}")
            error_count += 1
            # Mark as failed with error message
            mark_document_as_processed(link, document_index_name, 
                                      status="failed", 
                                      error_message=error_message)
        
        # Optional: Log progress every 10 files
        if i % 10 == 0 and i > 0:
            logger.info(f"Progress: {i}/{len(file_links)} files processed")
    
    logger.info(f"Indexing complete. Successfully processed {processed_count} files. Errors: {error_count}. Skipped: {skipped_count}")
    return indices_dict


# Assuming cloud_logger is a custom logger defined elsewhere
# cloud_logger = ...

# Standard logging for local development
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Cloud Logging (if credentials are available)
try:
    client = cloud_logging.Client(project=GCP_PROJECT_ID)
    handler = client.get_default_handler()
    cloud_logger = logging.getLogger("cloudLogger")
    cloud_logger.setLevel(logging.INFO)
    cloud_logger.addHandler(handler)
    logger.info("Cloud Logging initialized successfully")
except Exception as e:
    logger.warning(f"Cloud Logging not initialized. Using local logging only: {str(e)}")
    # Create a dummy cloud_logger that logs to the standard logger
    cloud_logger = logger


def create_tempfile_path(file_link: str) -> Optional[str]:
    """
    Download a file from the given link and return the path to a temporary file.

    Supports Google Drive links, GCS URIs, and HTTP/HTTPS URLs.

    Args:
        file_link (str): The link to the file (e.g., Google Drive URL, GCS URI, or HTTP/HTTPS URL).

    Returns:
        Optional[str]: The path to the temporary file, or None if the download fails.
    """
    if file_link.startswith("https://drive.google.com") or "docs.google.com" in file_link:
        return _download_from_google_drive(file_link)
    elif file_link.startswith("gs://"):
        return _download_from_gcs(file_link)
    else:
        return _download_from_http(file_link)

def _download_from_google_drive(file_link: str) -> Optional[str]:
    """Download a file from Google Drive and return the temporary file path."""
    # Extract file ID from various Google Drive URL formats
    file_id = _extract_file_id(file_link)
    if not file_id:
        cloud_logger.error(f"Unsupported Google Drive URL format: {file_link}")
        return None

    # Authenticate and build Drive API client
    drive_service = _authenticate_drive_api()
    if not drive_service:
        return None

    try:
        # Get file metadata
        file_metadata = _get_drive_file_metadata(drive_service, file_id)
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
            cloud_logger.info(f"Download progress: {int(status.progress() * 100)}%")
        fh.close()

        cloud_logger.info(f"{log_message} to {temp_file_path}")
        return temp_file_path

    except Exception as e:
        cloud_logger.error(f"Error downloading from Google Drive: {str(e)}")
        return None

def _download_from_gcs(file_link: str) -> Optional[str]:
    """Download a file from Google Cloud Storage and return the temporary file path."""
    from google.cloud import storage
    storage_client = storage.Client()

    # Extract bucket and blob name
    parts = file_link[5:].split('/', 1)
    if len(parts) < 2:
        cloud_logger.error(f"Invalid GCS URI: {file_link}")
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

        cloud_logger.info(f"Downloaded {blob_name} to {temp_file_path}")
        return temp_file_path
    except Exception as e:
        cloud_logger.error(f"Error downloading from GCS: {str(e)}")
        return None

def _download_from_http(file_link: str) -> Optional[str]:
    """Download a file from an HTTP/HTTPS URL and return the temporary file path."""
    try:
        response = requests.get(file_link, stream=True, timeout=30)
        if response.status_code != 200:
            cloud_logger.error(f"Failed to download file: HTTP {response.status_code}")
            return None

        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        file_extension = mimetypes.guess_extension(content_type) or '.bin'

        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)

        cloud_logger.info(f"Downloaded {file_link} to {temp_file_path}")
        return temp_file_path
    except Exception as e:
        cloud_logger.error(f"Error downloading from HTTP/HTTPS: {str(e)}")
        return None

def _extract_file_id(url: str) -> Optional[str]:
    """Extract the file ID from a Google Drive URL."""
    patterns = [
        r'https://drive\.google\.com/file/d/([^/]+)(?:/view)?',
        r'https://drive\.google\.com/open\?id=([^&]+)',
        r'https://docs\.google\.com/\w+/d/([^/]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def _authenticate_drive_api():
    """Authenticate with Google Drive API and return the service client."""
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = None
    token_path = 'token.pickle'

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secrets_file = 'client_secret.json'
            if not os.path.exists(client_secrets_file):
                cloud_logger.error(f"Client secrets file not found: {client_secrets_file}")
                cloud_logger.error("Download it from Google Cloud Console: https://developers.google.com/drive/api/quickstart/python")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def _get_drive_file_metadata(drive_service, file_id: str) -> Optional[dict]:
    """Retrieve file metadata from Google Drive, searching if direct access fails."""
    try:
        metadata = drive_service.files().get(
            fileId=file_id,
            fields='name,mimeType',
            supportsAllDrives=True
        ).execute()
        cloud_logger.info(f"Successfully found file: {metadata.get('name', 'unknown')}")
        return metadata
    except Exception as e:
        cloud_logger.warning(f"Could not get file metadata directly: {str(e)}")
        cloud_logger.info("Searching for file in user's accessible files...")

        results = drive_service.files().list(
            q=f"'{file_id}' in parents",
            fields="files(id,name,mimeType)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora="allDrives"
        ).execute()

        files = results.get('files', [])
        if not files:
            cloud_logger.error(f"File not found: {file_id}")
            return None
        metadata = files[0]
        cloud_logger.info(f"Found file via search: {metadata.get('name', 'unknown')}")
        return metadata