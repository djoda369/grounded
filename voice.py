import os
from io import BytesIO

from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings
import streamlit as st


# Load environment variables
load_dotenv()

# Initialize ElevenLabs client
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GAIA_VOICE_ID = os.getenv("GAIA_VOICE_ID")
el = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def text_to_speech_bytes(text: str) -> bytes:
    response = el.text_to_speech.convert(
        voice_id=GAIA_VOICE_ID,  # Adam
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",
        voice_settings=VoiceSettings(
            stability=1.0,
            similarity_boost=1.0,
            style=0.5,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )
    audio_buffer = BytesIO()
    for chunk in response:
        if chunk:
            audio_buffer.write(chunk)
    return audio_buffer.getvalue()


def autoplay_audio(b64):
    md = f"""
        <audio autoplay style="display:none;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)


if __name__ == "__main__":
    print(text_to_speech_bytes("Hello my name is Gaia."))