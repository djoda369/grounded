import pandas as pd
import json
from slack_sdk.errors import SlackApiError

from communication.slack_api import slack_client

# Constants
CSV_FILE = "data/gaia_slack.csv"
JSON_FILE = "data/channel_messages.json"


def fetch_channel_messages(channel_id, latest_timestamp=None):
    """
    Fetch messages from a Slack channel.
    """
    try:
        response = slack_client.conversations_history(
            channel=channel_id,
            latest=latest_timestamp,
            limit=100,  # Max allowed per request
        )
        return response.get("messages", []), response.get("has_more", False)
    except SlackApiError as e:
        print(f"Error fetching messages for channel {channel_id}: {e.response['error']}")
        return [], False


def save_messages_to_json(messages):
    """
    Save the updated list of messages to a JSON file.
    """
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4)


def main():
    # Step 1: Read the CSV file
    df = pd.read_csv(CSV_FILE)

    # Step 2: Fetch and store messages
    all_messages = {}  # Dictionary to store messages for each channel

    for _, row in df.iterrows():
        channel_id = row["ID"]
        print(f"Fetching messages for channel: {channel_id}")

        messages = []
        latest_timestamp = None
        has_more = True

        while has_more:
            fetched_messages, has_more = fetch_channel_messages(channel_id, latest_timestamp)
            messages.extend(fetched_messages)

            # Update latest timestamp for pagination
            if fetched_messages:
                latest_timestamp = fetched_messages[-1].get("ts")

        all_messages[channel_id] = messages

    # Step 3: Save messages to a JSON file
    save_messages_to_json(all_messages)
    print(f"Messages saved to {JSON_FILE}")


if __name__ == "__main__":
    main()
