import base64
from io import BytesIO
import streamlit as st

from mutagen.mp3 import MP3

from core.gpt.chatgpt import llm_chat
from core.gpt.history import History
from voice import text_to_speech_bytes, autoplay_audio

st.set_page_config(page_title="🗣️ Voice Player", layout="centered")

if "history" not in st.session_state:
    st.session_state.history = History()

approach = """
Roleplay as Gaia from GroundedWorld as you are talking to a potential client from GroundedWorld wanting to have a better understanding of GroundedWorld.
If the client has a question about GroundedWorld, ask follow up questions to understand their question better. Then if they have clarified their question we can recommend a service that GroundedWorld provides. If the client is interested in the solution, we can recommend sitting down for a 30 minute call using the following link <URL>.
Always try to reference any context of previous projects that Grounded World has done before to secure clients into understanding that Grounded World is the right partner.
Prioritize the context of both Grounded World and its experience and selected news over general information about the industry or problem so that any information mentioned can be linked back Grounded World.
"""

st.title("🗣️ Voice Assistant Player")
st.write("Chat with Gaia and hear the responses immediately!")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def generate_ai_response(user_message):
    st.session_state.history.system(approach)
    st.session_state.history.user(user_message)
    return llm_chat(st.session_state.history)


with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_area("You:", height=100)
    submitted = st.form_submit_button("Send")

if submitted and user_message.strip():
    # Store user message
    st.session_state.chat_history.append(("You", user_message))

    with st.spinner("Generating response..."):
        ai_response = generate_ai_response(user_message)
        st.session_state.chat_history.append(("Gaia", ai_response))

        # TTS
        audio_bytes = text_to_speech_bytes(ai_response)
        b64_audio = base64.b64encode(audio_bytes).decode()
        autoplay_audio(b64_audio)

        # Download button
        st.download_button(
            label="Download Audio",
            data=audio_bytes,
            file_name="voice_response.mp3",
            mime="audio/mpeg"
        )

        # Optional: Get duration
        audio = MP3(BytesIO(audio_bytes))
        duration_seconds = audio.info.length
        st.write(f"⏱️ Duration: {duration_seconds:.2f} seconds")

# Display chat history
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(f"**Gaia:** {message}")
