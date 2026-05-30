import os
import time

import rootpath

from core.gpt.chatgpt import llm_chat
from core.gpt.history import History
from core.helper.files import json_read_file, json_write_file, sanitize_filename, read_file
from path import DETECTED_PATH

scrape_key = "scraped"


def extract_channel_links():
    channel_messages = json_read_file("data/channel_messages.json")
    slack_data = {}
    link_count = 0
    for channel in channel_messages:
        slack_data[channel] = []
        for message in channel_messages[channel]:
            # Get the current timestamp
            current_time = time.time()

            # Calculate the range for one week from now
            one_week_in_seconds = 7 * 24 * 60 * 60  # 7 days in seconds
            week_from_now = current_time - one_week_in_seconds

            # Find all elements with 'ts' within a week from now
            if current_time >= float(message["ts"]) >= week_from_now:

                if "attachments" in message:
                    for attachment in message["attachments"]:
                        if "from_url" in attachment:
                            slack_data[channel].append(attachment)
                            link_count += 1
        print(link_count)
    print(f"Found {link_count} links")
    print(f"In {len(slack_data)} channels")
    return slack_data


def scrape_channel_links(data: dict, channel_name: str):
    folder = os.path.join(DETECTED_PATH, "communication", "slack", channel_name).replace("\\", "/")
    if not os.path.exists(folder):
        os.mkdir(folder)

    channel_links = data[channel_name]

    texts = {}
    for attachment in channel_links:
        url = attachment["from_url"]
        print(url, scrape_key in attachment)
        file_path = os.path.join(folder, f"{sanitize_filename(url)}.txt").replace("\\", "/")
        if os.path.exists(file_path):
            texts[url] = read_file(file_path)

    return texts


if __name__ == "__main__":
    file_name = "data/weekly_messages.json"
    #data = extract_channel_links()
    #json_write_file(file_name, data)
    summary_file = "data/weekly_summaries.json"

    data = json_read_file(file_name)
    summaries = json_read_file(summary_file)
    for channel in data:
        if channel in summaries:
            continue
        texts = scrape_channel_links(data, channel)
        history = History()
        if len(texts) == 0:
            continue

        for url in texts:
            history.user(url + ": " + texts[url])
        history.system("Summarize the top 5 insights from the links from this week:")
        answer = llm_chat(history)
        history.assistant(answer)
        history.system("Write a newsletter incorporating the top 5 insights to write a compelling update:")
        answer = llm_chat(history)
        summaries[channel] = answer
        print(channel, ": ", answer)
        json_write_file(summary_file, summaries)
