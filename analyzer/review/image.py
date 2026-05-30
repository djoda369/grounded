import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "gpt-4o"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def image_review(image_bytes, instruction: str, prompt: str):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{image_bytes}"}
                }
            ]}
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content
