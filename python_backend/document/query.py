import os
from typing import Dict, List, Optional, Any
import datetime

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.retrievers import VectorIndexRetriever, RouterRetriever
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
import time
import sys
sys.path.append('/Users/beckyxu/Documents/GitHub/sgd-insight-engine')

from python_backend.config import logger, POLICY_FOLDER, GCP_PROJECT_ID, GCP_LOCATION, DOCUMENTS_BUCKET
from python_backend.storage.bigquery import get_fa_from_bigquery
from python_backend.storage.gcs import ensure_bucket_exists
from python_backend.ai.models import llm, embed_model
from python_backend.document.processor import process_document_links, create_tempfile_path, docling_reader


def create_policy_docs(
    policy_links: List[str] = None, 
    ) -> Dict:
    """
    Initialize indices for policy documents using the existing ChromaDB collection.
    
    Args:
        policy_links: Optional list of policy document links (not used when loading from existing ChromaDB).
        folder_name: Folder in GCS for the vector indices.
        index_name: Base name for the vector indices.
        
    Returns:
        Dict mapping document descriptions to their indices.
    """
    # 1. create combinedtext for each document
    # file 1 SDG
    file_path = FILEPATHHERE
    docs = docling_reader.load_data(file_path)
    text_doc1_sdg = ' '.join(doc.text.strip() for doc in docs)
    
    # file 2 SDG
    file_path = FILEPATHHERE
    docs = docling_reader.load_data(file_path)
    text_doc2_sdg = ' '.join(doc.text.strip() for doc in docs)
    
    # file 3 RS
    file_path = FILEPATHHERE
    docs = docling_reader.load_data(file_path)
    text_doc1_rs = ' '.join(doc.text.strip() for doc in docs)
    
    # file 4 RS
    file_path = FILEPATHHERE
    docs = docling_reader.load_data(file_path)
    text_doc2_rs = ' '.join(doc.text.strip() for doc in docs)
    
    # file 5 RS
    file_path = FILEPATHHERE
    docs = docling_reader.load_data(file_path)
    text_doc3_rs = ' '.join(doc.text.strip() for doc in docs)
    
    return [text_doc1_sdg, text_doc2_sdg, text_doc1_rs, text_doc2_rs, text_doc3_rs] 

