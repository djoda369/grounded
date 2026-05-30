from core.helper.files import json_read_file, json_write_file


def extract_channel_links():
    channel_messages = json_read_file("data/channel_links.json")
    raw = {}
    for channel in channel_messages:
        raw[channel] = {}
        for message in channel_messages[channel]:
            if "from_url" in message:
                raw[channel][message["from_url"]] = {}
    return raw


def main():
    links = extract_channel_links()
    json_write_file("data/slack_links.json", links)
    print(len(links))


if __name__ == "__main__":
   main()
