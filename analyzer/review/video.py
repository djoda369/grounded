import base64
import requests
from moviepy import VideoFileClip
from openai import OpenAI

from core.helper.files import json_write_file
from image import image_review

client = OpenAI()


def download_video(video_url, output_file):
    """
    Download video from the provided URL and save it to the specified output file.
    """
    video_response = requests.get(video_url)
    with open(output_file, "wb") as file:
        file.write(video_response.content)
    return output_file


def extract_audio_from_video(video_file, audio_output):
    """
    Extract audio from the video file and save it as an audio file.
    """
    video_clip = VideoFileClip(video_file)
    video_clip.audio.write_atiudiofile(audio_output)
    return audio_output


def transcribe_audio(audio_file):
    """
    Transcribe the audio using OpenAI's Whisper model.
    """
    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=file
        )
    return transcription.text


def summarize_transcript_video(instagram):
    """
    Summarize the transcripts from Instagram video posts.
    """
    for post in instagram["posts"]:
        if "transcript" in post:
            continue

        if "video" not in post:
            continue

        response = requests.get(post["video"])
        encoded_string = base64.b64encode(response.content).decode("utf-8")
        post["image_summary"] = image_review(encoded_string)

    json_write_file(instagram["path"], instagram)
    return instagram


def process_instagram_video(video_url, video_output, audio_output):
    """
    Process an Instagram video: download it, extract audio, transcribe, and return transcription.
    """
    # Download the video
    downloaded_video = download_video(video_url, video_output)

    # Extract audio from the video
    extracted_audio = extract_audio_from_video(downloaded_video, audio_output)

    # Transcribe the audio
    transcription = transcribe_audio(extracted_audio)
    return transcription


def transcript_video_instagram(instagram):
    for post in instagram["posts"]:
        if "transcript" in post:
            continue

        if "video" not in post:
            continue

        post["transcript"] = process_instagram_video(post["video"], "data/video.mp4", "data/audio.mp3")

    json_write_file(instagram["path"], instagram)

    return instagram


if __name__ == "__main__":
    # URL of the Instagram video
    video_url = "https://instagram.fsgn8-3.fna.fbcdn.net/o1/v/t16/f1/m86/024068533BD7D2338168099D00EA74A2_video_dashinit.mp4"

    # Paths for saving the downloaded video and extracted audio
    video_file = "data/downloaded_instagram_video.mp4"
    audio_file = "data/extracted_audio.mp3"

    # Process the video and get the transcription
    transcription = process_instagram_video(video_url, video_file, audio_file)

    print(f"Transcription: {transcription}")
