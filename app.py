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

    # Check if the message starts with the chat summary trigger keyword
    if user_message.upper().startswith(config.CHAT_SUMMARY_TRIGGER):
        custom_prompt = user_message[len(config.CHAT_SUMMARY_TRIGGER):].strip()
        summary = summarize_chat(group_id, custom_prompt)
        if summary:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ขุนพระ! คุยไรกันเยอะแยะ! เดี๋ยวผมสรุปให้ฟังครับ 😂\n" + summary)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="No messages in the last 24 hours to summarize.")
            )

# Function to summarize the messages of the last 24 hours
def summarize_chat(group_id, custom_prompt=None):
    now = datetime.datetime.now()
    last_24_hours_messages = [
        msg['message'] for msg in messages.get(group_id, [])
        if (now - msg['timestamp']).total_seconds() < 86400
        and config.CHAT_SUMMARY_TRIGGER not in msg['message'].upper()
        and not any(ignore_word.lower() in msg['message'].lower() for ignore_word in config.IGNORE_WORDS)
    ]

    if not last_24_hours_messages:
        return None

    # Call OpenAI API to summarize messages
    prompt = custom_prompt if custom_prompt else "สรุปบทสนทนาเป็นภาษาไทย โดยให้สั้น กระชับ และแสดงเฉพาะจุดสำคัญ (ใช้ Bullet Points) เลือกเฉพาะเนื้อหาที่สำคัญที่สุด ข้ามส่วนที่ไม่จำเป็นหรือเป็นมุกตลก และหากมีการพูดถึงการตัดสินใจ ให้แสดงเฉพาะการตัดสินใจขั้นสุดท้ายเท่านั้น เพิ่มอิโมจิไม่เกิน 5 ตัวในผลลัพธ์:\n"
    prompt += "\n".join(last_24_hours_messages)
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
