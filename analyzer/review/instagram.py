import base64

import requests
from pydantic import BaseModel, Field

from analyzer.review.image import image_review
from core.gpt.chatgpt import llm_strict
from core.gpt.history import History
from core.helper.files import json_write_file


class PostReview(BaseModel):
    performance: str = Field(..., description="Describe in detail the performance of this post and why you came to that conclusion in one paragraph.")
    improvement: str = Field(..., description="Describe the improvements that could be made to make this post perform better in one paragraph.")


def review_instagram_images(instagram):
    for post in instagram["posts"]:
        if "image_summary" in post:
            continue

        if "url" not in post:
            continue
        response = requests.get(post["url"])

        encoded_string = base64.b64encode(response.content).decode("utf-8")

        post["image_summary"] = image_review(encoded_string, "You are an instagram post reviewer describe everything that is in the image", "Describe everything you see in the instagram image in one paragraph:")

    json_write_file(instagram["path"], instagram)

    return instagram


def review_posts(instagram):
    for post in instagram["posts"]:
        if "review" in post and "improvements" in post:
            continue
        review: PostReview = post_review(post, instagram)
        post["review"] = review.model_dump()

    json_write_file(instagram["path"], instagram)
    return instagram


def post_review(post, instagram):
    history = History()
    history.system("You are an instagram post reviewer")
    history.system("Current Trends: " + instagram["research"])
    history.system(f"Current Post likes: {post['likes']} and Account average likes: {instagram['avg_likes']}")
    history.system(f"Image description: {post['image_summary']}")
    history.system(f"Post Caption: {post['caption']}")
    history.system(f"Transcription: {post['transcript']}")

    review = llm_strict(history, "gpt-4o", PostReview)
    return review


def analyze_likes(instagram):
    total_likes = 0
    total_views = 0
    count_posts = len(instagram["posts"])

    for post in instagram["posts"]:
        total_likes += post["likes"] if post["likes"] else 0
        total_views += post["view_count"] if post["view_count"] else 0

    instagram["avg_likes"] = total_likes / count_posts
    instagram["avg_views"] = total_views / count_posts
    json_write_file(instagram["path"], instagram)
    return instagram


def sort_likes(instagram):
    instagram["posts"] = sorted(instagram["posts"], key=lambda x: x['likes'], reverse=True)
    json_write_file(instagram["path"], instagram)
    return instagram


def review_improvements(instagram):
    if "review" in instagram and "improvements" in instagram:
        return instagram

    instagram["review"] = get_review(instagram["posts"])


class SummarizePosts(BaseModel):
    performance: str = "Summarize performance of posts based on three key insights."
    improvements: str = "Summarize improvements into three main key points to improve."
    sentiment: str = "Summarize sentiment into three main key points to improve."


def get_review(posts):
    history = History()

    history.system("You are an instagram post reviewer describe in detail to summarize them")

    for post in posts:
        review = post["review"]
        history.system("Review: " + review["performance"] + " " + review["improvement"])

    history.system(f"Summarize reviews from instagram posts above and find keypoints among all:")
    answer = llm_strict(history, "gpt-4o", SummarizePosts)
    return answer.model_dump()
