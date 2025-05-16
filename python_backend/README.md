# Python Backend

This is the Python backend for the SDG Insight Engine application. It processes documents, extracts text content, and uses Google Cloud Platform services to analyze sustainability projects.

## Features

- Document processing and text extraction
- Google Cloud Storage integration for scalable file storage
- Vertex AI integration for LLM-powered analysis
- Vector search capabilities for policy document retrieval
- Cloud Logging for monitoring and debugging
- Secret Manager integration for secure credential management

## Setup Instructions

### Local Development

1. Create a virtual environment:
   ```
   conda create -n sgd-insight-engine python=3.12
   ```

2. Activate the virtual environment:
   - On Windows: `sgd-insight-engine\Scripts\activate`
   - On macOS/Linux: `source sgd-insight-engine/bin/activate` or conda activate sgd-insight-engine

3. Install the dependencies:
   ```
   cd python_backend
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file to add your actual API keys and GCP settings.

5. Run the application:
   ```
   python app.py
   ```

The API will be available at `http://localhost:5001`.

### Google Cloud Setup

#### Prerequisites

1. Create a Google Cloud project
2. Enable the following APIs:
   - Cloud Storage
   - Vertex AI
   - Secret Manager
   - Cloud Logging

#### Authentication

1. Install the Google Cloud CLI: https://cloud.google.com/sdk/docs/install

2. Authenticate with your Google account:
   ```
   gcloud auth login
   ```

3. Set your project:
   ```
   gcloud config set project YOUR_PROJECT_ID
   ```

4. Create a service account and download the key:
   ```
   gcloud iam service-accounts create sgd-insight-app
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:sgd-insight-app@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/storage.admin"
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:sgd-insight-app@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/aiplatform.user"
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:sgd-insight-app@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:sgd-insight-app@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/logging.logWriter"
   
   gcloud iam service-accounts keys create key.json --iam-account=sgd-insight-app@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

5. Set the environment variable for authentication:
   ```
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

#### Setting Up Cloud Resources

1. Create Cloud Storage buckets:
   ```
   gsutil mb -l us-central1 gs://sgd-insight-documents
   gsutil mb -l us-central1 gs://sgd-insight-policies
   ```

2. Store secrets in Secret Manager:
   ```
   echo -n "your-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
   ```

## Deployment Options

### Cloud Run

1. Build and deploy the container:
   ```
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/sgd-insight-engine
   gcloud run deploy sgd-insight-engine --image gcr.io/YOUR_PROJECT_ID/sgd-insight-engine --platform managed
   ```

### App Engine

1. Create an `app.yaml` file:
   ```yaml
   runtime: python39
   entrypoint: gunicorn -b :$PORT app:app
   
   env_variables:
     GCP_PROJECT_ID: "your-project-id"
     GCP_LOCATION: "us-central1"
     GCS_DOCUMENTS_BUCKET: "sgd-insight-documents"
     GCS_POLICY_BUCKET: "sgd-insight-policies"
   ```

2. Deploy to App Engine:
   ```
   gcloud app deploy
   ```

## API Endpoints

### POST /api/analyze

Analyzes a document for SDG metrics.

**Request:**
- Content-Type: multipart/form-data
- Body: 
  - file (document file: PDF, DOCX, TXT)
  - question (optional): Specific question to analyze

**Response:**
```json
{
  "relevant_sdgs": [
    "SDG 7: Affordable and Clean Energy",
    "SDG 13: Climate Action"
  ],
  "sdg_indicators": [
    "7.2.1 Renewable energy share in the total final energy consumption",
    "13.2.2 Total greenhouse gas emissions per year"
  ],
  "remote_sensing": [
    "Landsat 8",
    "Sentinel-2",
    "Google Earth Engine"
  ],
  "project_tools": [
    "QGIS",
    "Global Forest Watch",
    "SDG Tracker"
  ],
  "timestamp": "2023-09-10T15:30:45.123Z",
  "filename": "project_document.pdf"
}
```

### GET /api/health

Health check endpoint to verify service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-09-10T15:30:45.123Z",
  "version": "1.0.0",
  "services": {
    "gcs": true,
    "policy_index": true,
    "vertex_ai": true
  }
}
```

## Architecture

The application uses a hybrid architecture that can run both locally and in the cloud:

1. **File Storage**:
   - Local file system for development
   - Google Cloud Storage for production

2. **Document Processing**:
   - Local processing with Docling Reader
   - Option to use Document AI in production

3. **Vector Search**:
   - Local Llama Index for development
   - Vertex AI Vector Search for production

4. **LLM Integration**:
   - Direct Gemini API for development
   - Vertex AI for production

This hybrid approach allows for easy local development while providing a scalable path to production.
