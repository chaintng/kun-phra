import os
from openai import OpenAI

# LINE API credentials
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# App Configuration
ENABLE_CUSTOM_PROMPT=False
CHAT_SUMMARY_TRIGGER = "ขุนพระ"
IGNORE_WORDS = ["ขุนพระ"]
MAX_MESSAGES_PER_GROUP = 1000
