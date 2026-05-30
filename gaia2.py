import uuid

import streamlit
import streamlit as st

from conversation_util import initialize_deep_conversation, initialize_lite_conversation, deep_questions, lite_questions
from core.gpt.chatgpt import llm_chat
from core.helper.interface import streaming_logo_interface, show_background, show_disclaimer, display_messages
from core.vault.conversation import DeepConversation, LiteConversation

GAIA_INTRO = "What would you like to know?"


def show_interface():
    utm_source = st.query_params.get("utm_source", None)  # Extract the first value or None
    utm_medium = st.query_params.get("utm_medium", None)  # LITE
    utm_campaign = st.query_params.get("utm_campaign", "sustainable-fashion")  # LITE

    email = st.query_params.get("email", None)  # DEEP
    question = st.query_params.get("question", None)

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())



    initial_question = None
    if "history" not in streamlit.session_state:
        if email:
            st.session_state.conversation = DeepConversation(st.session_state.session_id, email)
            if len(st.session_state.conversation.logs) == 0:
                streamlit.session_state.conversation.assistant(GAIA_INTRO)
                initial_question = initialize_deep_conversation(email)

                if question in deep_questions:
                    if deep_questions[question] in st.session_state.company_data:
                        initial_question = st.session_state.company_data[deep_questions[question]]
        else:
            st.session_state.conversation = LiteConversation(st.session_state.session_id)
            if len(st.session_state.conversation.logs) == 0:
                streamlit.session_state.conversation.assistant(GAIA_INTRO)
                initial_question = initialize_lite_conversation()

                if question:
                    if question in lite_questions:
                        initial_question = lite_questions[question]

    # Main program logic (call this function when you want to start the thread)
    try:
        print("initial", initial_question)
        streaming_logo_interface(initial_question)
    except KeyboardInterrupt:
        print("Program interrupted.")

def apply_gaia_overrides():
    st.markdown("""
    <style>
    /* Remove Streamlit padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0;
    }

    /* Hide Streamlit header */
    header {visibility: hidden;}

    /* Remove top spacing */
    .stApp {
        background: #0B0A0A;
    }

    /* Buttons → glass style */
    .stButton > button {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.8);
        backdrop-filter: blur(20px);
        border-radius: 12px;
    }

    .stButton > button:hover {
        background: rgba(255,255,255,0.12);
    }

    /* Input fields */
    input, textarea {
        background: rgba(255,255,255,0.06) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* Sidebar (if used) */
    section[data-testid="stSidebar"] {
        background: #0B0A0A;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    background: str = "background.png"
    company_name = "Hello, I'm Gaia."

    emoji = "🌱"
    st.set_page_config(
        page_title=f"{company_name}",
        page_icon=emoji,
        layout="wide",
        menu_items={
            "Get Help": "https://gaia.zeeuwe.com/v2"
        }
    )
    apply_gaia_overrides()
    st.title(company_name)

    col1, col2 = st.columns([75, 25])
    with col1:
        display_messages()

    show_background()
    show_interface()
    show_disclaimer()
