import os
from asyncio import Lock

from communication.read_channels import fetch_channel_messages
from core.helper.files import json_read_file, json_write_file, sanitize_filename
from path import DETECTED_PATH
from research.website import WebsiteScraper

from concurrent.futures import ThreadPoolExecutor

scrape_key = "scraped"


def extract_channel_links():
    channel_messages = json_read_file("data/channel_messages.json")
    slack_data = {}
    link_count = 0
    for channel in channel_messages:
        slack_data[channel] = []
        for message in channel_messages[channel]:
            if "attachments" in message:
                for attachment in message["attachments"]:
                    if "from_url" in attachment:
                        slack_data[channel].append(attachment)
                        link_count += 1
        print(link_count)
    print(f"Found {link_count} links")
    print(f"In {len(slack_data)} channels")
    return slack_data


def count_txt_files_in_slack():
    """
    Counts the number of .txt files in the subfolders of a folder named 'slack'.

    Returns:
        int: The total number of .txt files found.
    """
    base_folder = 'slack'
    txt_file_count = 0

    # Traverse the folder structure
    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.endswith('.txt'):
                txt_file_count += 1

    return txt_file_count


def scrape_channel_links(folder: str, slack_messages: list[dict], channel_name: str):

    if not os.path.exists(folder):
        os.mkdir(folder)

    scraper = WebsiteScraper(keep_open=True, save_directory=folder)
    failed_websites = []

    scrape_path = os.path.join(folder, "scraping.json").replace("\\", "/")
    scrape_meta = json_read_file(scrape_path)

    if scrape_meta:
        if "failed" in scrape_meta:
            failed_websites = scrape_meta["failed"]

    for message in slack_messages:

        if 'attachments' in message:
            if len(message['attachments']) > 0:
                if "from_url" in message["attachments"][0]:
                    url = message["attachments"][0]["from_url"]
                    if "youtube.com" in url:
                        continue

                    if "linkedin.com" in url:
                        continue

                    file_path = os.path.join(folder, f"{sanitize_filename(url)}.txt").replace("\\", "/")
                    if os.path.exists(file_path):
                        continue

                    print(url)
                    text = scraper.scrape(url)
                    if not text:
                        print("failed to scrape ", str(url))
                        failed_websites.append(url)

                        json_write_file(scrape_path, {"failed": failed_websites})

    scraper.close()
    print("Finished channel", channel_name)


def thought_leadership_sync():
    channel_id = "C04B9SH1GRY"
    slack_data, has_more = fetch_channel_messages(channel_id)
    folder = os.path.join(DETECTED_PATH, "thoughtleadership").replace("\\", "/")
    scrape_channel_links(folder, slack_data, channel_id)


if __name__ == "__main__":
    thought_leadership_sync()