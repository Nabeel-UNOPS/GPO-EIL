import json
import sys
import os

# Add the project root to the Python path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from python_backend.api.projects_api import fetch_projects_from_bigquery

def test_fetch_projects():
    """Test the fetch_projects_from_bigquery function and print the results."""
    print("Fetching projects from BigQuery...")
    
    try:
        # Fetch projects
        projects = fetch_projects_from_bigquery()
        
        # Print the number of projects found
        print(f"Found {len(projects)} projects")
        
        if projects:
            # Print the first project with nice formatting
            print("\nFirst project details:")
            first_project = projects[0]
            print(json.dumps(first_project, indent=2, default=str))
            
            # Check for specific fields
            print("\nChecking important fields:")
            print(f"- id: {first_project.get('id', 'MISSING')}")
            print(f"- name: {first_project.get('name', 'MISSING')}")
            print(f"- sdg: {first_project.get('sdg', 'MISSING')}")
            print(f"- sdgNumber: {first_project.get('sdgNumber', 'MISSING')}")
            
            # Check for nested fields
            print("\nRelevant tools:")
            for i, tool in enumerate(first_project.get('relevantTools', [])):
                print(f"  Tool {i+1}:")
                print(f"  - name: {tool.get('name', 'MISSING')}")
                print(f"  - rationale: {tool.get('rationale', 'MISSING')[:50]}...")
                print(f"  - project_description_context: {(tool.get('project_description_context', 'MISSING') or 'EMPTY')[:50]}...")
            
            # Check for other nested fields
            print("\nSDG Goals:")
            for i, goal in enumerate(first_project.get('sdg_goals', [])):
                print(f"  Goal {i+1}: {goal.get('sdg_goal', 'MISSING')} - {goal.get('name', 'MISSING')}")
            
            # Print all keys to verify structure
            print("\nAll keys in project object:")
            print(sorted(first_project.keys()))
        else:
            print("No projects found!")
    
    except Exception as e:
        print(f"Error testing API: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch_projects()
