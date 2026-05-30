import json
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time

from communication.slack_api import slack_token

# Load Slack Token (set your token as an environment variable)
CHANNEL_ID = "C081YDKAD53"  # Replace with your Slack channel ID
JSON_FILE = "data/slack_messages.json"

# Initialize the Slack client
client = WebClient(token=slack_token)


def fetch_channel_messages(channel_id, latest_timestamp=None):
    """
    Fetch messages from a Slack channel.
    """
    try:
        response = client.conversations_history(
            channel=channel_id,
            latest=latest_timestamp,
            limit=100,  # Max allowed per request
        )
        return response.get("messages", []), response.get("has_more", False)
    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
        return [], False


def load_messages_from_json():
    """
    Load previously saved messages from a JSON file.
    """
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_messages_to_json(messages):
    """
    Save the updated list of messages to a JSON file.
    """
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4)


def main():
    """
    Main function to fetch and save Slack messages in a loop.
    """
    # Load existing messages from the JSON file
    saved_messages = load_messages_from_json()
    saved_message_ids = {msg["ts"] for msg in saved_messages}

    # Determine the latest timestamp from saved messages
    latest_timestamp = max((msg["ts"] for msg in saved_messages), default=None)

    print("Fetching initial messages...")
    messages, has_more = fetch_channel_messages(CHANNEL_ID, latest_timestamp)

    # Filter out already saved messages and merge with existing ones
    new_messages = [msg for msg in messages if msg["ts"] not in saved_message_ids]
    if new_messages:
        saved_messages.extend(new_messages)
        save_messages_to_json(saved_messages)
        print(f"Saved {len(new_messages)} new messages to {JSON_FILE}.")

    while True:
        print("Listening for new messages...")
        messages, _ = fetch_channel_messages(CHANNEL_ID, latest_timestamp)

        # Filter out already saved messages
        new_messages = [msg for msg in messages if msg["ts"] not in saved_message_ids]

        if new_messages:
            # Add new messages to the list and update the JSON file
            saved_messages.extend(new_messages)
            saved_message_ids.update(msg["ts"] for msg in new_messages)
            save_messages_to_json(saved_messages)
            print(f"Saved {len(new_messages)} new messages to {JSON_FILE}.")

            # Update the latest timestamp
            latest_timestamp = new_messages[0]["ts"]

        # Wait before checking for new messages
        time.sleep(10)


if __name__ == "__main__":
    main()
