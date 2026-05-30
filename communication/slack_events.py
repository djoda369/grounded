
from slack_bolt.adapter.socket_mode import SocketModeHandler

from communication.slack_api import slack_client, app, app_token


def get_channel_name(channel_id):
    try:
        # Call the conversations.info method of the Slack API
        response = slack_client.conversations_info(channel=channel_id)
        print(response)
        # Extract the channel name from the response
        channel_name = response['channel']['name']
        return channel_name
    except Exception as e:
        print(f"Error getting channel name: {e}")
        return None


def _send_message(channel_id, message):
    chat_message = {
        "channel": channel_id,
        "text": message['content'],
    }
    slack_client.chat_postMessage(**chat_message)


@app.event("message")
def handle_message(event, say):
    print("onMessage", event, say)


if __name__ == "__main__":
    SocketModeHandler(app, app_token=app_token).start()
