from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import logging
import json
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, TextNode
from llama_index.readers.docling import DoclingReader
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from google.cloud import storage
from google.cloud import aiplatform
from google.cloud import logging as cloud_logging
import uuid
from vertexai.language_models import TextGenerationModel

# Load environment variables
load_dotenv()

# Configure GCP project
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Configure GCS buckets
DOCUMENTS_BUCKET = os.getenv("GCS_DOCUMENTS_BUCKET")
# Folders within the main bucket
POLICY_FOLDER = os.getenv("GCS_POLICY_FOLDER", "policy_docs")
INDEX_FOLDER = os.getenv("GCS_INDEX_FOLDER", "vector_index")

# Configure BigQuery dataset and table
BQ_FA_DATASET = os.getenv("BQ_FA_DATASET")
BQ_FA_TABLE = os.getenv("BQ_FA_TABLE")



# Define LLM and Embedding Model
vertexai_config={
        "project": GCP_PROJECT_ID,
        "location": GCP_LOCATION,
    }

llm = GoogleGenAI(
    model="gemini-2.0-flash",
    vertexai_config=vertexai_config,
    context_window=200000, # you should set the context window to the max input tokens for the model
    max_tokens=1000,
)

embed_model = GoogleGenAIEmbedding(
    model_name="text-embedding-005", #005 is good for english text; multilingual text, text-multilingual-embedding-002
    embed_batch_size=100,
    vertexai_config=vertexai_config)

EMBED_DIMENSIONS = 768
Settings.llm = llm
Settings.embed_model = embed_model
docling_reader = DoclingReader()
text_splitter = SentenceSplitter(chunk_size=300, chunk_overlap=20)  # Smaller chunks
Settings.text_splitter = text_splitter

chroma_client = chromadb.PersistentClient(path="./chroma_db")

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

# Helper function to sanitize metadata for ChromaDB
def sanitize_metadata_for_chroma(metadata):
    """
    Ensure metadata values are compatible with ChromaDB.
    ChromaDB only accepts str, int, float, or None as values.
    """
    if metadata is None:
        return {}
    
    sanitized = {}
    for key, value in metadata.items():
        # Handle scalar types that are directly supported
        if value is None or isinstance(value, (str, int, float)):
            sanitized[key] = value
        # Convert lists and dicts to strings
        elif isinstance(value, (list, dict)):
            sanitized[key] = str(value)
        # Convert any other types to strings
        else:
            sanitized[key] = str(value)
    
    return sanitized

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# GCP File Storage Logic
# Initialize GCS client
try:
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    # Ensure buckets exist
    def ensure_bucket_exists(bucket_name):
        """Create bucket if it doesn't exist."""
        try:
            bucket = storage_client.bucket(bucket_name)
            return bucket
        except Exception as e:
            cloud_logger.error(f"Error ensuring bucket {bucket_name} exists: {str(e)}")
            return None
    
    documents_bucket = ensure_bucket_exists(DOCUMENTS_BUCKET)
    cloud_logger.info("GCS initialized successfully")
except Exception as e:
    cloud_logger.error(f"Error initializing GCS: {str(e)}")
    documents_bucket = None

