# Life-Coach: Your Personalized AI Companion 🚀
Welcome to **Life-Coach**, an interactive web application designed to provide personalized guidance and support in various aspects of life. Leveraging the power of Google's Gemini language model and Retrieval-Augmented Generation (RAG), Life-Coach offers engaging conversations tailored to different coaching personas.

## What is Life-Coach? 🤔

Life-Coach is a Flask-based web application that acts as a versatile AI companion agent. You can interact with different "coaches," each embodying a unique personality and area of expertise. Whether you're seeking wisdom from "AI Yoda," motivation from the "Wellness Warrior," or career advice from the "Career Catalyst," Life-Coach aims to provide helpful and insightful responses.

**Key Features:**

* **Diverse Coaching Personas:** Engage with a variety of AI coaches, each defined by a specific prompt prefix that shapes their responses. These personas are loaded from JSON files in the `coach_data` directory, making it easy to add and customize new coaching styles.
* **Retrieval-Augmented Generation (RAG):** For more informed and context-aware conversations, Life-Coach integrates a RAG system (powered by the `rag_processor` module). This allows the AI to search through relevant documents and incorporate that information into its responses, providing more grounded and helpful advice.
* **Google Gemini Integration:** The core of Life-Coach is powered by Google's state-of-the-art Gemini language model (`gemini-2.0-flash-lite-001` for cost-efficiency, as per your configuration!). This ensures high-quality, natural-sounding conversations.
* **Conversation History Management:** The application intelligently manages your conversation history with each coach, allowing for more coherent and contextually relevant interactions. It also filters out generic AI disclaimers to keep the focus on the coaching persona.
* **Simple and Intuitive Interface:** The Flask web framework provides a straightforward and user-friendly interface for interacting with the AI coaches.
* **Dad Joke Interludes:** Need a quick laugh? Just ask for a joke! The application includes a function to fetch a delightful (or groan-worthy) dad joke.
* **Feedback Mechanism:** You can provide feedback on the AI's responses, helping to improve the system over time.
* **Robust Error Handling and Logging:** The application includes comprehensive logging and error handling to ensure stability and provide insights into its operation.

## Why is Life-Coach Cool? 😎

Life-Coach isn't just another chatbot; it's a dynamic platform for personalized AI interaction. Here's what makes it stand out:

* **Personalized Experiences:** The coaching personas offer tailored interactions, making the AI feel more like a specialized guide than a generic assistant.
* **Enhanced Knowledge with RAG:** By integrating RAG, Life-Coach can go beyond its internal knowledge and provide answers grounded in external information, making the advice more relevant and comprehensive. This turns the AI from a conversationalist into a research-backed advisor.
* **Practical Application of LLMs:** This project demonstrates a real-world application of Large Language Models (LLMs) in providing helpful and engaging user experiences. It showcases how LLMs can be used for more than just answering questions, but for creating interactive and supportive tools.
* **Extensibility and Customization:** The modular design, with coach personas defined in JSON files and a separate `rag_processor` module, makes it easy to extend the application with new coaches, knowledge sources, and functionalities.
* **Cost-Effective Design:** By utilizing the `gemini-2.0-flash-lite-001` model, the application prioritizes efficiency without sacrificing the quality of interactions.
* **Learning Opportunity:** This project serves as an excellent example of how to integrate a powerful LLM with a web framework and external knowledge retrieval, providing valuable insights into the world of Generative AI and LLM applications.

## How it Works ⚙️

1.  **User Interaction:** You interact with Life-Coach through a web interface, selecting a coach and typing your message.
2.  **Request Handling:** The Flask application (`app.py`) receives your message and the selected coach's name.
3.  **Persona Loading:** The application loads the prompt prefix associated with the chosen coach from a JSON file. This prefix sets the tone and focus of the AI's responses.
4.  **RAG Processing (Optional):** If RAG is enabled and relevant, the `rag_processor.py` module searches for documents related to your query. The retrieved information is then formatted and included as context for the Gemini model.
5.  **Conversation History Management:** The application retrieves the past conversation history with the current coach to maintain context.
6.  **Gemini Interaction:** The prompt, consisting of the coach's prefix, the conversation history, and your current message (along with any retrieved context), is sent to the Google Gemini API.
7.  **Response Generation:** Gemini processes the input and generates a response based on the persona and available information.
8.  **Output Display:** The generated response is sent back to the web interface and displayed to you.

## Code Structure 📂

