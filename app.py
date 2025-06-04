from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent
from openai import OpenAI
import os
import datetime
from collections import deque
import config

# Initialize Flask app
app = Flask(__name__)

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

client = OpenAI(api_key=config.OPENAI_API_KEY)

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

def should_use_custom_prompt(user_message, group_id):
    return user_message.upper() != config.CHAT_SUMMARY_TRIGGER and (config.ENABLE_CUSTOM_PROMPT_FOR_ALL_CHANNEL or group_id in config.WHITELIST_CUSTOM_PROMPT_GROUPS)
    
# Handle message events
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_message = event.message.text
        user_id = event.source.user_id
        group_id = event.source.group_id if event.source.type == "group" else user_id

        print(f"Handling message from user {user_id} in group {group_id}: {user_message}")

        # Check if the message is a reset command
        if user_message.strip() == "ขุนพระ reset":
            if group_id in messages:
                messages[group_id].clear()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="ขุนพระรีเซ็ตข้อมูลสำหรับกลุ่มนี้แล้วครับ! 🗑️")
                )
            return

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
            custom_prompt = None
            if should_use_custom_prompt(user_message, group_id):
                custom_prompt = user_message[len(config.CHAT_SUMMARY_TRIGGER):].strip() + " ตอบสั้นๆ ครับ ใส่ emoji ผสม สูงสุด 5"
            output = send_custom_prompt(custom_prompt) if custom_prompt else summarize_chat(group_id)
            if output:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=output)
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="อ่า... ขุนพระ ไม่เห็นมีข้อความใหม่ให้สรุปแล้วนะครับ\nไว้คุยกันเพิ่ม ค่อยเรียก 'ขุนพระ' ใหม่นะคับ")
                )
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขอโทษครับ, ตอนนี้ ขุนพระ เจอปัญหาทางเทคนิค กรุณารอ @Por มาแก้ทีนะจ้า")
        )

# Handle join events (bot being added to a group)
@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id if event.source.type == "group" else None
    if group_id:
        welcome_message = "สวัสดีทุกคน! 'ขุนพระ' เองครับ 🐦\nผมสามารถช่วยสรุปบทสนทนาของคุณได้ เพียงพิมพ์เรียก 'ขุนพระ' แล้วผมจะช่วยสรุปให้ครับ!\n\nไม่ต้องห่วงนะครับ ผมไม่มีการเก็บข้อมูลใดๆ แน่นอน ให้ @Por รับประกัน".format(config.CHAT_SUMMARY_TRIGGER)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=welcome_message)
        )

# Function to send custom prompt to OpenAI API
def send_custom_prompt(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7
    )
    output = response.choices[0].message.content.strip()
    print(f"OpenAI response: {output}")
    return output

# Function to summarize the messages of the last 24 hours
def summarize_chat(group_id):
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
    prompt = "Summarize all text after this prompt as bullet points in Thai language. Keep it short, concise, and focus only on the high-priority information. Emojify the result, used up to 5 emojis. Do not include other opinions or extra details. If there is decision-making involved, just give the conclusion. Make the summary simple and easy to read.\n"
    prompt += "\n".join(last_24_hours_messages)
    output = send_custom_prompt(prompt)

    ## Reset message after summarize
    messages[group_id].clear()
    return "ได้ครับ, ขุนพระ สรุปให้ฟังครับ\n\n" + output + "\n\n ปล. ไม่ต้องห่วงนะคับ ผมไม่ได้แอบเก็บข้อมูลใดๆ"


# Run Flask app
if __name__ == "__main__":
    app.run(port=8080)
