# rag_processor.py (Fixed for tuple metadata)

import faiss
import pickle
import os
import logging
from sentence_transformers import SentenceTransformer
import time # Optional: for timing loading

# --- Constants ---
FAISS_INDEX_DIR = "faiss_index"
FAISS_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "index.faiss")
PKL_PATH = os.path.join(FAISS_INDEX_DIR, "index.pkl")
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

# --- Global Variables ---
embedding_model = None
faiss_index = None
metadata = None

# --- Initialization Function ---
def load_rag_components():
    """
    Loads the Sentence Transformer embedding model, FAISS index, and
    associated metadata (from pickle file) into memory.

    Returns:
        bool: True if all components loaded successfully, False otherwise.
    """
    global embedding_model, faiss_index, metadata
    start_time = time.time()
    logging.info("Attempting to load RAG components...")

    if are_rag_components_loaded():
        logging.info("RAG components appear to be already loaded.")
        return True

    # 1. Load Embedding Model
    try:
        logging.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logging.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' loaded successfully.")
    except Exception as e:
        logging.error(f"CRITICAL: Failed to load embedding model '{EMBEDDING_MODEL_NAME}'. RAG will be disabled. Error: {e}", exc_info=True)
        embedding_model = None
        return False

    # 2. Load FAISS Index
    if not os.path.exists(FAISS_INDEX_PATH):
        logging.error(f"CRITICAL: FAISS index file not found at: {FAISS_INDEX_PATH}. RAG will be disabled.")
        return False
    try:
        logging.info(f"Loading FAISS index from: {FAISS_INDEX_PATH}...")
        faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        logging.info(f"FAISS index loaded successfully. Index contains {faiss_index.ntotal} vectors.")
    except Exception as e:
        logging.error(f"CRITICAL: Failed to load FAISS index from '{FAISS_INDEX_PATH}'. RAG will be disabled. Error: {e}", exc_info=True)
        faiss_index = None
        return False

    # 3. Load Metadata (Pickle file)
    if not os.path.exists(PKL_PATH):
        logging.error(f"CRITICAL: Metadata pickle file not found at: {PKL_PATH}. RAG will be disabled.")
        return False
    try:
        logging.info(f"Loading metadata from: {PKL_PATH}...")
        with open(PKL_PATH, 'rb') as f:
            metadata = pickle.load(f)

        # --- Validation updated to accept list or tuple ---
        if not isinstance(metadata, (list, tuple)): # Check for list OR tuple
             logging.error(f"CRITICAL: Metadata loaded from '{PKL_PATH}' is not a list or tuple (type: {type(metadata)}). Expected sequence mapping index to document. RAG may fail.")
             # You might still consider returning False if structure is completely wrong
        else:
             logging.info(f"Metadata loaded successfully. Found {len(metadata)} items (type: {type(metadata)}).")
             if len(metadata) != faiss_index.ntotal:
                 logging.warning(f"Metadata length ({len(metadata)}) does not match FAISS index size ({faiss_index.ntotal}). Check index/metadata consistency.")
        # --- End Validation ---

    except (pickle.UnpicklingError, EOFError, FileNotFoundError, Exception) as e:
        logging.error(f"CRITICAL: Failed to load or parse metadata from '{PKL_PATH}'. RAG will be disabled. Error: {e}", exc_info=True)
        metadata = None
        return False

    end_time = time.time()
    logging.info(f"All RAG components loaded successfully in {end_time - start_time:.2f} seconds.")
    # Return True even if metadata type caused an error log above, allows app to run without RAG
    # If metadata structure is critical, consider returning False on the type error inside the try block.
    return True # Indicate components *attempted* loading

# --- Search Function ---
def search_documents(query: str, k: int = 3) -> list[str]:
    """
    Embeds the query and performs similarity search against the FAISS index.

    Args:
        query (str): The user query text.
        k (int): The maximum number of documents to retrieve. Defaults to 3.

    Returns:
        list[str]: A list containing the text content of the retrieved documents.
                   Returns an empty list if RAG components are not loaded,
                   if the query is invalid, or if an error occurs during search.
    """
    if not are_rag_components_loaded():
        logging.warning("Search called but RAG components are not loaded. Returning empty list.")
        return []
    # Also specifically check if metadata loaded correctly, even if other components did
    if metadata is None:
         logging.error("Search called but metadata object is None. Cannot retrieve documents.")
         return []

    if not isinstance(query, str) or not query.strip():
        logging.warning("Search query is empty or invalid. Returning empty list.")
        return []

    logging.debug(f"Performing RAG search for query: '{query[:100]}...', k={k}")

    try:
        query_embedding = embedding_model.encode([query])
        distances, indices = faiss_index.search(query_embedding, k)
        retrieved_indices = indices[0]

        results = []
        # --- Ensure metadata is the list OR tuple we expect ---
        if isinstance(metadata, (list, tuple)): # <--- THE FIX IS HERE
            for idx in retrieved_indices:
                if idx != -1:
                    if 0 <= idx < len(metadata):
                        doc_content = metadata[idx]
                        if isinstance(doc_content, str):
                            results.append(doc_content)
                        # Add handling for other expected types if needed (e.g., dicts)
                        # elif isinstance(doc_content, dict) and 'content' in doc_content:
                        #     results.append(doc_content['content'])
                        else:
                            logging.warning(f"Retrieved metadata item at index {idx} is not a string (type: {type(doc_content)}). Skipping.")
                    else:
                        logging.warning(f"Retrieved index {idx} is out of bounds for metadata (size {len(metadata)}). Skipping.")
                else:
                    logging.debug("FAISS search returned -1 index; fewer than k results available.")
        # --- Updated Error Message ---
        else:
             logging.error(f"Cannot retrieve documents: metadata is not a list or tuple (type: {type(metadata)}).")
             return [] # Return empty list because we can't process metadata

        logging.info(f"RAG search found {len(results)} documents for query: '{query[:50]}...'")
        return results

    except Exception as e:
        logging.error(f"Error during RAG search for query '{query[:50]}...': {e}", exc_info=True)
        return []

# --- Helper to check loading status ---
def are_rag_components_loaded() -> bool:
    """ Checks if the embedding model, FAISS index, and metadata are loaded. """
    # Check if all are not None. Metadata check is crucial after loading attempt.
    loaded = all([embedding_model is not None, faiss_index is not None, metadata is not None])
    # Also check that metadata is the *correct type* (list or tuple) for retrieval to work
    type_ok = isinstance(metadata, (list, tuple))
    if not loaded:
        logging.debug("Checked RAG components: Not all components were loaded successfully (are None).")
    elif not type_ok:
         logging.warning(f"Checked RAG components: Metadata loaded but has unexpected type ({type(metadata)}), retrieval might fail.")

    return loaded and type_ok # RAG is only truly ready if loaded AND type is correct