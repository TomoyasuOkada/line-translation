from google import genai
from google.genai import types
import os
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import dotenv
dotenv.load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANEL_SECRET = os.getenv("CHANEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANEL_SECRET)
client = genai.Client(api_key=GEMINI_API_KEY)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        output_text = generate_content(event.message.text)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=output_text)]
            )
        )


def generate_content(input_text: str) -> str:
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        config=types.GenerateContentConfig(
            system_instruction="If the user's input is in Japanese, translate it into natural English. If the user's input is in English, translate it into natural Japanese. "
            "Do not provide alternatives. "
            "Do not use '/'. "
            "Do not explain."),
        contents=input_text,    
    )
    return response.text


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)