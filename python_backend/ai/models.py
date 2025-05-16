"""
AI Models Module

This module provides centralized configuration for LLM and embedding models.
"""

from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

from python_backend.config import GCP_PROJECT_ID, GCP_LOCATION, logger
from google.generativeai import types

# Vertex AI configuration
vertexai_config = {
    "project": GCP_PROJECT_ID,
    "location": GCP_LOCATION,
}

# # LLM model
# config = types.GenerationConfig(
#     temperature=0,
#     # top_p=0.95,
#     stop_sequences=None
# )

llm = GoogleGenAI(
    model="gemini-2.0-flash",
    vertexai_config=vertexai_config,
    context_window=200000,  # max input tokens for the model
    max_tokens=2000,
    # generation_config=config
)


# Embedding model
embed_model = GoogleGenAIEmbedding(
    model_name="text-embedding-005",  # Using 005 since it's the latest model
    # For multilingual text, use: "text-multilingual-embedding-002"
    embed_batch_size=10,
    vertexai_config=vertexai_config
)

# Set the embedding dimension for reference
# EMBED_DIMENSION = 768  # text-embedding-005 has 768 dimensions

# Text splitter for chunking documents
text_splitter = SentenceSplitter(chunk_size=400, chunk_overlap=40)  # Smaller chunks

# Set global settings for LlamaIndex
def initialize_llama_settings():
    """Initialize global LlamaIndex settings with our models"""
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.text_splitter = text_splitter
    # logger.info("LlamaIndex settings initialized with Google AI models")

# Call this at import time to ensure settings are initialized
initialize_llama_settings()
