from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
import os
import datetime
from collections import deque
import config

# Initialize Flask app
app = Flask(__name__)

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

OpenAI.api_key = config.OPENAI_API_KEY
client = OpenAI()

# Store messages in memory with a deque (limited size, works as a simple queue)
messages = {}  # Dictionary to store messages for each group

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
    group_id = event.source.group_id if event.source.type == "group" else user_id

    print(f"Handling message from user {user_id} in group {group_id}: {user_message}")

    # Store incoming messages in memory with timestamp
    if group_id not in messages:
        messages[group_id] = deque(maxlen=config.MAX_MESSAGES_PER_GROUP)
    messages[group_id].append({
        'user_id': user_id,
        'message': user_message,
        'timestamp': datetime.datetime.now()
    })

    # Check if the message contains the chat summary trigger keyword
    if config.CHAT_SUMMARY_TRIGGER in user_message.upper():
        summary = summarize_chat(group_id)
        if summary:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ขุนพระ! คุยไรกันเยอะแยะ! เดี๋ยวผมสรุปให้ฟังครับ 😂" + summary)
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
        msg['message'] for msg in messages.get(group_id, [])
        if (now - msg['timestamp']).total_seconds() < 86400
        and config.CHAT_SUMMARY_TRIGGER not in msg['message'].upper()
    ]

    if not last_24_hours_messages:
        return None

    # Call OpenAI API to summarize messages
    prompt = "ช่วยสรุป บทสนทนาเหล่านี้ เป็นข้อๆ (bullet points) ขอสั้นๆ กระชับๆ เอาเฉพาะๆ ที่สำคัญๆ ที่ตลกๆ สนุกๆ แล้วใส่ Emoji ไปบ้าง:\n" + "\n".join(last_24_hours_messages)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        output = response.choices[0].message.content.strip()
        print(f"OpenAI response: {output}")
        return output
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "ขุนพระช่วย! ตอนนี้ @ขุนพระ มีปัญหาอยู่ กรุณารอ @Por มาแก้นะจ้า"

# Run Flask app
if __name__ == "__main__":
    app.run(port=8080)
