import logging
import telegram
import os
from flask import Flask, request
from telegram.ext import Dispatcher, MessageHandler, Filters
import openai

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Default language and configuration
chat_language = os.getenv("INIT_LANGUAGE", default="zh")
MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default=20))
LANGUAGE_TABLE = {
    "zh": "哈囉！",
    "en": "Hello!"
}

class Prompts:
    def __init__(self):
        self.msg_list = []
        self.msg_list.append(f"AI:{LANGUAGE_TABLE[chat_language]}")
    
    def add_msg(self, new_msg):
        if len(self.msg_list) >= MSG_LIST_LIMIT:
            self.remove_msg()
        self.msg_list.append(new_msg)
    
    def remove_msg(self):
        self.msg_list.pop(0)
    
    def generate_prompt(self):
        return '\n'.join(self.msg_list)  

class ChatGPT:  
    def __init__(self):
        self.prompt = Prompts()
        self.model = os.getenv("OPENAI_MODEL", default="text-davinci-003")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", default=0))
        self.frequency_penalty = float(os.getenv("OPENAI_FREQUENCY_PENALTY", default=0))
        self.presence_penalty = float(os.getenv("OPENAI_PRESENCE_PENALTY", default=0.6))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default=240))
    
    def get_response(self):
        response = openai.Completion.create(
            model=self.model,
            prompt=self.prompt.generate_prompt(),
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self.max_tokens
        )
        
        print("AI回答內容：")        
        print(response['choices'][0]['text'].strip())

        print("AI原始回覆資料內容：")      
        print(response)
        
        return response['choices'][0]['text'].strip()
    
    def add_msg(self, text):
        self.prompt.add_msg(text)

# Set up Telegram Bot token
telegram_bot_token = str(os.getenv("TELEGRAM_BOT_TOKEN"))

# Enable logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize the bot using the provided Telegram token
bot = telegram.Bot(token=telegram_bot_token)

# Initialize the dispatcher (used by the Telegram bot to process updates)
dispatcher = Dispatcher(bot, None)

@app.route('/callback', methods=['POST'])
def webhook_handler():
    """Handle incoming webhook updates from Telegram."""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

def reply_handler(bot, update):
    """Handle incoming messages from users and generate replies using GPT."""
    chatgpt = ChatGPT()
    
    # Add user message to the prompt
    chatgpt.prompt.add_msg(update.message.text)
    
    # Get GPT response
    ai_reply_response = chatgpt.get_response()
    
    # Send the response to the user on Telegram
    update.message.reply_text(ai_reply_response)

# Add handler for text messages (chat messages)
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))

if __name__ == "__main__":
    # Set the webhook for Telegram to call Flask's /callback route
    webhook_url = "https://your_domain.com/callback"  # Replace with your actual domain
    bot.set_webhook(url=webhook_url)
    
    # Run the Flask app
    app.run(debug=True)
