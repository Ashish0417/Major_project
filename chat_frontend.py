from flask import Flask, request, jsonify, render_template_string
from llm_orchestrator import TravelItineraryOrchestrator

app = Flask(__name__)
orchestrator = TravelItineraryOrchestrator()

CHAT_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Travel Planner Chatbot</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f7fb; margin:0; padding:0; }
    .container { max-width: 800px; margin: 30px auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .messages { min-height: 330px; margin-bottom: 10px; border: 1px solid #ddd; padding: 12px; border-radius: 6px; background: #fff; overflow-y: auto; max-height: 500px; display: flex; flex-direction: column; }
    .bubble { margin: 10px 0; padding: 10px 12px; border-radius: 12px; display: inline-block; max-width: 80%; line-height: 1.4; }
    .user { background: #dbe8ff; align-self: flex-end; }
    .bot { background: #e8f7e4; align-self: flex-start; }
    .typing { font-style: italic; color: #999; }
    .row { display: flex; align-items: center; }
    .thumbs { margin-left: 10px; }
    .thumbs button { border: 1px solid #ccc; padding: 6px 10px; margin-right: 4px; border-radius: 4px; cursor: pointer; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Travel Planner Chatbot</h1>
    <div class="messages" id="messages"></div>

    <div class="row">
      <input id="queryInput" style="flex:1; padding: 8px; border: 1px solid #ccc; border-radius: 6px;" placeholder="Ask me to plan your trip..." />
      <button id="sendBtn" style="margin-left: 8px; padding: 8px 16px;">Send</button>
    </div>

    <div class="row thumbs" style="margin-top: 10px;">
      <span>Feedback:</span>
      <button id="thumbsUp" style="background-color: #c6f6d5;">👍</button>
      <button id="thumbsDown" style="background-color: #fed7d7;">👎</button>
    </div>

    <div id="status" style="margin-top: 12px; color: #666;"></div>
  </div>

<script>
  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('queryInput');
  const statusEl = document.getElementById('status');
  const userId = localStorage.getItem('rag_user_id') || 'default_user';
  localStorage.setItem('rag_user_id', userId);

  document.getElementById('sendBtn').addEventListener('click', sendMessage);
  inputEl.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

  document.getElementById('thumbsUp').addEventListener('click', () => sendFeedback(1));
  document.getElementById('thumbsDown').addEventListener('click', () => sendFeedback(0));

  let lastQuery = '';
  let lastResponse = '';
  let lastTripInfo = {};
  let typingBubble = null;

  function setTyping(on) {
    if (on && !typingBubble) {
      typingBubble = document.createElement('div');
      typingBubble.className = 'bubble bot typing';
      typingBubble.textContent = '✍️ Agent is thinking...';
      messagesEl.appendChild(typingBubble);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    } else if (!on && typingBubble) {
      typingBubble.remove();
      typingBubble = null;
    }
  }

  function addBubble(text, user) {
    const div = document.createElement('div');
    div.className = 'bubble ' + (user ? 'user' : 'bot');
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendMessage() {
    const query = inputEl.value.trim();
    if (!query) return;

    addBubble(query, true);
    lastQuery = query;
    inputEl.value = '';

    statusEl.textContent = 'Sending...';
    setTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, query })
      });

      const data = await res.json();
      setTyping(false);

      if (res.ok) {
        lastResponse = data.response || 'No response';
        // Try to extract trip info from response
        if (lastResponse.includes('Destination:')) {
          lastTripInfo = {
            has_itinerary: true,
            response_length: lastResponse.length
          };
        }
        addBubble(lastResponse, false);
        statusEl.textContent = '✅ Done. You can give thumbs feedback.';
      } else {
        addBubble(`Error: ${data.response || 'Unknown issue'}`, false);
        statusEl.textContent = '❌ Failed to generate itinerary';
      }
    } catch (error) {
      setTyping(false);
      addBubble('Error fetching response. Please check your backend.', false);
      statusEl.textContent = '❌ Network error';
    }
  }

  async function sendFeedback(rating) {
    if (!lastQuery) {
      statusEl.textContent = 'Send a query first.';
      return;
    }
    const comment = rating === 1 ? 'Great itinerary!' : 'Could be better';
    const feedbackData = {
      user_id: userId,
      query: lastQuery,
      response: lastResponse,
      rating: rating,
      comment: comment,
      trip_info: lastTripInfo
    };
    
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackData)
      });
      const data = await res.json();
      statusEl.textContent = data.status;
    } catch (error) {
      statusEl.textContent = '❌ Error sending feedback';
    }
  }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(CHAT_HTML)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json(force=True)
    user_id = data.get('user_id', 'default_user')
    query = data.get('query', '').strip()

    if not query:
        return jsonify({'response': 'Please enter a query.'}), 400

    response_text = orchestrator.ask(query, user_id=user_id)
    return jsonify({'response': response_text})

@app.route('/api/feedback', methods=['POST'])
def feedback_api():
    data = request.get_json(force=True)
    user_id = data.get('user_id', 'default_user')
    query = data.get('query', '')
    rating = int(data.get('rating', 0))
    comment = data.get('comment', '')
    response_text = data.get('response', '')
    trip_info = data.get('trip_info', {})

    if rating not in (0, 1):
        return jsonify({'status': 'Rating must be 0 or 1.'}), 400

    success = orchestrator.history_manager.store_feedback(
        user_id, 
        query, 
        rating, 
        comment,
        response_text=response_text,
        trip_info=trip_info
    )
    
    if success:
        emoji = '👍' if rating == 1 else '👎'
        return jsonify({'status': f'{emoji} Feedback saved. Thank you!'})
    else:
        return jsonify({'status': '❌ Error saving feedback'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
