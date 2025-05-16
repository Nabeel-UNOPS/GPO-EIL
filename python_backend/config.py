import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure GCP project
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Configure GCS buckets
DOCUMENTS_BUCKET = os.getenv("GCS_DOCUMENTS_BUCKET")
# Folders within the main bucket - not separate buckets
POLICY_FOLDER = os.getenv("GCS_POLICY_FOLDER", "policy_docs")
# INDEX_FOLDER = os.getenv("GCS_INDEX_FOLDER", "vector_index")

# Construct full GCS paths
POLICY_PATH = f"gs://{DOCUMENTS_BUCKET}/{POLICY_FOLDER}"
# INDEX_PATH = f"gs://{DOCUMENTS_BUCKET}/{INDEX_FOLDER}"

# Configure BigQuery dataset and table
BQ_FA_DATASET = os.getenv("BQ_FA_DATASET")
BQ_FA_TABLE = os.getenv("BQ_FA_TABLE")

BQ_MIT_DATASET = os.getenv("BQ_MIT_DATASET")
BQ_MIT_TABLE = os.getenv("BQ_MIT_TABLE")

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)