# Initialize BigQuery client for Tracking Table
try:
    from google.cloud import bigquery
    # Use the GCP_LOCATION from config to specify the location explicitly
    bigquery_client = bigquery.Client(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    cloud_logger.info("BigQuery client initialized successfully")
    
    # Ensure the processed documents table exists
    def ensure_processed_docs_table_exists():
        """Create the processed documents tracking table if it doesn't exist."""
        try:
            # First ensure the dataset exists
            dataset_id = f"{GCP_PROJECT_ID}.LLM_Tracking"
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = GCP_LOCATION
            
            try:
                bigquery_client.get_dataset(dataset_id)
                cloud_logger.info(f"Dataset {dataset_id} already exists")
            except Exception:
                # Create the dataset if it doesn't exist
                bigquery_client.create_dataset(dataset, exists_ok=True)
                            
            # Define the schema for the processed documents table
            schema = [
                bigquery.SchemaField("file_link", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("index_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("folder_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("process_date", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("status", "STRING", mode="REQUIRED"),  # "success" or "failed"
                bigquery.SchemaField("error_message", "STRING", mode="NULLABLE")
            ]
            
            # Define the table reference
            table_id = f"{GCP_PROJECT_ID}.LLM_Tracking.Processed_Documents"
            table = bigquery.Table(table_id, schema=schema)
            
            # Check if table exists
            try:
                bigquery_client.get_table(table_id)
                cloud_logger.info(f"Table {table_id} already exists")
            except Exception:
                # Create the table if it doesn't exist
                bigquery_client.create_table(table)
                cloud_logger.info(f"Created table {table_id}")
            
            return True
        except Exception as e:
            cloud_logger.error(f"Error ensuring processed documents table exists: {str(e)}")
            return False
    
    # Create the table if it doesn't exist
    processed_docs_table_exists = ensure_processed_docs_table_exists()
except Exception as e:
    cloud_logger.error(f"Error initializing BigQuery client: {str(e)}")
    bigquery_client = None

# Function to check if a document has already been processed
def is_document_already_processed(file_link, index_name=None):
    """
    Check if a document has already been processed and indexed.
    
    Args:
        file_link (str): File link (Google Drive URL or GCS URI)
        folder_name (str, optional): Folder in GCS for the vector index
        index_name (str, optional): Name of the vector index
        
    Returns:
        bool: True if the document has already been processed successfully, False otherwise
    """
    try:
        if not bigquery_client or not processed_docs_table_exists:
            cloud_logger.warning("BigQuery client or processed documents table not initialized")
            return False
            
        # Build query conditions
        conditions = [f"file_link = '{file_link}'"]
        if folder_name:
            conditions.append(f"folder_name = '{folder_name}'")
        if index_name:
            conditions.append(f"index_name = '{index_name}'")
        conditions.append("status = 'success'")
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT COUNT(*) as count
        FROM `{GCP_PROJECT_ID}.{BQ_FA_DATASET}.processed_documents`
        WHERE {where_clause}
        """
        
        query_job = bigquery_client.query(query)
        results = query_job.result()
        
        # Get the count from the results
        for row in results:
            return row.count > 0
            
        return False
    except Exception as e:
        cloud_logger.error(f"Error checking if document is already processed: {str(e)}")
        return False

# Function to mark a document as processed
def mark_document_as_processed(file_link, folder_name, index_name, status="success", error_message=None):
    """
    Record a document as processed in the tracking table.
    
    Args:
        file_link (str): File link (Google Drive URL or GCS URI)
        folder_name (str): Folder in GCS for the vector index
        index_name (str): Name of the vector index
        status (str): Processing status - "success" or "failed"
        error_message (str, optional): Error message if processing failed
        
    Returns:
        bool: True if recording was successful, False otherwise
    """
    try:
        if not bigquery_client or not processed_docs_table_exists:
            cloud_logger.warning("BigQuery client or processed documents table not initialized")
            return False
            
        # Create a row to insert
        row = {
            "file_link": file_link,
            "folder_name": folder_name,
            "index_name": index_name,
            "status": status
        }
        
        if error_message:
            row["error_message"] = error_message
            
        # Insert the row into the table
        table_id = f"{GCP_PROJECT_ID}.{BQ_FA_DATASET}.processed_documents"
        errors = bigquery_client.insert_rows_json(table_id, [row])
        
        if errors:
            cloud_logger.error(f"Error inserting row into processed documents table: {errors}")
            return False
            
        return True
    except Exception as e:
        cloud_logger.error(f"Error marking document as processed: {str(e)}")
        return False

# Get FA Link and info from FA BigQuery
def get_fa_from_bigquery(number_entries = 1):
    """Retrieve document links from BigQuery.
    
    Returns:
        List of document links (GCS URIs or Google Drive links)
    """
    try:
        from google.cloud import bigquery
        # Use the GCP_LOCATION from config to specify the location explicitly
        bigquery_client_fa = bigquery.Client(project=GCP_REPORTS_ID, location=GCP_LOCATION)
        if not bigquery_client_fa:
            cloud_logger.error("BigQuery client not initialized")
            return []
        
        # TODO: CHANGE THIS TO THE ACTUAL COLNAME
        query = f"""
        SELECT 
            Legal_Agreement, 
            File_URL, 
            File_Name,
        FROM `{GCP_PROJECT_ID}.{BQ_FA_DATASET}.{BQ_FA_TABLE}`
        CROSS JOIN
            UNNEST(Legal_Agreement_Files) AS t0
        LIMIT {number_entries}
        """
        
        query_job = bigquery_client_fa.query(query) 
        results = query_job.result()
        
        links = [row.file_url for row in results]
        cloud_logger.info(f"Retrieved {len(links)} document links from BigQuery")
        return links
    except Exception as e:
        cloud_logger.error(f"Error retrieving document links from BigQuery: {str(e)}")
        return []

# Vector database setup with Firestore storage
def initialize_policy_index():
    try:
        chroma_collection = chroma_client.get_or_create_collection("policy_documents")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        if not documents_bucket:
            cloud_logger.error("No documents bucket available")
            return None
        
        # Get all blobs/docs in the policy folder
        blobs = [blob for blob in documents_bucket.list_blobs(prefix=POLICY_FOLDER)]
        if not blobs:
            cloud_logger.info("No new policy documents to process")
            return VectorStoreIndex([], storage_context=storage_context)
        
        # Read docs with Docling and tempfile 
        docling_reader = DoclingReader()
        policy_docs = []
        temp_dir = "/tmp/policy_docs"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download, and read all files in GCS with llamaindex reader, add metadata
        for blob in blobs:
            # get file name 
            blob_name = blob.name.split('/')[-1]
            if not blob_name or blob.name.endswith('/'):
                continue
            
            # create temp file path
            temp_file_path = os.path.join(temp_dir, blob_name)
            try:
                # 1. Download file to temp
                cloud_logger.info(f"Downloading {blob.name} to {temp_file_path}")
                blob.download_to_filename(temp_file_path)
                if not os.path.exists(temp_file_path):
                    cloud_logger.error(f"Failed to download {blob.name}")
                    continue
                
                # 2. Read file from temp
                docs = docling_reader.load_data(temp_file_path)
                
                # 3. Add metadata
                for doc in docs:
                    doc.metadata = {
                        "file_name": blob_name,
                        "document_type": "policy",
                        "source": blob,
                    }
                    policy_docs.append(doc)
            except Exception as e:
                cloud_logger.error(f"Error processing {blob.name}: {str(e)}")
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        
        # Sanitize metadata for ChromaDB compatibility
        for doc in policy_docs:
            cloud_logger.debug(f"Document: {doc.metadata.get('file_name', 'No filename')}")
            doc.metadata = sanitize_metadata_for_chroma(doc.metadata)
        
        if not policy_docs:
            cloud_logger.info("No valid policy documents processed")
            return VectorStoreIndex([], storage_context=storage_context)
            
        # From Document Objects to index - Single step to create index with splitting
        text_splitter = SentenceSplitter(chunk_size=180, chunk_overlap=10)
        cloud_logger.info(f"Processing {len(policy_docs)} documents into index")
        policy_index = VectorStoreIndex.from_documents(
            documents=policy_docs,
            transformations=[text_splitter],
            storage_context=storage_context
        )
        
        return policy_index
        
    except Exception as e:
        cloud_logger.error(f"Failed to initialize policy index: {str(e)}")
        return None

def create_modular_vector_index(file_link, folder_name=INDEX_FOLDER, index_name='project-documents-index'):
    """
    Create a vector index for a single document.
    
    Args:
        file_link (str): File link (Google Drive URL or GCS URI)
        folder_name (str): Folder in GCS for the vector index
        index_name (str): Base name of the vector index
        
    Returns:
        tuple: (VectorStoreIndex, str) - The created index and its description
    """
    try:
        cloud_logger.info(f"Creating vector index for document: {file_link}")
        
        # Create a unique index ID for this document
        file_id = os.path.basename(file_link)
        document_index_name = f"{index_name}-{file_id}"
        
        # Create a FirestoreVectorStore for storing embeddings in Firestore
        vector_store = FirestoreVectorStore(
            project_id=GCP_PROJECT_ID,
            collection_name=document_index_name,
            database_id="sdg-engine"
        )
        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        temp_file_path = None
        
        try:
            # Download file from link to tempfile path
            temp_file_path = create_tempfile_path(file_link)
            
            # Process the file
            docs = docling_reader.load_data(temp_file_path)
            
            # Add metadata to documents
            document_description = f"Document: {os.path.basename(file_link)}"
            for doc in docs:
                doc.metadata = {
                    "file_name": os.path.basename(file_link),
                    "document_type": "Project FA",  # or whatever type
                    # TODO add other metadata, check the query table
                    # "engagement_id":
                    "original_source": file_link,
                }
                doc.metadata = sanitize_metadata_for_chroma(doc.metadata)
            
            # Create index for this document
            index = None
            if docs:
                index = VectorStoreIndex.from_documents(
                    docs,
                    storage_context=storage_context
                )
            
            # Clean up
            if temp_file_path:
                os.remove(temp_file_path)
            
            return index, document_description
            
        except Exception as e:
            cloud_logger.error(f"Error processing file {file_link}: {str(e)}")
            # Clean up on error
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return None, None
        
    except Exception as e:
        cloud_logger.error(f"Error in create_modular_vector_index: {str(e)}")
        return None, None

def process_document_links(file_links, folder_name=INDEX_FOLDER, index_name='project-documents-index', skip_processed_check=False):
    """
    Process a list of document links and create indices for each document.
    
    Args:
        file_links (list): List of file links (Google Drive URLs or GCS URIs)
        folder_name (str): Folder in GCS for the vector indices
        index_name (str): Base name for the vector indices
        skip_processed_check (bool): If True, skips checking if documents have already been processed
                                    (useful for bulk processing of known new documents)
        
    Returns:
        dict: Dictionary mapping document descriptions to their indices
    """
    indices_dict = {}
    processed_count = 0
    error_count = 0
    skipped_count = 0
    
    cloud_logger.info(f"Processing {len(file_links)} documents" + 
                     (" (skipping processed check)" if skip_processed_check else ""))
    
    # TODO change this back to process all links when ready
    for i, link in enumerate(file_links[:2]):
        cloud_logger.info(f"Processing document {i+1}/{len(file_links)}: {link}")
        
        # Check if document has already been processed (unless skipped)
        document_index_name = f"{index_name}"
        if not skip_processed_check and is_document_already_processed(link, folder_name, document_index_name):
            cloud_logger.info(f"Document already processed, skipping: {link}")
            skipped_count += 1
            continue
        
        try:
            index, description = create_modular_vector_index(
                file_link=link,
                folder_name=folder_name,
                index_name=document_index_name
            )
            
            if index and description:
                indices_dict[description] = {"index": index, "file_link": link}
                processed_count += 1
                # Mark as successfully processed
                mark_document_as_processed(link, folder_name, document_index_name)
            else:
                error_count += 1
                # Mark as failed
                mark_document_as_processed(link, folder_name, document_index_name, 
                                          status="failed", 
                                          error_message="Failed to create index")
        except Exception as e:
            error_message = str(e)
            cloud_logger.error(f"Error processing document {link}: {error_message}")
            error_count += 1
            # Mark as failed with error message
            mark_document_as_processed(link, folder_name, document_index_name, 
                                      status="failed", 
                                      error_message=error_message)
        
        # Optional: Log progress every 10 files
        if i % 10 == 0 and i > 0:
            cloud_logger.info(f"Progress: {i}/{len(file_links)} files processed")
    
    cloud_logger.info(f"Indexing complete. Successfully processed {processed_count} files. Errors: {error_count}. Skipped: {skipped_count}")
    return indices_dict

def answer_question(question, project_chunks, policy_index, use_vertex=True):
    """Answer a question by cross-referencing project documents with policy documents.
    
    Args:
        question (text): text string of a question
        project_chunks (list): list of text chunks returned from process_project_documents
        policy_index (object): policy index processed by Llama-index or Vertex AI
        use_vertex (bool): whether to use Vertex AI for completions (default) or fall back to Gemini
 
    Returns:
        text: text output from LLM 
    """
    try:
        # Combine all project chunks into a single context
        project_context = "\n".join(project_chunks) if project_chunks else "No project documents available."
        
        # Get relevant policies from the policy index
        if policy_index:
            query_engine = policy_index.as_query_engine()
            relevant_policies_response = query_engine.query(question)
            relevant_policies = str(relevant_policies_response)
        else:
            relevant_policies = "Policy index not available."
        
        if use_vertex:
            # Use Vertex AI for completion
            prompt = f"""
            You are an expert analyst specializing in sustainable development and project evaluation. Your task is to analyze a project description document against three reference documents: 
            1. SDG Indicators (containing Sustainable Development Goals and their metrics),
            2. Remote Sensing Policy (guidelines on remote sensing applicability),
            3. Available Tools to Assist Projects (a list of tools for project assistance).

            Given the project description and relevant snippets from these reference documents, provide a structured analysis answering the following:
            - Which SDGs (e.g., SDG 1, SDG 13) are most relevant to the project, and why?
            - Which specific SDG indicators (e.g., 13.1.1) are applicable, and how do they relate to the project?
            - Is remote sensing applicable to this project? If yes, explain how; if no, explain why not.
            - What available tools (e.g., satellite imagery analysis) can be used to develop and measure the project, and how would they help?
            
            If the project description lacks detail, make reasonable assumptions and note them in the output.
            
            Base your answers solely on the provided context. Structure your response as a JSON object with keys: 'relevant_sdgs', 'sdg_indicators', 'remote_sensing', and 'project_tools'. If information is missing or unclear, note it explicitly in the response.
            
            Example input: "A project to monitor deforestation in the Amazon using satellite data."
            Example output:
            "relevant_sdgs": ["SDG 15: Life on Land", "SDG 13: Climate Action"],
            "sdg_indicators": ["15.1.1 Forest area as a proportion of total land area", "13.2.2 Total greenhouse gas emissions"],
            "remote_sensing": ["Landsat 8", "Sentinel-2", "Google Earth Engine"],
            "project_tools": ["QGIS", "Global Forest Watch", "SDG Tracker"]
            
            Project Context:
            {tempfile_index}
            
            Policy Requirements:
            {policy_indices}
            
            Question: {question}
            
            Please provide a detailed analysis of how the project aligns with policies and any potential compliance issues.
            """
            # prompt = f'{system_prompt}\n\nContext:\n{combined_context}\n\nQuestion: {question}'
            response = get_vertex_completion(prompt)
            return response
        else:
            # Fall back to Gemini if available
            try:
                model = genai.GenerativeModel('gemini-pro')
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                ]
                
                prompt = f"""
                I need to analyze a project document against policy requirements.
                
                Project Context:
                {project_context}
                
                Policy Requirements:
                {relevant_policies}
                
                Question: {question}
                
                Please provide a detailed analysis of how the project aligns with policies and any potential compliance issues.
                """
                
                response = model.generate_content(
                    contents=prompt,
                    safety_settings=safety_settings,
                    generation_config={"temperature": 0.2, "max_output_tokens": 1024, "top_p": 0.8, "top_k": 40}
                )
                
                return response.text
            except Exception as e:
                cloud_logger.error(f"Error using Gemini for completion: {str(e)}")
                return f"Error obtaining answer: {str(e)}"
    except Exception as e:
        cloud_logger.error(f"Error in answer_question: {str(e)}")
        return f"Error obtaining answer: {str(e)}"

# //////////////////
import os
import re
import tempfile
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

# Assuming cloud_logger is a custom logger defined elsewhere
# cloud_logger = ...

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
  
    
if __name__ == '__main__':
    
    print('starting') 

    # test_link = "https://docs.google.com/document/d/136r1EP7H7i_KXAzMniqYUV5IyuJs6glN3LCgd5P9N_k"
    test_link = "https://drive.google.com/file/d/1BnxsDqskNB2Q4KLcZ7mAK-tZ6BGXaiEY"

    # Try downloading the file
    result = create_tempfile_path(test_link)
    if result:
        print(f"Success! Downloaded file to: {result}")
        print(f"File contents can now be processed with DoclingReader or other document processors")
    else:
        print("Failed to download file. See error logs for details.")
