import json
import os

import rootpath

from core.helper.files import sanitize_filename
from path import DETECTED_PATH
from research.api.news import NewsScraper


def get_new_articles(topic, search_query):
    # Path to save/load the JSON file
    topic_path = os.path.join(DETECTED_PATH, "data", "news", topic).replace("\\", "/")
    if not os.path.exists(topic_path):
        os.mkdir(topic_path)

    news_path = os.path.join(topic_path, f"{sanitize_filename(search_query)}.json").replace("\\", "/")

    # Initialize the scraper
    scraper = NewsScraper()
    new_links = scraper.scrape(search_query)

    # Check if the JSON file exists
    if os.path.exists(news_path):
        # If file exists, read the existing articles
        with open(news_path, "r") as json_file:
            existing_links = json.load(json_file)

        # Extract the URLs from existing articles
        existing_urls = {article['link'] for article in existing_links}

        # Filter new links to only include those not already in the existing file
        new_links = [link for link in new_links if link['link'] not in existing_urls]

        if new_links:
            # If there are new links, append them to the file
            existing_links.extend(new_links)
            with open(news_path, "w") as json_file:
                json.dump(existing_links, json_file, indent=4)
            return new_links  # Return only the newly scraped links
        else:
            return []  # No new links, so return an empty list
    else:
        # If the file doesn't exist, save the scraped links and don't return any results
        with open(news_path, "w") as json_file:
            json.dump(new_links, json_file, indent=4)
        return []  # No results to return, as it's the warm-up phase


def main():
    # Load the JSON file
    filename = "data/gaia_channels.json"
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file '{filename}'.")
        return

    # Process each topic
    for topic in data.get("topics", []):
        title = topic.get("title", "Unknown Title")
        subjects = topic.get("subjects", [])
        for subject in subjects:
            get_new_articles(title, subject)


def search_one(topic: str = "test", search_query: str = 'sustainable living'):
    new_articles = get_new_articles(topic, search_query)

    if new_articles:
        print("Newly scraped articles:")
        for article in new_articles:
            print(article)
    else:
        print("No new articles or file was just created.")


# Example usage
if __name__ == '__main__':
    main()