# app.py (with RAG integration)

from flask import Flask, render_template, request, jsonify, abort, url_for, session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# Removed dotenv import as load_dotenv() wasn't called
import os
import logging
import json
import time
import traceback
import requests
import uuid
import re

# --- RAG Processor Import ---
# Import the functions we need from our new module
import rag_processor

# --- Setup ---
# Configure logging (consider DEBUG for testing, INFO for production)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

# Load Flask secret key from environment
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    logging.critical("CRITICAL: FLASK_SECRET_KEY not found in environment! Sessions will not work securely. Set the variable.")
    # You might want to exit(1) here in production if sessions are essential
else:
    logging.info("Flask secret key loaded successfully from environment.")

# Load Google API Key
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GEMINI_API_KEY:
    logging.critical("CRITICAL: GOOGLE_API_KEY not set! Cannot connect to Gemini.")
    exit(1) # Exit if the API key is missing

# Set Gemini Model Name (using your preferred cheap model)
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-lite-001")
logging.info(f"Using Gemini model: {GEMINI_MODEL_NAME}")

# --- Constants ---
COACH_DATA_DIR = "coach_data"
if not os.path.isdir(COACH_DATA_DIR):
    logging.critical(f"CRITICAL: Coach data directory '{COACH_DATA_DIR}' not found! App cannot load personas.")
    # Consider exiting if coach data is essential
    # exit(1)

# For cache busting static assets
app.config['LAST_UPDATED'] = int(time.time())

# --- Load RAG Components at Startup ---
# Call the loading function from rag_processor.py
# This happens once when the Flask app starts.
RAG_ENABLED = rag_processor.load_rag_components()
if not RAG_ENABLED:
    logging.warning("RAG components failed to load. Application will run WITHOUT RAG functionality.")
else:
    logging.info("RAG components loaded successfully. RAG is ENABLED.")

# --- Helper Functions ---
# (get_dad_joke, create_gemini_chat_model, sanitize_input remain largely the same)
# Minor update to create_gemini_chat_model logging
def get_dad_joke():
    # ... (previous code is fine) ...
    url = "https://icanhazdadjoke.com/"
    headers = {'Accept': 'application/json'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json().get('joke', "No joke today, but you’re still awesome!")
    except requests.RequestException as e:
        logging.warning(f"Dad Joke API failed: {e}")
        return "No joke fetched – my bad!"

def create_gemini_chat_model():
    logging.debug("Creating Gemini chat model instance.")
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key=GEMINI_API_KEY,
        # Consider adding safety_settings if needed
        # safety_settings=...
    )

def sanitize_input(text):
    # ... (previous code is fine) ...
    if isinstance(text, str):
        return text.strip()
    return ""

# Updated manage_conversation_history to optionally exclude the *new* message
def manage_conversation_history(history_from_frontend, new_sanitized_message=None, max_exchanges=15):
    """
    Builds a list of LangChain messages from frontend history, applying filtering and trimming.
    Optionally adds the new user message at the end.
    """
    messages = []
    # Keep your denial phrases - they are useful!
    denial_phrases = [
        "i am a large language model", "i'm a large language model", "i am an ai",
        "i'm an ai assistant", "trained by google", "i cannot fulfill that request",
        "i do not have personal opinions", "as an ai", "language model",
        "i am not yoda", "i am not aiyoda", "i am not wellness warrior",
        "i am not career catalyst", "i am not executive coach",
        "i am not personal growth guru", "i am not relationship revivalist",
        "hypothetical scenario", "i don't have \"clients\"", "as i am a language model"
    ] # ... (keep your full list) ...

    logging.debug(f"Managing history. Input turns: {len(history_from_frontend)}, Max Exchanges: {max_exchanges}")

    # Process past turns from frontend
    for turn in history_from_frontend:
        user_msg_content = turn.get('user')
        bot_msg_content = turn.get('bot')

        if user_msg_content:
            sanitized_user_msg = sanitize_input(user_msg_content)
            if sanitized_user_msg:
                messages.append(HumanMessage(content=sanitized_user_msg))

        if bot_msg_content:
            if isinstance(bot_msg_content, str):
                is_denial = any(phrase in bot_msg_content.lower() for phrase in denial_phrases)
                if not is_denial:
                    messages.append(AIMessage(content=bot_msg_content))
                else:
                    logging.debug(f"History Filter: Skipping denial AIMessage: {bot_msg_content[:60]}...")
            else:
                logging.warning(f"Skipping non-string bot message in history: {bot_msg_content}")

    # Trim history if it's too long
    num_messages_to_keep = max_exchanges * 2
    if len(messages) > num_messages_to_keep:
        original_len = len(messages)
        messages = messages[-num_messages_to_keep:]
        logging.debug(f"History trimmed from {original_len} to {len(messages)} messages.")

    # Optionally add the *new* sanitized message (used for non-RAG or if RAG fails)
    if new_sanitized_message:
        messages.append(HumanMessage(content=new_sanitized_message))
        logging.debug("Added new user message to history list.")
    elif new_sanitized_message is not None: # Only log if it was deliberately empty
         logging.warning("New user message was empty after sanitization, not adding to history.")

    return messages