def answer_question_from_document_link(document_link: str) -> Dict[str, Any]:
    """
    Answer a question based on a document link and policy indices.
    First extracts information from policy documents, then uses that to analyze the project document.
    
    Args:
        document_link: The link to the project document to analyze.
                
    Returns:
        Dict containing the structured analysis and relevant context.
    """
    import json
    
    logger.info(f"Processing document link: {document_link}")
    
    # Step 1: load policy context docs
    try:
        policy_doc_list = create_policy_docs()
        logger.info(f"Initialized {len(policy_doc_list)} policy document")
    except Exception as e:
        logger.error(f"Error initializing policy docments: {str(e)}")
        return {}

    # Step 2: Download and analyze the project document 
    try:
        processed_doc = process_document(document_link) 
        project_doc_text = processed_doc['text_doc_fa'] 
    except Exception as e:
        logger.error(f"Error initializing project fa doc: {str(e)}")
        return {}
    
    # Step 3: Extract data from the project fa and the unops policy docs 
    try:
        system_prompt = """
            Use ReAct:
                1. **Reason**: Identify relevant project elements from project document.
                2. **Act**: Match to tool or indicators.
                3. **Reason**: Validate matches.
                4. **Act**: Format the response as JSON
                If information is missing or uncertain, include null values.
        """
        from python_backend.ai.models import llm
        
        # 1. Create a summary text 
        try:
            # Create prompt for the LLM
            prompt = f"""
            You are analyzing a project document financial document for Sustainable Development Goals (SDGs) impact and potential application of remote sensing.
            The project document contains two main sections in the report: <finance> and <project description>.
            Based on the document text below, please answer the following question:
            
            *Questions*:
            - What are the main objectives of the project? Focus on the <project description>.
            - What specific societal, economic, or environmental problems does it address? Focus on <project description>.
            - Who are the beneficiaries and who will be impacted? Focus on <project description>.
            - What are the anticipated short-term and long-term outcomes? Focus on <project description> and <finance>.
            
            *Here is the document text*:
            {project_doc_text}
            
            Create a written summary of the project based on the questions and the document text.
            """
            
            # Get response from LLM
            response = llm.complete(system_prompt + prompt)
            answer_summary = response.text.strip()
            
            # Store in summary
            print(answer_summary)
            logger.info(f"Generated summary for doc")
        except:
            logger.info(f"Fail to generate summary")
            answer_summary = None
            
        # 2. Create a sdg and sdg indicators json
        try:
            # Create prompt for the LLM
            prompt = f"""
            You are analyzing a project document financial document for Sustainable Development Goals (SDGs) and measurable SDG indicators.
            You are given two sets of documents: 1. project document, 2. sdg indicators documents.
            The project document contains two main sections in the report: <finance> and <project description>.
            Focusing on <project description> and the sdg indicators documents, analyze:
            - What SDG goals does this project contribute to?
            - What specific SDG indicators are measurable in this project?"
            - Output a nested json with keys: "sdg_goals" and "sdg_indicators". Each key can have a list of objects. Follow the format below.
            
            *Here is the project document*:
            {project_doc_text}
            
            *Here is the sdg indicators document*:
            {policy_doc_list[0]}
            {policy_doc_list[1]}

            *Strictly follow this nested json response format*
            {
                "sdg_goals": [
                    {
                        "sdg_goal": "string",  # e.g., "6"
                        "name": "string",     # e.g., "Clean Water and Sanitation"
                        "relevance": "string" # e.g., "Provides safe water"
                    }, ...]
                ,
                "sdg_indicators": [
                    {
                        "sdg_indicator": "string",    # e.g., "6.1.1"
                        "indicator_name": "string",  # e.g., "Proportion with safe water"
                        "unsd_indicator_codes": "string",  # e.g., "C060101"
                        "relevance": "string"        # e.g., "Measures household access"
                    }, ...]
            }
            
            Only output the json string.
            """
            # Get response from LLM
            response = llm.complete(system_prompt+prompt)
            answer_sdg = response.text.strip()
            
            # Store in summary
            print(answer_sdg)
            logger.info(f"Generated SDG for doc")
            
        except Exception as e:
            logger.error(f"system_prompt + Error generating summary doc")
            answer_sdg = None
            
        # 3. Create a imat and remote sensing capacity json
        try:
            # Create prompt for the LLM
            prompt = f"""
            You are analyzing a project document financial document for potential application of remote sensing.
            You are given two sets of documents: 1. project document, 2. remote sensing tools documents.
            The project document contains two main sections in the report: <finance> and <project description>.
            Focusing on <project description> from the  project document, and the remote sensing tool documents, analyze:
            - Which remote sensing or other IMAT tools applicable for this project?
            - How is this remote sensing or IMAT tool applicable for this project?
            - Output a nested json with keys: "remote_sensing_tools". Each key can have a list of objects. Follow the format below.

            *Here is the project document text*:
            {project_doc_text}
            
            *Here are the remote sensing tools documents*:
            {policy_doc_list[2]}
            {policy_doc_list[3]}
            {policy_doc_list[4]}
            
            *Strictly follow this nested json response format*
            {
                "remote_sensing_tools":[
                    {
                        "technology": "string",   # e.g., "Remote Sensing Tool A"
                        "application": "string"   # e.g., "Monitor water sources"
                    }
                ]
            }
            Only output the json string.
            """
            
            # Get response from LLM
            response = llm.complete(system_prompt+prompt)
            answer_rs = response.text.strip()
            
            # Store in summary
            print(answer_rs)
            logger.info(f"Generated remote sensing summary for doc")
            
        except Exception as e:
            logger.error(f"Error generating summary doc")
            answer_rs = None
        
        return {**answer_summary, **answer_sdg, **answer_rs}

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {"answer": f"Error processing document: {str(e)}", "source_links": [document_link]}

#     # Step 4: Answer questions

#             #     "question": "Is remote sensing or other IMAT tools applicable for this project, and how?",
#             #     "response_format": {
#             #         "remote_sensing": [
#             #             {
#             #                 "technology": "string",   # e.g., "Remote Sensing Tool A"
#             #                 "application": "string"   # e.g., "Monitor water sources"
#             #             }
#             #         ]
#             #     }
#             # }
#         ]
        
