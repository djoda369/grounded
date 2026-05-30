from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from communication.slack_api import slack_token

# Load Slack Token (set your token as an environment variable)
CHANNEL_ID = "C081YDKAD53"  # Replace with your Slack channel ID
JSON_FILE = "data/slack_messages.json"

# Initialize the Slack client
client = WebClient(token=slack_token)


def send_hello_world_message():
    """
    Sends a "Hello, World!" message to the specified Slack channel.
    """
    try:
        response = client.chat_postMessage(
            channel=CHANNEL_ID,
            text="Hello, World!"  # The message content
        )
        print(f"Message sent successfully: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


if __name__ == "__main__":
    send_hello_world_message()
    