# load_coach_sidebar_data remains the same
def load_coach_sidebar_data():
    # ... (previous code is fine, ensure COACH_DATA_DIR is defined globally) ...
    coach_data_list = []
    try:
        if not os.path.isdir(COACH_DATA_DIR):
            logging.error(f"Coach data directory '{COACH_DATA_DIR}' not found during sidebar load!")
            return []

        for filename in sorted(os.listdir(COACH_DATA_DIR)):
            if filename.endswith(".json") and not filename.startswith('.'):
                base_name = filename[:-5]
                coach_display_name = base_name.replace("_", " ").title()
                coach_url_name = coach_display_name.lower().replace(" ", "")
                filepath = os.path.join(COACH_DATA_DIR, filename)
                try:
                    with open(filepath, "r", encoding='utf-8') as f:
                        persona_data = json.load(f)
                        image_filename = persona_data.get('image', 'default.jpg')
                        # ... (rest of the image checking logic is fine) ...
                        static_images_dir = os.path.join(app.static_folder, 'images')
                        image_path_check = os.path.join(static_images_dir, image_filename)
                        if not os.path.exists(image_path_check):
                            logging.warning(f"Image file not found: {image_path_check} for coach {coach_display_name}. Using default.jpg.")
                            image_filename = 'default.jpg'

                        coach_data_list.append({
                            'name': coach_display_name,
                            'url_name': coach_url_name,
                            'image': image_filename,
                            'image_url': url_for('static', filename=f'images/{image_filename}', v=app.config['LAST_UPDATED'])
                        })
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from {filename}: {e}")
                except Exception as e:
                    logging.error(f"Error processing coach file {filename}: {e}")
    except Exception as e:
        logging.error(f"Error listing coach data directory '{COACH_DATA_DIR}': {e}")
    return coach_data_list

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    coach_sidebar_list = load_coach_sidebar_data() # Load for GET and potential errors

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            logging.error("POST / - No JSON data received")
            return jsonify({'error': 'No data provided'}), 400

        message = data.get('message')
        coach_display_name = data.get('coach_name')
        history_from_frontend = data.get('history', [])

        # Basic input validation
        if not message or not coach_display_name:
            logging.warning(f"POST / - Missing fields: message={bool(message)}, coach_name={bool(coach_display_name)}")
            return jsonify({'error': 'Missing message or coach name'}), 400

        sanitized_message = sanitize_input(message)
        message_id = str(uuid.uuid4()) # Unique ID for this request
        logging.info(f"POST / - Request ID: {message_id} - Coach: '{coach_display_name}', Msg: '{sanitized_message[:50]}...'")

        # --- Coach Persona Loading ---
        coach_filename = f"{coach_display_name.lower().replace(' ', '_')}.json"
        coach_filepath = os.path.join(COACH_DATA_DIR, coach_filename)
        coach_persona = None
        try:
            with open(coach_filepath, "r", encoding='utf-8') as f:
                coach_persona = json.load(f)
            logging.debug(f"ID:{message_id} - Successfully loaded persona: {coach_filepath}")
            if "prompt_prefix" not in coach_persona or not coach_persona["prompt_prefix"]:
                 logging.error(f"ID:{message_id} - CRITICAL: 'prompt_prefix' missing or empty in {coach_filepath}")
                 return jsonify({'error': 'Internal server error: Coach configuration invalid.'}), 500
            # --- IMPORTANT REMINDER ---
            logging.info(f"ID:{message_id} - REMINDER: Ensure prompt_prefix in {coach_filename} instructs model to use provided 'Context:' if available.")
            # --- END REMINDER ---
        except FileNotFoundError:
            logging.error(f"ID:{message_id} - Coach data file not found: {coach_filepath}")
            return jsonify({'error': f'Coach configuration for "{coach_display_name}" not found.'}), 400
        except json.JSONDecodeError as e:
            logging.error(f"ID:{message_id} - Error decoding JSON from {coach_filepath}: {e}")
            return jsonify({'error': 'Error loading coach configuration.'}), 500
        except Exception as e:
            logging.error(f"ID:{message_id} - Unexpected error loading coach data from {coach_filepath}: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error loading coach data.'}), 500

        # --- Dad Joke Trigger ---
        joke_triggers = ["joke", "dad joke", "make me laugh", "something funny", "cheer me up"]
        if any(trigger in sanitized_message.lower() for trigger in joke_triggers):
            dad_joke = get_dad_joke()
            answer = f"Okay, you asked for it! Here’s a dad joke: {dad_joke}"
            logging.info(f"ID:{message_id} - Dad joke triggered. Response: '{answer[:100]}...'")
            return jsonify({'answer': answer, 'message_id': message_id})

        # --- RAG Processing ---
        retrieved_context_str = ""
        rag_search_performed = False
        if RAG_ENABLED: # Check if components loaded successfully at startup
            try:
                logging.debug(f"ID:{message_id} - Performing RAG search...")
                retrieved_docs = rag_processor.search_documents(sanitized_message, k=3) # Get top 3 docs
                rag_search_performed = True
                if retrieved_docs:
                    # Format the retrieved documents into a string block
                    context_parts = ["Context related to your query:"]
                    for i, doc in enumerate(retrieved_docs, 1):
                        context_parts.append(f"[{i}] {doc}") # Add numbering
                    retrieved_context_str = "\n".join(context_parts)
                    logging.debug(f"ID:{message_id} - RAG search found {len(retrieved_docs)} documents. Context snippet: {retrieved_context_str[:150]}...")
                else:
                    logging.debug(f"ID:{message_id} - RAG search completed but found 0 relevant documents.")
            except Exception as e:
                 logging.error(f"ID:{message_id} - Error during RAG search execution: {e}", exc_info=True)
                 # Proceed without context if RAG search fails
        else:
            logging.warning(f"ID:{message_id} - RAG is disabled or failed to load. Skipping vector search.")

        # --- Conversation History Management ---
        # Manage history BEFORE constructing the final prompt message
        previous_coach = session.get('current_coach')
        history_for_processing = []
        if previous_coach and coach_display_name == previous_coach:
            history_for_processing = history_from_frontend
            logging.debug(f"ID:{message_id} - Same coach. Using frontend history (len: {len(history_for_processing)}).")
        else:
            logging.info(f"ID:{message_id} - Coach changed from '{previous_coach}' to '{coach_display_name}' or first message. Clearing history for model.")
        session['current_coach'] = coach_display_name # Update session

        # Get the list of past HumanMessage/AIMessage pairs
        # Pass `None` for new_sanitized_message as we'll build the final prompt separately
        past_conversation_messages = manage_conversation_history(history_for_processing, None)

        # --- Prepare messages for Gemini ---
        try:
            chat_model = create_gemini_chat_model()

            # 1. System Message (Persona)
            system_prompt_content = coach_persona["prompt_prefix"]
            system_message_obj = SystemMessage(content=system_prompt_content)
            logging.debug(f"ID:{message_id} - SystemMessage: '{system_prompt_content[:150]}...'")

            # 2. Construct the Final Human Message (incorporating context if available)
            final_prompt_parts = []
            if retrieved_context_str:
                # Add context clearly labelled
                final_prompt_parts.append("--- Start of Provided Context ---")
                final_prompt_parts.append(retrieved_context_str)
                final_prompt_parts.append("--- End of Provided Context ---")
                final_prompt_parts.append("\nBased on the context above and our previous conversation, answer the following query:")

            # Always include the user's latest query
            final_prompt_parts.append(f"User Query: {sanitized_message}")

            final_human_content = "\n".join(final_prompt_parts)
            final_human_message = HumanMessage(content=final_human_content)
            logging.debug(f"ID:{message_id} - Final HumanMessage content: '{final_human_content[:200]}...'")

            # 3. Combine all messages: System + Past History + Final Human message with Context/Query
            messages_to_send = [system_message_obj] + past_conversation_messages + [final_human_message]
            logging.debug(f"ID:{message_id} - Total messages being sent to Gemini: {len(messages_to_send)}")
            # Optional: Log full message list structure if needed for deep debugging
            # logging.debug(f"ID:{message_id} - Messages structure: {[type(m).__name__ for m in messages_to_send]}")

            # --- Invoke Gemini ---
            logging.debug(f"ID:{message_id} - Invoking Gemini model...")
            response = chat_model.invoke(messages_to_send)
            answer = response.content

            # Response processing
            if not isinstance(answer, str):
                logging.warning(f"ID:{message_id} - Gemini response content was not a string ({type(answer)}). Converting.")
                answer = str(answer)
            answer = answer.strip()
            answer = re.sub(r'[\*]+', '', answer).strip() # Remove markdown emphasis

            logging.info(f"ID:{message_id} - Gemini Call Successful. Answer: '{answer[:100]}...'")
            return jsonify({'answer': answer, 'message_id': message_id})

        except Exception as e:
            error_id = message_id # Use the unique ID for error reference
            # Add specific context about where the error occurred
            step = "RAG search" if rag_search_performed else "Gemini API call or processing"
            logging.error(f"ID:{error_id} - Error during {step}: {e}", exc_info=True)
            # Attach error ID to the exception object for the 500 handler
            setattr(e, 'error_id', error_id)
            # Re-raise the exception to be caught by the generic 500 handler
            raise e

    # Handle GET request
    return render_template('index.html', coaches=coach_sidebar_list)


# --- Other Routes and Error Handlers ---

# /coach/<coach_url_name> remains the same
@app.route('/coach/<coach_url_name>')
def coach_page(coach_url_name):
    # ... (previous code is fine) ...
    coach_template_mapping = {
        'aiyoda': 'aiyoda',
        'wellnesswarrior': 'wellwar',
        'careercatalyst': 'carcat',
        'executivecoach': 'execu',
        'personalgrowthguru': 'pg',
        'relationshiprevivalist': 'rr'
    }
    template_name_base = coach_template_mapping.get(coach_url_name.lower())

    if template_name_base:
        template_filename = f'{template_name_base}.html'
        template_filepath = os.path.join(app.template_folder, template_filename)

        if os.path.exists(template_filepath):
            coach_sidebar_list = load_coach_sidebar_data()
            current_coach_details = next((c for c in coach_sidebar_list if c['url_name'] == coach_url_name), None)
            # Make RAG status available to templates if needed (optional)
            # return render_template(template_filename, coaches=coach_sidebar_list, current_coach=current_coach_details, rag_enabled=RAG_ENABLED)
            return render_template(template_filename, coaches=coach_sidebar_list, current_coach=current_coach_details)

        else:
            logging.error(f"Template file not found: {template_filepath} for coach URL {coach_url_name}")
            abort(404, description=f"Coach page template '{template_filename}' not found.")
    else:
        logging.warning(f"No template mapping found for coach URL name: {coach_url_name}")
        abort(404, description=f"Coach '{coach_url_name}' not recognized.")

# /feedback remains the same
@app.route('/feedback', methods=['POST'])
def feedback():
     # ... (previous code is fine) ...
    data = request.get_json()
    if not data or 'message_id' not in data or 'rating' not in data:
        return jsonify({'error': 'Invalid feedback data'}), 400
    logging.info(f"Feedback Received: Message ID {data['message_id']}, Rating: {data['rating']}, Comment: {data.get('comment', 'N/A')}")
    # Consider storing feedback persistently here
    return jsonify({'status': 'success', 'message': 'Feedback received. Thank you!'})


# Error Handlers remain mostly the same, ensure they get sidebar data
@app.errorhandler(404)
def page_not_found(e):
    # ... (previous code is fine) ...
    logging.warning(f"404 Not Found: {request.path} - {getattr(e, 'description', 'No description')}")
    coach_sidebar_list = load_coach_sidebar_data()
    return render_template('error.html', error_message=getattr(e, 'description', "Page not found."), coaches=coach_sidebar_list), 404

@app.errorhandler(500)
@app.errorhandler(Exception) # Catch other exceptions too
def internal_server_error(e):
    # Get the error ID if we attached it earlier (from the POST handler)
    error_ref = getattr(e, 'error_id', 'N/A')
    # Log the underlying error and traceback
    logging.error(f"500 Internal Server Error: {request.path} - Ref: {error_ref} - Error: {e}", exc_info=True)
    coach_sidebar_list = load_coach_sidebar_data()
    # Provide a user-friendly message with the reference ID
    user_message = f"An unexpected internal error occurred (Ref: {error_ref}). Please try again later or contact support if the issue persists."
    return render_template('error.html', error_message=user_message, coaches=coach_sidebar_list), 500

# --- Main Execution Guard ---
# Recommended practice for Flask apps
if __name__ == '__main__':
    # Use Flask's development server for local testing
    # Host 0.0.0.0 makes it accessible on your network / from Codespaces port forwarding
    # Debug=True enables auto-reloading and more detailed errors (use False in production)
    # Port 8080 matches your Gunicorn/Dockerfile config
    app.run(host='0.0.0.0', port=8080, debug=True)
    # When deploying with Gunicorn, Gunicorn runs the app, so this __main__ block isn't executed then.