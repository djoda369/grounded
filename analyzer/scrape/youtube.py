from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url):
    try:
        parsed_url = urlparse(url)
        if parsed_url.netloc in ["www.youtube.com", "youtube.com"]:
            query_params = parse_qs(parsed_url.query)
            return query_params.get("v", [None])[0]
        elif parsed_url.netloc == "youtu.be":  # For shortened URLs
            return parsed_url.path.lstrip("/")
    except Exception as e:
        print(f"Error: {e}")

    return None


def youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return "\n".join([f"{entry['text']}" for entry in transcript])
    except Exception as e:
        print("Error " + str(e))
        return None


class YoutubeScraper:

    def __init__(self):
        pass

    def scrape(self, request):
        if "url" not in request:
            request["error"] = "Url could not be found."
            return request

        video_id = extract_video_id(request["url"])
        if not video_id:
            request["error"] = "Could not find video ID from URL"
            return request

        request["text"] = youtube_transcript(video_id).replace("\n", " ")
        return request


if __name__ == "__main__":
    links = ["https://youtu.be/lVI_J1cbFb4?si=hfpY5dNaKmdLmm1r"]
    scraper = YoutubeScraper()
    for link in links:
        request = scraper.scrape({"url": link})
        print(request)
