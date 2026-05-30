import os

from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()


class InstagramScraper:

    def __init__(self, amount_posts: int = 10):
        self.amount_posts = amount_posts

    def scrape(self, username: str):

        cl = Client()
        cl.login(os.environ["INSTAGRAM_USERNAME"], os.environ["INSTAGRAM_PASSWORD"])

        user_id = cl.user_id_from_username(username)
        medias = cl.user_medias(user_id, self.amount_posts)

        posts = []
        for media in medias:
            print(media)
            if media.thumbnail_url:
                data = {"title": media.title, "caption": media.caption_text, "likes": media.like_count, "transcript": "",
                        "view_count": media.view_count, "comments_count": media.comment_count, "description": "",
                        "url": str(media.thumbnail_url) if media.thumbnail_url else "",
                        "video": str(media.video_url) if media.video_url else "", "date": media.taken_at}
                posts.append(data)

        return posts


if __name__ == "__main__":
    username = "reset_energia"
    scraper = InstagramScraper()
    print(scraper.scrape(username))
