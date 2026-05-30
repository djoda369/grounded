import base64
import os

import streamlit
import streamlit as st
from langchain_community.vectorstores import FAISS
from pydantic import Field, BaseModel

from core.gpt.chatgpt import llm_stream, process_stream, llm_strict
from core.gpt.knowledge import index_path, embeddings_function
from core.vault.conversation import LiteConversation
from path import DETECTED_PATH
from voice import text_to_speech_bytes, autoplay_audio


def get_base64_image(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""  # Fallback if gaia.png is missing


GAIA_IMG = get_base64_image("gaia.png")


class TalkingPointsModel(BaseModel):
    sustainable_fashion_question: bool = Field(..., description="The users question is related to the topic of sustainable fashion.")


def stream_slack(user_prompt):
    talking_points: TalkingPointsModel = llm_strict(st.session_state.conversation, "gpt-4o", TalkingPointsModel)
    if talking_points.sustainable_fashion_question:
        db = FAISS.load_local(index_path, embeddings_function, "sustainable_fashion", allow_dangerous_deserialization=True)
        for result in db.similarity_search(user_prompt, k=3):
            text = result.page_content
            print(text)
            st.session_state.conversation.system(text)
        response_stream = llm_stream(st.session_state.conversation)
        return response_stream

    response_stream = llm_stream(st.session_state.conversation)
    return response_stream


def load_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string


# TODO redo parameters to make a class to extract the data or interface to simplify the parameters
def show_background():


    if "voice" not in st.session_state:
        st.session_state.voice = True

    button_element = st.empty()
    # Streamlit button with unique key
    result = button_element.button("🔇" if not st.session_state.voice else "🔊")
    if result:
        st.session_state.voice = not st.session_state.voice
        button_element.button("🔇" if not st.session_state.voice else "🔊")

    # Fix button position via CSS targeting its key
    st.markdown(
        """
        <style>
        [data-testid="stBaseButton-secondary"] {
            position: fixed;
            width: 3%;
            top: 70%;
            right: 14%;
            z-index: 1000;
            font-size: 18px;
            padding: 5px 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Load the Gaia image (for background)
    background_image = load_image(
        os.path.join(DETECTED_PATH, "data", "images", "background3.png").replace("\\", "/"))


    # Custom CSS to set the background image to the right and 50% of the width
    st.markdown(f"""
            <style>
            /* Set the background image on the right side taking up 50% width */
            .stApp {{
                background-image: url("data:image/png;base64,{background_image}");
                background-size: auto 75%; /* 50% of the width, auto for height */
                background-position: center right; /* Centered vertically, right-aligned */
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """, unsafe_allow_html=True)


def check_lite_conversation():
    if len(st.session_state.conversation.logs) > 10 and \
            isinstance(st.session_state.conversation, LiteConversation):
        if not st.session_state.conversation.is_requested():
            prompt = "To give you a better idea on how grounded.world can help you in your role more " \
                     "specifically, please enter your email address so we can send you some more tips " \
                     "for your company specifically."
            st.session_state.conversation.assistant(prompt)
            st.session_state.conversation.set_requested(True)
            st.session_state.conversation.system("If the next message from the user contains their email address, then respond with: 'Thanks for providing your email. This will enable me to provide more contextually relevant guidance, links  and references the next time we talk! Watch out for an email with a link to enable you to ask me more specific questions around your business challenges and opportunities.'")
            st.markdown(f"""
                    <div class="chat-row chat-right">
                        <div class="chat-bubble user">{prompt}</div>
                    </div>
                    """, unsafe_allow_html=True)


def display_messages():
    for message in st.session_state.conversation.logs:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def streaming_logo_interface(initial_question):

    user_prompt = st.chat_input("Ask Gaia anything...")

    # Check if we have an input or an initial question triggered
    if user_prompt or initial_question:
        current_prompt = initial_question if initial_question else user_prompt

        # 1. Save and display the User Message immediately
        st.session_state.conversation.user(current_prompt)
        # Render your custom user bubble here if display_messages() didn't catch it
        st.markdown(f"""
                <div class="chat-row chat-right">
                    <div class="chat-bubble user">{current_prompt}</div>
                </div>
            """, unsafe_allow_html=True)

        # 2. SHOW THINKING BUBBLE (Temporary placeholder)
        thinking_placeholder = st.empty()
        with thinking_placeholder:
            st.markdown(f"""
                <div class="assistant-block">
                    <div>
                        <img src="data:image/png;base64,{GAIA_IMG}" class="avatar">
                        <span class="name" style="color: #6BB6FF;">Gaia is thinking...</span>
                    </div>
                    <div class="thinking-container">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 3. START STREAMING
        # We use an empty container for the assistant's message
        assistant_message_placeholder = st.empty()

        # Start your slack stream logic
        answers = process_stream(stream_slack(current_prompt))

        full_response = ""
        for chunk in answers:
            # Remove the thinking bubbles as soon as the first chunk arrives
            thinking_placeholder.empty()

            full_response = chunk  # Assuming 'chunk' grows or is the final state

            # Update the assistant's bubble progressively
            assistant_message_placeholder.markdown(f"""
                <div class="assistant-block">
                    <div>
                        <img src="data:image/png;base64,{GAIA_IMG}" class="avatar">
                        <span class="name">Gaia</span>
                    </div>
                    <div class="chat-bubble assistant">{full_response}</div>
                </div>
                """, unsafe_allow_html=True)

        # 4. FINALIZATION
        st.session_state.conversation.assistant(full_response)

        # TTS Logic
        if st.session_state.voice:
            audio_bytes = text_to_speech_bytes(full_response)
            b64_audio = base64.b64encode(audio_bytes).decode()
            autoplay_audio(b64_audio)

        check_lite_conversation()

        # Rerun once at the end to clean up the 'initial_question' state if necessary
        if initial_question:
            st.rerun()



def show_disclaimer():
    disclaimer = "The information provided by GAIA is for general informational purposes only and should not be construed as legal advice.<br>You should consult with an attorney licensed in your jurisdiction before making any legal decisions. No attorney-client relationship is formed by accessing or using this website."
    # Get the current Streamlit theme background color
    theme_background = st.get_option("theme.backgroundColor")

    # Determine text color based on theme
    text_color = "black" if theme_background in ["#FFFFFF", "rgb(255, 255, 255)"] else "white"

    # Disclaimer with CSS
    st.markdown(
        f"""
        <style>
        .disclaimer {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            color: {text_color};
            background-color: rgba(0, 0, 0, 0.5);
            padding: 5px 10px;
            font-size: 10px;
            z-index: 1000;
            max-height: 50px;
            overflow-y: auto;
        }}
        .mute-btn {{
            position: absolute;
            bottom: 5px;
            right: 10px;
            padding: 2px 6px;
            font-size: 10px;
            border: none;
            background-color: #444;
            color: #fff;
            border-radius: 3px;
            cursor: pointer;
        }}
        @media screen and (max-width: 600px) {{
            .disclaimer {{ font-size: 8px; padding: 5px; }}
            .mute-btn {{ font-size: 8px; padding: 1px 4px; }}
        }}
        </style>
        <div class="disclaimer">
            {disclaimer}
        </div>
        """,
        unsafe_allow_html=True
    )



if __name__ == "__main__":
    streamlit.session_state.conversation = LiteConversation("test")
    stream_slack("I want to know more about sustainable fashion")
    print(streamlit.session_state.conversation.logs)
