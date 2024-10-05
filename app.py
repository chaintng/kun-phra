from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import datetime
from collections import deque

# Initialize Flask app
app = Flask(__name__)

# LINE API credentials
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Store messages in memory with a deque (limited size, works as a simple queue)
messages = deque()

# Health check endpoint
@app.route("/", methods=['GET'])
def health_check():
    return jsonify(status="OK"), 200

# Listen for incoming requests from LINE platform
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print(f"Received callback event: {body}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature error while handling callback")
        return "Invalid signature", 400
    return 'OK'

# Handle message events
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id
    group_id = event.source.sender_id if event.source.type == "group" else user_id

    print(f"Handling message from user {user_id} in group {group_id}: {user_message}")

    # Store incoming messages in memory with timestamp
    messages.append({
        'group_id': group_id,
        'user_id': user_id,
        'message': user_message,
        'timestamp': datetime.datetime.now()
    })

    # Check for "CHAT SUMMARY" trigger
    if user_message.upper() == "CHAT SUMMARY":
        summary = summarize_chat(group_id)
        if summary:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=summary)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="No messages in the last 24 hours to summarize.")
            )

# Function to summarize the messages of the last 24 hours
def summarize_chat(group_id):
    now = datetime.datetime.now()
    last_24_hours_messages = [
        msg['message'] for msg in messages
        if msg['group_id'] == group_id and (now - msg['timestamp']).total_seconds() < 86400
    ]

    if not last_24_hours_messages:
        return None

    # Call OpenAI API to summarize messages
    prompt = "Summarize the following conversation into bullet points:\n" + "\n".join(last_24_hours_messages)
    try:
        response = openai.ChatCompletion.create(
            engine="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        print(f"OpenAI response: {response.choices[0].text.strip()}")
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Failed to generate summary. Please try again later."

# Run Flask app
if __name__ == "__main__":
    app.run(port=8080)
