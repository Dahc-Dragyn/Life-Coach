document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, initializing chat functionality');

    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const coachSelect = document.getElementById('coach-select');

    // Check if elements exist
    if (!messageInput) console.error("Element 'message-input' not found!");
    if (!sendButton) console.error("Element 'send-button' not found!");
    if (!chatMessages) console.error("Element 'chat-messages' not found!");
    if (!coachSelect) console.error("Element 'coach-select' not found!");

    if (!messageInput || !sendButton || !chatMessages || !coachSelect) {
        console.error('One or more critical elements missing, aborting script.');
        return;
    }

    // Load conversation history from localStorage
    let conversationHistory = JSON.parse(localStorage.getItem('conversationHistory')) || [];
    const maxHistoryLength = 5;

    // Function to add a message to the chat display
    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'You' ? 'user-message' : 'bot-message');

        const senderSpan = document.createElement('span');
        senderSpan.classList.add('sender');
        senderSpan.textContent = sender + ": ";

        const messageText = document.createElement('span');
        messageText.textContent = message;

        messageDiv.appendChild(senderSpan);
        messageDiv.appendChild(messageText);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Display conversation history on page load
    function displayConversationHistory() {
        chatMessages.innerHTML = '';
        conversationHistory.forEach(turn => {
            addMessage('You', turn.user);
            if (turn.bot) addMessage(turn.coachName, turn.bot); // Use coach name from history
        });
    }

    displayConversationHistory();

    // Function to send a message
    function sendMessage() {
        const message = messageInput.value.trim();
        const coachName = coachSelect.value;

        if (!message) return;

        console.log('Sending message:', message, 'to coach:', coachName);
        addMessage('You', message);
        messageInput.value = '';

        // Add user message to history
        conversationHistory.push({ user: message, coachName: coachName });
        if (conversationHistory.length > maxHistoryLength) {
            conversationHistory.shift();
        }

        fetch('/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                coach_name: coachName,
                history: conversationHistory
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Response not OK');
            return response.json();
        })
        .then(data => {
            if (data.error) {
                addMessage(coachName, `Error: ${data.error}`);
            } else {
                addMessage(coachName, data.answer);
                // Add bot response to history with coach name
                conversationHistory[conversationHistory.length - 1].bot = data.answer;
                localStorage.setItem('conversationHistory', JSON.stringify(conversationHistory));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage(coachName, 'An error occurred. Please try again.');
        });
    }

    // Event listeners
    sendButton.addEventListener('click', function() {
        console.log('Send button clicked');
        sendMessage();
    });

    messageInput.addEventListener('keydown', function(event) {
        console.log('Key pressed:', event.key);
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            console.log('Enter detected, sending message');
            sendMessage();
        }
    });
});