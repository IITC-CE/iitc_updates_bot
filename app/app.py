import os
from github_webhook import Webhook
from flask import Flask
import requests

app = Flask(__name__)
LISTENER_HOST = os.environ.get('HOST', '0.0.0.0')
LISTENER_PORT = os.environ.get('PORT', '4567')
WEBHOOK_SECRET = os.environ['WEBHOOK_SECRET']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
TELEGRAM_TOPIC_ID = os.environ.get('TELEGRAM_TOPIC_ID', None)

webhook = Webhook(app, secret=WEBHOOK_SECRET)  # Defines '/postreceive' endpoint


def escape_special_characters(string):
    # List of characters to escape
    special_characters = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    # Escape each character in the string
    for character in special_characters:
        string = string.replace(character, '\\' + character)

    return string


def send_message(text):
    # Set the API endpoint URL
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Set the request payload
    payload = {
        'text': text,
        'parse_mode': 'MarkdownV2',
        'disable_notification': 'true',
        'disable_web_page_preview': 'true',
        'chat_id': TELEGRAM_CHAT_ID
    }

    if TELEGRAM_TOPIC_ID is not None:
        payload['is_topic_message'] = True
        payload['message_thread_id'] = TELEGRAM_TOPIC_ID

    # Send the POST request
    response = requests.post(url, data=payload)

    # Check the response status code
    if response.status_code != 200:
        print('Error:', response.status_code, response.text)


@app.route("/")
def hello_world():
    return "Status: ok"


@webhook.hook(event_type="pull_request")
def on_pull_request(data):
    number = data['number']
    pr_url = data['pull_request']['html_url']
    title = escape_special_characters(data['pull_request']['title'] or "")
    author = escape_special_characters(data['pull_request']['user']['login'] or "")
    author_url = data['pull_request']['user']['html_url'] or ""
    body = escape_special_characters(data['pull_request']['body'] or "")

    text = None
    if data['action'] == "opened":
        text = f"🚧 *New* \#PR{number} [{title}]({pr_url}) by [{author}]({author_url})\n\n{body}"
    if data['action'] == "reopened":
        text = f"☑️ *Reopened* \#PR{number} [{title}]({pr_url})"
    if data['action'] == "closed":
        if data['pull_request']['merged'] and data['pull_request']['merged'] == True:
            text = f"✅ *Merged* \#PR{number} [{title}]({pr_url})"
        else:
            text = f"❌ *Closed* \#PR{number} [{title}]({pr_url})"

    if text is not None:
        send_message(text)


if __name__ == "__main__":
    app.run(host=LISTENER_HOST, port=int(LISTENER_PORT))
