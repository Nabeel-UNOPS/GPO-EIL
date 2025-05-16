from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from python_backend.config import logger, GCP_PROJECT_ID, BQ_MIT_DATASET, BQ_MIT_TABLE
from python_backend.storage.bigquery import get_bigquery_client

app = FastAPI(title="UNOPS Remote Sensing API")

# Add CORS middleware to allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = get_bigquery_client()

def fetch_projects_from_bigquery() -> List[Dict[str, Any]]:
    """
    Fetch project data from BigQuery and format for frontend.
    
    Returns:
        List of project dictionaries formatted for the frontend
    """
    try:
        if not client:
            logger.error("BigQuery client not initialized")
            return []
        
        table_id = f"{GCP_PROJECT_ID}.{BQ_MIT_DATASET}.final_results_engagement"
        query = f"SELECT * FROM `{table_id}`"
        
        query_job = client.query(query)
        results = query_job.result()
        
        projects = []
        for row in results:
            # Convert row to dict
            project = dict(row.items())
            
            # Handle nested/repeated fields
            for key in [
                "quantifiable_outcome_list",
                "sdg_goals",
                "sdg_indicators",
                "remote_sensing_tools"
            ]:
                if key in project and project[key] is not None:
                    project[key] = [dict(item) for item in project[key]]
            
            # Transform to match frontend expectations
            transformed_project = transform_project_for_frontend(project)
            projects.append(transformed_project)
        
        logger.info(f"Retrieved {len(projects)} projects from BigQuery")
        return projects
    
    except Exception as e:
        logger.error(f"Error fetching projects from BigQuery: {str(e)}")
        return []

def transform_project_for_frontend(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a BigQuery project row to match the frontend expected format.
    
    Args:
        project: Raw project data from BigQuery
        
    Returns:
        Transformed project data ready for frontend
    """
    # Map remote_sensing_tools to relevantTools format
    relevant_tools = []
    if project.get("remote_sensing_tools"):
        for tool in project["remote_sensing_tools"]:
            if tool.get("technology"):
                relevant_tools.append({
                    "name": tool.get("technology", ""),
                    "rationale": tool.get("relevance_justification", ""),
                    "project_description_context": tool.get("project_description_context", "")
                })
    
    # Create a transformed project object that matches frontend expectations
    transformed = {
        # Core project identifiers
        "id": project.get("file_id", ""),
        "name": project.get("Engagement_Description", ""),
        
        # Legal and administrative details
        "legal_agreement": project.get("Legal_Agreement", ""),
        "file_url": project.get("File_URL", ""),
        "region": project.get("Region", "Unknown"),
        "hub": project.get("Hub", ""),
        "donor": project.get("Donor_Description", ""),
        
        # Project management contacts
        "projectManager": project.get("Project_Manager_Name", "Unknown"),
        "projectManagerEmail": project.get("Project_Manager_Email_Address", "unknown@example.com"),
        "deputyProjectManager": project.get("Deputy_Project_Manager_Name", ""),
        "deputyProjectManagerEmail": project.get("Deputy_Project_Manager_Email_Address", ""),        
        
        # Project details generated from LLM
        "summary": project.get("project_summary", ""),
        "objectives": project.get("objectives", ""),
        "problems_addressed": project.get("problems_addressed", ""),
        "beneficiaries": project.get("beneficiaries_and_impacted_groups", ""),
        "anticipated_outcomes": project.get("anticipated_outcomes_short_and_long_term", ""),
        
        # SDG information -> need to fix this 
        "sdg_goals": project.get("sdg_goals", []),
        "sdg_indicators": project.get("sdg_indicators", []),
        
        # Tools and outcomes
        "relevantTools": relevant_tools,
        "quantifiable_outcomes": [
            item.get("outcome_item", "") 
            for item in project.get("quantifiable_outcome_list", []) 
            if item.get("outcome_item")
        ],
        "quantifiable_outcome_list": project.get("quantifiable_outcome_list", []),
        "remote_sensing_tools": project.get("remote_sensing_tools", [])
    }
    
    return transformed

@app.get("/api/projects", response_model=List[Dict[str, Any]])
async def get_projects():
    """
    Get all projects from BigQuery.
    
    Returns:
        List of projects formatted for the frontend
    """
    projects = fetch_projects_from_bigquery()
    if not projects:
        logger.warning("No projects found or error occurred")
    return projects

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
