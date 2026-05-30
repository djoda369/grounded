import re
from typing import Dict


def extract_fireflies_data(text: str) -> Dict[str, object]:
    # only extract the data if it has the right header.
    if "<b>Title</b>: " not in text:
        return {"message": text}

    data = {}

    patterns = {
        "title": r"<b>Title</b>: (.*?)<br>",
        "date": r"<b>Date</b>: (.*?)<br>",
        "participants": r"<b>Participants</b>: (.*?)<br>",
        "transcript_link": r"<b>Transcript</b>: <a href=\"(.*?)\"",
        "audio_link": r"<b>Audio</b>: <a href=\"(.*?)\"",
        "duration": r"<b>Duration</b>: (\d+)<br>",
        "summary": r"<b>Summary</b>(.*?)<br><br><b>Outline</b>",
        "outline": r"<b>Outline</b>(.*?)<br><b>Notes</b>",
        "notes": r"<b>Notes</b>(.*?)<br><b>Action Items</b>",
        "action_items": r"<b>Action Items</b>(.*?)</li>"
    }
    # Extract each field using the defined patterns
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        print(key, match)
        if match:
            answer = match.group(1).strip()
            print(answer)
            data[key] = answer

    # Further processing for specific fields
    # Split participants by comma and strip whitespace
    if "participants" in data:
        data["participants"] = [email.strip() for email in data["participants"].split(',')]

    # Convert duration to integer
    if "duration" in data:
        data["duration"] = int(data["duration"])

    return data


if __name__ == "__main__":
    # Example usage
    text = """<b>Title</b>: Fireflies Sample Data :: 2024-10-31T04:02:23.226Z<br><b>Date</b>: Thu Oct 31 2024 00:02:24 GMT-0400 (Eastern Daylight Time)<br><b>Participants</b>: team@fireflies.ai, client@fireflies.ai, daan@mai-tai.ai, sample@fireflies.ai<br><b>Transcript</b>: <a href=\"https://app.fireflies.ai/view/Fireflies-Sample-Data-2024-10-31T04-02-23-226Z::5qzLPNY0dBcFWNxl\" target=\"_blank\">See full transcript</a><br><b>Audio</b>: <a href=\"https://app.fireflies.ai/view/Fireflies-Sample-Data-2024-10-31T04-02-23-226Z::5qzLPNY0dBcFWNxl\" target=\"_blank\">Listen to audio</a><br><b>Duration</b>: 45<br><br><b>Summary</b><li>The lecture is about the history of weather forecasting, starting with ancient cultures and their belief in weather gods. The Babylonians produced the first short-range weather forecasts based on observations of clouds and other phenomena around 650 BC, while the Chinese recognized weather patterns by 300 BC. The Greeks were the first to develop a more scientific approach to explaining the weather, with Aristotle's work holding sway for nearly 2000 years despite some errors. Inventions such as thermometers and barometers contributed to our understanding of atmospheric processes, and systematic collection of data began in the mid-19th century through records kept by people in different locations. Section one is a conversation between a man from Bariton Stansons and Angela, customer services manager at Flanders conference hotel regarding holding a conference over two days for approximately 50 or 60 people early next year in Sydney. They discuss available dates, facilities such as rooms equipped with projectors and microphones along with an open area for coffee breaks/exhibitions etc., accommodation discounts for attendees along with transport links/attractions nearby before discussing costs associated with hosting this event at their location.</li><br><br><b>Outline</b><br>1. Introduction to the lecture about the history of weather forecasting<br>2. Early history and ancient cultures' weather gods<br>3. Observations of skies and the first short-range weather forecasts<br>4. Chinese and ancient Greeks' contributions to understanding weather patterns<br>5. Aristotle's work and influence on weather theory <li><a href=\"https://app.fireflies.ai/view/Fireflies-Sample-Data-2024-10-31T04-02-23-226Z::5qzLPNY0dBcFWNxl\" target=\"_blank\">[+ 2 More]</a></li><br><b>Notes</b><br>1. The lecture is about the history of weather forecasting.<br>2. Ancient cultures had weather gods and attributed weather to their whims.<br>3. Babylonians produced the first short-range weather forecasts around 650 BC.<br>4. Chinese developed a calendar with 24 festivals associated with different weather phenomena by 300 BC.<br>5. Greeks developed a more scientific approach to explaining weather, with Aristotle's work being noteworthy. <li><a href=\"https://app.fireflies.ai/view/Fireflies-Sample-Data-2024-10-31T04-02-23-226Z::5qzLPNY0dBcFWNxl\" target=\"_blank\">[+ 6 More]</a></li><br><b>Action Items</b><br>1. Book the conference for the weekend beginning February 4th.<br>2. Use the Tesla room for talks and presentations, ensure it is equipped with a projector and microphones for the speaker and audience.<br>3. Set up an exhibition area in the central atrium for product displays and coffee breaks.<br>4. Provide WiFi access throughout the hotel.<br>5. Send a copy of the standard menu for the buffet lunch, priced at $45 per person. <li><a href=\"https://app.fireflies.ai/view/Fireflies-Sample-Data-2024-10-31T04-02-23-226Z::5qzLPNY0dBcFWNxl\" target=\"_blank\">[+ 2 More]</a></li>"""  # truncated for brevity
    data = extract_fireflies_data(text)
    print(data)