#         responses = {}
#         for item in questions:
#             question = item["question"]
#             response_format = json.dumps(item["response_format"], indent=2)
#             prompt = f"""
            
#             You are an expert analyst specializing in sustainable development and project evaluation. Based on a project summary, answer question with ReAct.
            
#             Project Summary:
#             {summary_text}

#             Question: {question}

#             Use ReAct:
#             1. **Reason**: Identify relevant project elements from summary and context.
#             2. **Act**: Match to policy data (SDGs, remote sensing capacities, IMAT tools), using project context for clarity.
#             3. **Reason**: Validate matches.
#             4. **Act**: Format the response as JSON with this schema:{response_format}
            
#             Do not include any text outside of this JSON structure. 
#             If information is missing or uncertain, include null values.
#             """
#             try:
#                 response = combined_engine.query(prompt)
#                 responses[question] = json.loads(str(response))
#             except Exception as e:
#                 logger.error(f"Error querying {question}: {str(e)}")
#                 responses[question] = {"error": str(e)}
            
#             # Step 5: Upload to BigQuery
#             # try:
#             #     rows = json_to_bigquery_rows(responses, document_link)
#             #     upload_to_bigquery(
#             #         rows,
#             #         project_id=bigquery_config.get("project_id"),
#             #         dataset_id=bigquery_config.get("dataset_id"),
#             #         table_id=bigquery_config.get("table_id")
#             #     )
#             # except Exception as e:
#             #     logger.error(f"Error transforming/uploading to BigQuery: {str(e)}")
                
#     except Exception as e:
#         logger.error(f"Error analyzing document: {str(e)}")
#         return {"answer": f"Error analyzing document: {str(e)}", "source_links": [document_link]}
        
#     # Clean up the tempfile path 
#     if temp_file_path and os.path.exists(temp_file_path):
#         try:
#             os.remove(temp_file_path)
#             logger.info(f"Removed temp file: {temp_file_path}")
#         except Exception as e:
#             logger.warning(f"Failed to remove temp file {temp_file_path}: {str(e)}")
    
#     print(responses)
#     return responses


# # TODO 
# #  processing a batch of documents all at once
# #  to be implemented when the llm pipeline is completed 
# # def process_document_batch_from_query_table(
# #     questions: List[str],
# #     query_table_data: List[Dict[str, str]],
# #     policy_indices_dict: Dict = None
# # ) -> List[Dict[str, Any]]:
# #     """
# #     Process multiple documents from a query table with file_URL, file_name, and file_code columns.
    
# #     Args:
# #         questions: List of questions to answer for each document.
# #         query_table_data: List of dictionaries with file_URL, file_name, and file_code.
# #         policy_indices_dict: Dictionary of policy indices.
        
# #     Returns:
# #         List of dictionaries with answers for each document and question.
# #     """
# #     results = []
    
# #     # Initialize policy indices once if not provided
# #     if policy_indices_dict is None:
# #         policy_indices_dict = initialize_policy_indices()
    
# #     for document in query_table_data:
# #         file_url = document.get('file_URL')
# #         file_name = document.get('file_name', 'Unknown')
# #         file_code = document.get('file_code', 'Unknown')
        
# #         if not file_url:
# #             logger.warning(f"Missing file_URL for document: {file_name}")
# #             continue
        
# #         document_results = {
# #             'file_name': file_name,
# #             'file_code': file_code,
# #             'file_URL': file_url,
# #             'results': []
# #         }
        
# #         for question in questions:
# #             logger.info(f"Processing question for document {file_name}: {question}")
            
# #             answer_result = answer_question_from_document_link(
# #                 question=question,
# #                 document_link=file_url,
# #                 policy_indices_dict=policy_indices_dict
# #             )
            
# #             document_results['results'].append({
# #                 'question': question,
# #                 'answer': answer_result.get('answer', ''),
# #                 'metadata': {
# #                     'project_context_length': len(answer_result.get('project_context', '')),
# #                     'policy_context_length': len(answer_result.get('policy_context', ''))
# #                 }
# #             })
        
# #         results.append(document_results)
    
# #     return results


if __name__ == "__main__":
    # //to delete after testing 
    # document_link = "https://drive.google.com/file/d/1BnxsDqskNB2Q4KLcZ7mAK-tZ6BGXaiEY"
    # answer_question_from_document_link(document_link)
    print('testing')