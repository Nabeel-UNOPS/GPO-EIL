from ast import main
import os
from google.cloud import bigquery

from python_backend.auth.credentials import credentials_manager
from python_backend.config import logger, GCP_PROJECT_ID, BQ_FA_DATASET, BQ_FA_TABLE, BQ_MIT_DATASET, BQ_MIT_TABLE, GCP_LOCATION
# BQ_REPORTS_RESULT

_bigquery_client = None
_processed_docs_table_exists = False

# define the schema for uploading analysis results
schema = [
    bigquery.SchemaField("file_id", "STRING", mode="REQUIRED", description="Unique identifier for the file"),
    bigquery.SchemaField("project_summary", "STRING", mode="NULLABLE", description="A summary of the project"),
    bigquery.SchemaField("objectives", "STRING", mode="NULLABLE", description="An analysis item related to the project summary"),
    bigquery.SchemaField("problems_addressed", "STRING", mode="NULLABLE", description="An analysis item related to the project summary"),
    bigquery.SchemaField("beneficiaries_and_impacted_groups", "STRING", mode="NULLABLE", description="An analysis item related to the project summary"),
    bigquery.SchemaField("anticipated_outcomes_short_and_long_term", "STRING", mode="NULLABLE", description="An analysis item related to the project summary"),
    bigquery.SchemaField(
        "quantifiable_outcome_list",
        "RECORD",
        mode="REPEATED",
        description="List of quantifiable outcomes",
        fields=[
            bigquery.SchemaField("outcome_item", "STRING", mode="NULLABLE", description="A specific quantifiable outcome item")
        ],
    ),
    bigquery.SchemaField(
        "sdg_goals",
        "RECORD",
        mode="REPEATED",
        description="List of Sustainable Development Goals associated with the project",
        fields=[
            bigquery.SchemaField("sdg_goal", "STRING", mode="NULLABLE", description="The SDG goal number (e.g., 16)"),
            bigquery.SchemaField("name", "STRING", mode="NULLABLE", description="The name of the SDG goal (e.g., Peace, Justice and Strong Institutions)"),
            bigquery.SchemaField("relevance", "STRING", mode="NULLABLE", description="Explanation of how the project relates to the SDG goal"),
        ],
    ),
    bigquery.SchemaField(
        "sdg_indicators",
        "RECORD",
        mode="REPEATED",
        description="List of Sustainable Development Goal indicators associated with the project",
        fields=[
            bigquery.SchemaField("sdg_indicator", "STRING", mode="NULLABLE", description="The SDG indicator number (e.g., 16.4.1)"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE", description="Description of the SDG indicator"),
            bigquery.SchemaField("measurability", "STRING", mode="NULLABLE", description="Explanation of how the indicator can be measured in relation to the project"),
        ],
    ),
    bigquery.SchemaField(
        "remote_sensing_tools",
        "RECORD",
        mode="REPEATED",
        description="List of remote sensing tools used in the project",
        fields=[
            bigquery.SchemaField("technology", "STRING", mode="NULLABLE", description="The name of the remote sensing technology or tool"),
            bigquery.SchemaField("relevance_justification", "STRING", mode="NULLABLE", description="Explanation of why the tool is relevant to the project, as supported by the project description"),
            bigquery.SchemaField("project_description_context", "STRING", mode="NULLABLE", description="Exact section/paragraph/page/sentence(s) from the project description that justify the tool's inclusion, including a direct quote and its location"),
        ],
    ),
]


def get_bigquery_client(location=GCP_LOCATION):
    """Get authenticated BigQuery client."""
    # a global variable is accessible throughout the entire module (file)
    global _bigquery_client
    if _bigquery_client is None:
        try:
            credentials = credentials_manager.get_credentials('bigquery')
            _bigquery_client = bigquery.Client(project=GCP_PROJECT_ID, credentials=credentials)
            logger.info("BigQuery client initialized")
        except Exception as e:
            logger.error(f"Error initializing BigQuery client: {str(e)}")
            return None
    return _bigquery_client

def ensure_processed_docs_table_exists():
    """
    Create the processed documents tracking table if it doesn't exist.
    
    Returns:
        bool: True if the table exists or was created, False otherwise.
    """
    global _processed_docs_table_exists
    
    if _processed_docs_table_exists:
        return True
        
    bigquery_client = get_bigquery_client()
    if not bigquery_client:
        return False
        
    try:
        # Check if the dataset exists
        dataset_id = f"{GCP_PROJECT_ID}.{BQ_MIT_DATASET}"
        try:
            bigquery_client.get_dataset(dataset_id)
            logger.info(f"Dataset {dataset_id} exists")
        except Exception as e:
            # Dataset doesn't exist, create it
            logger.info(f"Dataset {dataset_id} does not exist. Creating it.")
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = "US"  # Set the location
            bigquery_client.create_dataset(dataset, timeout=30)
            
        # Define table schema
        schema = [
            bigquery.SchemaField("file_link", "STRING", mode="REQUIRED", description="Document URL or GCS URI"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED", description="Processing status (success/failed)"),
            bigquery.SchemaField("error_message", "STRING", mode="NULLABLE", description="Error message if processing failed"),
            bigquery.SchemaField("processed_at", "TIMESTAMP", mode="REQUIRED", description="Processing timestamp"),
        ]
        
        # Define table
        table_id = f"{GCP_PROJECT_ID}.{BQ_MIT_DATASET}.processed_documents"
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="processed_at"
        )
        
        # Create table if it doesn't exist
        try:
            bigquery_client.get_table(table_id)
            logger.info(f"Table {table_id} exists")
        except Exception as e:
            logger.info(f"Table {table_id} does not exist. Creating it.")
            table = bigquery_client.create_table(table, exists_ok=True)
            
        _processed_docs_table_exists = True
        return True
        
    except Exception as e:
        logger.error(f"Error creating processed documents table: {str(e)}")
        return False

def is_document_already_processed(file_link, engagement_code = None):
    """
    Check if a document has already been processed and indexed.
    
    Args:
        file_link (str): File link (Google Drive URL or GCS URI)
        engagement_code: Engagement code of the project
        
    Returns:
        bool: True if the document has already been processed successfully, False otherwise
    """
    try:
        bigquery_client = get_bigquery_client()
        if not bigquery_client or not ensure_processed_docs_table_exists():
            logger.warning("BigQuery client or processed documents table not initialized")
            return False
            
        # Build query conditions
        conditions = [f"file_link = '{file_link}'"]
        # If there are more identifying fields
        # if engagement_code:
        #     conditions.append(f"engagement_code = '{engagement_code}'")
        conditions.append("status = 'success'")
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT COUNT(*) as count
        FROM `{GCP_PROJECT_ID}.{BQ_MIT_DATASET}.processed_documents`
        WHERE {where_clause}
        """
        query_job = bigquery_client.query(query)
        results = query_job.result()
        
        # Get the count from the results
        for row in results:
            return row.count > 0
            
        return False
    except Exception as e:
        logger.error(f"Error checking if document is already processed: {str(e)}")
        return False

def mark_document_as_processed(file_link, status="success", error_message=None):
    """
    Record a document as processed in the tracking table.
    
    Args:
        file_link (str): File link (Google Drive URL or GCS URI)
        status (str): Processing status - "success" or "failed"
        error_message (str, optional): Error message if processing failed
        
    Returns:
        bool: True if recording was successful, False otherwise
    """
    try:
        bigquery_client = get_bigquery_client()
        if not bigquery_client or not ensure_processed_docs_table_exists():
            logger.warning("BigQuery client or processed documents table not initialized")
            return False
            
        # Create a row to insert
        from datetime import datetime
        row = {
            "file_link": file_link,
            "status": status,
            "processed_at": datetime.now().isoformat()
        }
        
        if error_message:
            row["error_message"] = error_message
            
        # Insert the row into the table
        table_id = f"{GCP_PROJECT_ID}.{BQ_MIT_DATASET}.processed_documents"
        errors = bigquery_client.insert_rows_json(table_id, [row])
        
        if errors:
            logger.error(f"Error inserting row into processed documents table: {errors}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error marking document as processed: {str(e)}")
        return False

def get_fa_from_bigquery(number_entries=10):
    """
    Retrieve document links from BigQuery.
    
    Args:
        number_entries (int): Number of entries to retrieve.
    
    Returns:
        List of document links (GCS URIs or Google Drive links)
    """
    try:
        # Use a different client for the project
        bigquery_client_fa = get_bigquery_client()
        if not bigquery_client_fa:
            logger.error("BigQuery client not initialized")
            return []
        
        # Query to retrieve document links
        query = f"""
        SELECT 
            -- Legal_Agreement,
            t0.File_URL,
            -- t1.Donor,
        FROM 
            `{GCP_PROJECT_ID}.{BQ_FA_DATASET}.{BQ_FA_TABLE}`
            CROSS JOIN
            UNNEST(Legal_Agreement_Files) AS t0
            -- CROSS JOIN
            --     UNNEST(Donors) AS t1
        WHERE
            t0.File_URL IS NOT NULL
        LIMIT {number_entries}
        """
        
        query_job = bigquery_client_fa.query(query) 
        results = query_job.result()
        
        links = [row["File_URL"] for row in results]
        logger.info(f"Retrieved {len(links)} document links from BigQuery")
        return links
    except Exception as e:
        logger.error(f"Error retrieving document links from BigQuery: {str(e)}")
        return []

# Update Table with New Row
def upload_to_bigquery(row: dict, project_id = GCP_PROJECT_ID, dataset_id = BQ_MIT_DATASET, table_id = BQ_MIT_TABLE) -> None:
    """
    Upload a single row to a BigQuery table with Repeated Fields.
    Args:
        row: Dict[str, Any], processed row from json document analysis results to upload,
        project_id: str, GCP project id, 
        dataset_id: str, GCS dataset id, 
        table_id: str, GCS table id

    Returns:
    """

    bigquery_client = get_bigquery_client()
    if not bigquery_client or not ensure_processed_docs_table_exists():
        logger.warning("BigQuery client or processed documents table not initialized")
        return False
            
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_APPEND"
    )
    file_link = row.get("file_id")  # or any other field that identifies the document source
    try:
        job = bigquery_client.load_table_from_json([row], table_ref, job_config=job_config)
        job.result()
        logger.info(f"Uploaded row for {file_link} to {table_ref}")
        if file_link:
            mark_document_as_processed(file_link, status="success")
        return True

    except Exception as e:
        logger.error(f"Error uploading to BigQuery: {str(e)}")
        raise
 
# The big query table that stores analysis result
def create_bigquery_table(project_id = GCP_PROJECT_ID, dataset_id = BQ_MIT_DATASET, table_id = BQ_MIT_TABLE) -> None:
    """
    Create a BigQuery with name: table_id table with Repeated Fields to store analysis data.
    Args:
        project_id: str, GCP project id, 
        dataset_id: str, GCS dataset id, 
        table_id: str, GCS table id

    Returns:
    """
    
    bigquery_client = get_bigquery_client()
    if not bigquery_client or not ensure_processed_docs_table_exists():
        logger.warning("BigQuery client or processed documents table not initialized")
        return False
            
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    table = bigquery.Table(table_ref, schema=schema)
    try:
        client = get_bigquery_client()
        table = client.create_table(table)  # Make an API request.
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Exception as e:
        print(f"Error creating table: {e}")
        
if __name__ == "__main__":
    create_bigquery_table()