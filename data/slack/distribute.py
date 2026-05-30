import os

import pandas as pd
import rootpath

from core.helper.files import json_read_file, json_write_file
from path import DETECTED_PATH

data = json_read_file("slack_links.json")

# Step 1: Read the CSV file
df = pd.read_csv("gaia_slack.csv")

# Step 2: Fetch and store messages
all_messages = {}  # Dictionary to store messages for each channel

catalog: dict = {}

for _, row in df.iterrows():
    channel_id = row["ID"]
    category = row["Category"]
    channel = row["Channel"]

    if category != "Others":

        print(f"Fetching messages for channel: {channel_id}")
        if category not in catalog:
            catalog[category] = {}

        first_path = os.path.join(DETECTED_PATH, "data", "topics", category.replace(" ", "_")).replace("\\", "/")
        if not os.path.exists(first_path):
            os.mkdir(first_path)

        path = os.path.join("data", "topics", category.replace(" ", "_"), channel.strip().replace("/", "-").replace(" ", "_")).replace("\\", "/")
        folder_path = os.path.join(DETECTED_PATH, path).replace("\\", "/")
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        subset = data[row["ID"]]
        full_path = os.path.join(path, "slack.json").replace("\\", "/")
        catalog[category][channel] = full_path
        json_write_file(os.path.join(DETECTED_PATH, full_path).replace("\\", "/"), subset)
    else:
        print(f"Fetching messages for channel: {channel_id}")

        path = os.path.join("data", "topics", channel.strip().replace("/", "-").replace(" ", "_")).replace("\\", "/")
        folder_path = os.path.join(DETECTED_PATH, path).replace("\\", "/")
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        subset = data[row["ID"]]
        full_path = os.path.join(path, "slack.json").replace("\\", "/")
        catalog[channel] = full_path
        json_write_file(os.path.join(DETECTED_PATH, full_path), subset)
    json_write_file("catalog.json", catalog)