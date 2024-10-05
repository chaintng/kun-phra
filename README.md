# LINE Chat Summary Bot

This project is a LINE bot that listens to messages in a LINE group and summarizes the conversation from the last 24 hours into bullet points upon receiving the trigger command "CHAT SUMMARY". The bot uses the LINE Messaging API and OpenAI's GPT-3 API for generating summaries.

## Features

- Listens to messages in LINE groups or individual chats.
- Stores messages in memory for up to 24 hours.
- When triggered by the command "CHAT SUMMARY", it summarizes the last 24 hours' conversation into bullet points using OpenAI's GPT-3.

## Requirements

To run this project, you'll need:

- Python 3.7 or higher
- LINE Channel Access Token and Channel Secret
- OpenAI API Key

### Dependencies

The following Python packages are required:

- Flask (for creating the web server)
- line-bot-sdk (for interacting with LINE's Messaging API)
- openai (for GPT-3 integration)

All dependencies are listed in the `requirements.txt` file:

```
Flask==2.1.1
line-bot-sdk==2.1.0
openai==0.27.0
```

To install the dependencies, run:

```
pip install -r requirements.txt
```

## Environment Variables

To configure the bot, set the following environment variables:

- `LINE_CHANNEL_ACCESS_TOKEN`: Your LINE channel access token.
- `LINE_CHANNEL_SECRET`: Your LINE channel secret.
- `OPENAI_API_KEY`: Your OpenAI API key.

## Running the Bot

1. Clone the repository:

   ```
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Set the required environment variables:

   ```
   export LINE_CHANNEL_ACCESS_TOKEN='your_line_channel_access_token'
   export LINE_CHANNEL_SECRET='your_line_channel_secret'
   export OPENAI_API_KEY='your_openai_api_key'
   ```

4. Run the Flask app:

   ```
   python app.py
   ```

5. Use a tunneling service like [ngrok](https://ngrok.com/) to expose the Flask server to the internet:

   ```
   ngrok http 8080
   ```

6. Set the webhook URL in the LINE Developer Console to point to your ngrok URL:

   ```
   https://<your-ngrok-subdomain>.ngrok.io/callback
   ```

## Usage

- Add the bot to your LINE group.
- The bot will start storing messages from the group.
- To get a summary of the last 24 hours, send the message "CHAT SUMMARY" to the group.

## Limitations

- The bot stores messages in memory, which means it will lose all messages if the server is restarted. For persistent storage, consider integrating a database.
- OpenAI API usage may incur costs depending on the amount of text summarized.

## License

This project is licensed under the MIT License. Feel free to use and modify it as needed.

## Contributions

Contributions are welcome! Please open an issue or submit a pull request if you'd like to improve this bot.

## Acknowledgements

- [LINE Messaging API](https://developers.line.biz/en/services/messaging-api/)
- [OpenAI API](https://openai.com/api/)

