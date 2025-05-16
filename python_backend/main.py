"""
SDG Insight Engine - Sample Usage
"""

# Import the necessary modules
import sys
sys.path.append('/Users/beckyxu/Documents/GitHub/sgd-insight-engine')

from python_backend.document.processor import process_document_links
from python_backend.document.query import (
    initialize_policy_indices,
    answer_question_from_document_link,
)
from python_backend.config import logger
import json

from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from python_backend.document.processor import process_document_links, create_tempfile_path, docling_reader

def example_process_documents():
    """Process individual documents and create indices"""
    # Example document links
    file_links = [
        "https://drive.google.com/file/d/YOUR_FILE_ID",
        "https://storage.googleapis.com/your-bucket/your-file.pdf"
    ]
    
    # Process documents and create indices
    indices = process_document_links(file_links)
    logger.info(f"Created {len(indices)} document indices")
    
    return indices

def example_single_document_analysis(document_link):
    """Example of analyzing a single document using policy information"""
    
    # Generic question - the function will use specific queries internally
    question = "Analyze this project for SDG alignment"
    
    # Initialize policy indices - no need to pass policy links as it will use ChromaDB
    policy_indices = initialize_policy_indices()
    
    # Process the document
    result = answer_question_from_document_link(
        # question=question,
        document_link=document_link,
        policy_indices_dict=policy_indices
    )
    
    # Print result
    print(f"Analysis complete for document: {document_link}")
    
    # If structured data is available, print it nicely
    if "structured_data" in result:
        print("\nStructured Analysis:")
        print(json.dumps(result["structured_data"], indent=2))
        
        # Example of how you might use this for visualization
        print("\nVisualization Data:")
        # Count SDGs for a bar chart
        if "sdg_indicators" in result["structured_data"]:
            sdgs = [item["sdg"] for item in result["structured_data"]["sdg_indicators"]]
            print(f"SDGs identified: {len(sdgs)}")
            print(f"SDGs list: {sdgs}")
        
        # Check if remote sensing is applicable
        if "remote_sensing" in result["structured_data"]:
            rs_applicable = len(result["structured_data"]["remote_sensing"]) > 0
            print(f"Remote sensing applicable: {rs_applicable}")
            
            if rs_applicable:
                rs_tools = [item["technology"] for item in result["structured_data"]["remote_sensing"]]
                print(f"Recommended RS tools: {rs_tools}")
    else:
        print("\nWarning: No structured data available in the response")
        print(f"Raw answer: {result['answer']}")

def test_tempfile_download(document_link):
    temp_file_path = create_tempfile_path(document_link)
    if not temp_file_path:
        logger.error(f"Failed to download document from link: {document_link}")
        return {"answer": "Failed to download document.", "source_links": []}
    try:
        # Create index from the temp file
        logger.info(f"Creating index from temp file: {temp_file_path}")
        docs = docling_reader.load_data(temp_file_path)
        if not docs:
            logger.warning(f"No documents loaded from temp file: {temp_file_path}")
            return {"answer": "No content found in the document.", "source_links": []}
        
        # # Inspect the loaded documents
        # for i, doc in enumerate(docs):
        #     logger.info(f"Document {i+1} content preview: {doc.text[:200]}...")
        #     logger.info(f"Document {i+1} metadata: {doc.metadata}")
        
        # Create a temporary index from the document
        tempfile_index = VectorStoreIndex.from_documents(docs)
        test_query_engine = tempfile_index.as_query_engine()
        test_response = test_query_engine.query("what are the main goals of the project")
        print(f"Test tempfile_index creation by invoking response: {test_response}")

    except Exception as e:
        logger.error(f"Error creating tempfile_index: {str(e)}")
        return {"answer": f"Error creating tempfile_index: {str(e)}", "source_links": [document_link]}
              
if __name__ == "__main__":
    print("SDG Insight Engine - Sample Usage")
    
    # Example of analyzing a single document with the updated workflow
    document_link = "https://drive.google.com/file/d/1BnxsDqskNB2Q4KLcZ7mAK-tZ6BGXaiEY"
    # example_single_document_analysis(document_link)
    # test_tempfile_download(document_link)
    answer_question_from_document_link(document_link)


    # policy_indices_dict = initialize_policy_indices()
    # # print(policy_indices_dict)
    # try:
    #     # Create a query engine directly from policy index
    #     policy_retriever = None
    #     if policy_indices_dict and "policy_documents" in policy_indices_dict:
    #         # Get the policy index
    #         policy_index = policy_indices_dict["policy_documents"]
    #         # Create policy_index retriever
    #         policy_retriever = policy_index.as_retriever(similarity_top_k=5)
    #         logger.info(f"Created policy retriever")
    # except Exception as e:
    #     logger.error(f"Error extracting policy info as retriever: {str(e)}")
    #     policy_retriever = None
    
    