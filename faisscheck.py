# faiss_indexchecker.py

import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
import time

# --- Configuration (Should match faissmaker.py and rag_processor.py) ---
FAISS_DIR = "faiss_index"
INDEX_PATH = os.path.join(FAISS_DIR, "index.faiss")
PKL_PATH = os.path.join(FAISS_DIR, "index.pkl")
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2' # Model used to create the index

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def check_faiss_index():
    """
    Performs checks on the FAISS index and metadata pickle file.
    Returns True if all basic checks pass, False otherwise.
    """
    logging.info("--- Starting FAISS Index Checks ---")
    checks_passed = True
    faiss_index = None
    metadata = None
    model_dim = None

    # 1. Check File Existence
    logging.info(f"Checking existence of FAISS index: {INDEX_PATH}")
    if not os.path.exists(INDEX_PATH):
        logging.error(f"FAISS index file not found at {INDEX_PATH}")
        checks_passed = False
    else:
        logging.info("FAISS index file found.")

    logging.info(f"Checking existence of Metadata pickle: {PKL_PATH}")
    if not os.path.exists(PKL_PATH):
        logging.error(f"Metadata pickle file not found at {PKL_PATH}")
        checks_passed = False
    else:
        logging.info("Metadata pickle file found.")

    if not checks_passed:
        logging.error("One or both required files are missing. Cannot proceed.")
        return False # Stop if files are missing

    # 2. Load FAISS Index
    try:
        logging.info(f"Attempting to load FAISS index from {INDEX_PATH}...")
        start_time = time.time()
        faiss_index = faiss.read_index(INDEX_PATH)
        load_time = time.time() - start_time
        logging.info(f"FAISS index loaded successfully in {load_time:.2f}s.")
        logging.info(f"  - Index dimension (d): {faiss_index.d}")
        logging.info(f"  - Total vectors (ntotal): {faiss_index.ntotal}")
        if faiss_index.ntotal == 0:
            logging.warning("FAISS index loaded but contains 0 vectors.")
            checks_passed = False # Index is empty
    except Exception as e:
        logging.error(f"Failed to load FAISS index: {e}", exc_info=True)
        checks_passed = False
        faiss_index = None # Ensure it's None if loading failed

    # 3. Load Metadata Pickle
    try:
        logging.info(f"Attempting to load metadata from {PKL_PATH}...")
        start_time = time.time()
        with open(PKL_PATH, 'rb') as f:
            metadata = pickle.load(f)
        load_time = time.time() - start_time
        logging.info(f"Metadata pickle loaded successfully in {load_time:.2f}s.")
        logging.info(f"  - Metadata type: {type(metadata)}")
        # Check type immediately
        if not isinstance(metadata, (list, tuple)):
            logging.error(f"Metadata is not a list or tuple (type: {type(metadata)})! Retrieval will fail.")
            checks_passed = False
            metadata = None # Mark as invalid
        elif len(metadata) == 0:
             logging.warning("Metadata loaded but contains 0 items.")
             checks_passed = False # Metadata is empty
        else:
            logging.info(f"  - Number of metadata items: {len(metadata)}")
    except Exception as e:
        logging.error(f"Failed to load metadata pickle: {e}", exc_info=True)
        checks_passed = False
        metadata = None # Ensure it's None if loading failed

    # 4. Check Size Match (Only if both loaded successfully and are valid types)
    if faiss_index is not None and metadata is not None and isinstance(metadata, (list, tuple)):
        logging.info("Comparing FAISS index size and metadata length...")
        if faiss_index.ntotal == len(metadata):
            logging.info(f"SUCCESS: FAISS index size ({faiss_index.ntotal}) matches metadata length ({len(metadata)}).")
        else:
            logging.error(f"FAILURE: FAISS index size ({faiss_index.ntotal}) DOES NOT MATCH metadata length ({len(metadata)})!")
            checks_passed = False
    elif checks_passed: # Only log if no previous critical errors
         logging.warning("Skipping size match check due to previous loading errors.")


    # 5. Check Embedding Dimension (Optional but good)
    try:
        logging.info(f"Loading embedding model ({MODEL_NAME}) to check dimension...")
        model = SentenceTransformer(MODEL_NAME)
        model_dim = model.get_sentence_embedding_dimension()
        logging.info(f"Model embedding dimension: {model_dim}")
        if faiss_index is not None and faiss_index.d == model_dim:
            logging.info(f"SUCCESS: FAISS index dimension ({faiss_index.d}) matches model dimension ({model_dim}).")
        elif faiss_index is not None:
            logging.error(f"FAILURE: FAISS index dimension ({faiss_index.d}) DOES NOT MATCH model dimension ({model_dim})!")
            checks_passed = False
        elif checks_passed: # Only log if no previous critical errors
             logging.warning("Skipping dimension match check due to FAISS index loading error.")
        del model # Free up model memory
    except Exception as e:
        logging.error(f"Could not load embedding model to check dimension: {e}", exc_info=True)
        # Don't fail the check just because model couldn't load, but log it.
        logging.warning("Could not verify embedding dimension.")


    # 6. Perform Sample Search & Lookup (Optional but helpful)
    if checks_passed and faiss_index is not None and metadata is not None and model_dim is not None:
        logging.info("Performing sample search and metadata lookup...")
        try:
            sample_query = "test query for validation"
            # Reload model briefly if needed, or use dummy vector of correct dimension
            # Using dummy vector is faster if model was deleted
            dummy_vector = np.random.rand(1, model_dim).astype(np.float32)
            # sample_embedding = SentenceTransformer(MODEL_NAME).encode([sample_query]).astype(np.float32)

            k_sample = 1 # Just need one result
            distances, indices = faiss_index.search(dummy_vector, k_sample)
            logging.info(f"Sample search executed.")

            first_index = indices[0][0]
            if first_index == -1:
                logging.warning("Sample search returned index -1 (no results found for dummy vector). Cannot test lookup.")
                # This isn't necessarily a failure of the index itself, maybe dummy vector was bad match
            elif 0 <= first_index < len(metadata):
                logging.info(f"Sample search returned index: {first_index} (Valid range [0, {len(metadata)-1}])")
                try:
                    sample_text = metadata[first_index]
                    logging.info("SUCCESS: Successfully retrieved sample metadata text:")
                    logging.info(f"  Sample Text (Index {first_index}): '{str(sample_text)[:150]}...'") # Show snippet
                except Exception as lookup_e:
                    logging.error(f"FAILURE: Failed to lookup metadata at index {first_index}: {lookup_e}", exc_info=True)
                    checks_passed = False
            else:
                logging.error(f"FAILURE: Sample search returned index {first_index}, which is OUT OF BOUNDS for metadata (size {len(metadata)}).")
                checks_passed = False
        except Exception as search_e:
            logging.error(f"FAILURE: Error during sample search/lookup: {search_e}", exc_info=True)
            checks_passed = False
    elif checks_passed:
        logging.warning("Skipping sample search/lookup due to previous errors or missing components.")


    # --- Final Result ---
    logging.info("--- FAISS Index Checks Complete ---")
    if checks_passed:
        logging.info(">>> RESULT: All basic checks passed. Index and metadata appear consistent.")
    else:
        logging.error(">>> RESULT: One or more checks failed. Please review errors above.")

    return checks_passed

if __name__ == "__main__":
    if check_faiss_index():
        print("\nIndex check PASSED.")
    else:
        print("\nIndex check FAILED.")