* `app.py`: The main Flask application file. It handles routing, request processing, Gemini API calls, and conversation management.
* `rag_processor.py`: (If present) Contains the logic for the Retrieval-Augmented Generation (RAG) system, including document loading, indexing, and searching.
* `coach_data/`: A directory containing JSON files that define the different coaching personas and their prompt prefixes.
* `templates/`: Contains the HTML templates for the web interface.
* `static/`: Contains static files like CSS, JavaScript, and images (including coach profile pictures).
* `.gitignore`: Specifies intentionally untracked files that Git should ignore.
* `requirements.txt`: Lists the Python dependencies required to run the application.
* (Potentially other files depending on the full project structure)

## Getting Started 🚀

To run Life-Coach locally (assuming you have Python and pip installed):

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Dahc-Dragyn/Life-Coach.git](https://github.com/Dahc-Dragyn/Life-Coach.git)
    cd Life-Coach
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up environment variables:**
    * You'll need a Google Cloud Project with the Gemini API enabled and an API key. Set this as an environment variable:
        ```bash
        export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
        ```
    * It's also recommended to set a secret key for Flask sessions:
        ```bash
        export FLASK_SECRET_KEY="your_secret_random_key"
        ```
    * Optionally, you can set the Gemini model name (it defaults to `gemini-2.0-flash-lite-001`):
        ```bash
        export GEMINI_MODEL_NAME="gemini-pro" # Or another available Gemini model
        ```
4.  **Ensure Coach Data:** Make sure the `coach_data` directory exists and contains JSON files defining your coaching personas.
5.  **Run the Flask application:**
    ```bash
    python app.py
    ```
6.  **Open your browser:** Navigate to `http://127.0.0.1:8080/` to start interacting with Life-Coach. (Note: In GitHub Codespaces, the port will be automatically forwarded, and you'll see the accessible URL).

## Future Upgrades and Ideas 💡

Life-Coach is a continuously evolving project. Here are some potential future upgrades and ideas we're considering:

* **Enhanced RAG Capabilities:**
    * **More Diverse Data Sources:** Integrate with various data sources beyond local files (e.g., web scraping, APIs, databases) to provide a wider range of context.
    * **Improved Document Processing:** Implement more sophisticated techniques for document chunking, embedding generation, and indexing for better retrieval accuracy.
    * **User-Specific Knowledge Bases:** Allow users to upload their own documents to create personalized knowledge bases for even more tailored coaching.
    * **Contextual Relevance Scoring:** Fine-tune the RAG system to better understand the nuances of user queries and prioritize the most relevant context.

* **Advanced Coaching Features:**
    * **Goal Setting and Tracking:** Enable users to set goals and receive ongoing support and motivation to achieve them.
    * **Action Planning:** Help users break down complex goals into actionable steps and provide guidance on implementation.
    * **Mood Tracking and Analysis:** Integrate features to track user mood and tailor coaching responses accordingly.
    * **Personalized Learning Paths:** Based on user interactions and goals, suggest relevant resources, articles, or exercises.
    * **Multi-Turn Reasoning:** Improve the AI's ability to understand and respond to more complex, multi-part conversations.

* **User Interface and Experience Enhancements:**
    * **Improved Styling and Responsiveness:** Enhance the visual design and ensure the application works seamlessly on different devices.
    * **User Accounts and Saved Conversations:** Allow users to create accounts and save their conversation history with different coaches.
    * **Visualizations and Progress Tracking:** Display user progress towards goals and provide visual insights.
    * **Voice Input and Output:** Enable voice-based interaction for a more natural conversational experience.

* **Coach Persona Expansion:**
    * **More Specialized Coaches:** Develop new coaching personas with expertise in niche areas (e.g., specific skills, hobbies, or life challenges).
    * **Dynamic Persona Adjustment:** Explore the possibility of the AI adapting its persona based on the user's needs and the flow of the conversation.
    * **Community-Contributed Personas:** Allow users to create and share their own coaching persona definitions (with moderation).

* **Technical Improvements:**
    * **Asynchronous Operations:** Implement asynchronous tasks for potentially long-running operations (like RAG searches) to improve responsiveness.
    * **More Comprehensive Testing:** Expand the unit and integration tests to ensure the application's stability and reliability.
    * **Performance Optimization:** Continuously profile and optimize the code for better performance and resource utilization.

These are just some initial ideas, and the future direction of Life-Coach will be shaped by user feedback and ongoing development efforts. Stay tuned for exciting updates!

## Contributing 🤝

Contributions to Life-Coach are welcome! If you have ideas for new coaching personas, improvements to the RAG system, or enhancements to the user interface, feel free to submit a pull request.

## License 📜

[Add your license information here, e.g., MIT License]

## Acknowledgements 🙏

* [Mention any libraries or resources you found particularly helpful, e.g., The Flask team, The LangChain community, Google AI for the Gemini API]

Enjoy your journey with Life-Coach! Let the personalized guidance begin. ✨