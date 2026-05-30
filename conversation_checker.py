
import os
import json
from datetime import datetime, timedelta

import rootpath
from pydantic import BaseModel, Field

from communication.link_scraper import thought_leadership_sync
from conversation_util import lite_function, deep_function
from core.gpt.chatgpt import llm_strict
from core.gpt.knowledge import refresh_index
from core.vault.conversation import LiteConversation, DeepConversation
from path import DETECTED_PATH


# Iterate through files in the folder
class EmailExtraction(BaseModel):
    email: str = Field(..., description="Client's email address")
    is_email_available: bool = Field(..., description="Did the user give their email address in this conversation?")


def get_path_processed(folder: str):
    # Configuration
    folder_path = os.path.join(DETECTED_PATH, "data", "conversation", folder).replace("\\", "/")
    processed_json = os.path.join(DETECTED_PATH, "data", "analysis", folder, "processed_files.json").replace("\\", "/")

    # Initialize the processed files JSON if it doesn't exist
    if not os.path.exists(processed_json):
        with open(processed_json, "w") as f:
            json.dump({"processed": []}, f)

    # Load processed files
    with open(processed_json, "r") as f:
        processed_data = json.load(f)

    return folder_path, processed_json, processed_data


def analyze_conversations(folder: str, processing_function):
    folder_path, processed_json, processed_data = get_path_processed(folder)
    processed_files = processed_data.get("processed", [])
    print("analyzing", folder)
    # Current time
    current_time = datetime.now()

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name).replace("\\", "/")

        # Skip directories
        if not os.path.isfile(file_path):
            continue

        # Get the last modified time of the file
        last_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

        # Check if the file was modified more than 1 hour ago
        if current_time - last_modified_time <= timedelta(minutes=30):
            continue

        # Check if the file has already been processed
        if file_name in processed_files:
            continue

        print(f"Processing file: {file_name}")

        # Extract Email from Conversation

        # Analyze Company
        if folder == "lite":
            print(file_name)
            conversation = LiteConversation(file_name.replace(".json", ""))

            if len(conversation.logs) == 0:
                print("logs are unavailable")
                continue

            email: EmailExtraction = llm_strict(conversation, "gpt-4o", EmailExtraction)
            if email:
                print("conversation is processed")
                if email.is_email_available:
                    print("email is available")
                    processing_function(email.email, conversation)
            else:
                print("email is none")
        elif folder == "deep":
            conversation = DeepConversation(file_name.replace(".json", ""))

            if len(conversation.logs) == 0:
                print("logs are unavailable")
                continue

            processing_function(conversation)

        # Add the file to the processed list
        processed_files.append(file_name)

    # Save the updated processed files list
    with open(processed_json, "w") as f:
        json.dump({"processed": processed_files}, f)

    print("Processing complete.")


def analyze_meetings():
    analyze_conversations("lite", lite_function)
    analyze_conversations("deep", deep_function)

    try:
        thought_leadership_sync()
        refresh_index()
    except:
        # Some Error Handling.
        pass


if __name__ == "__main__":
    print("Checking conversations")
    analyze_meetings()
