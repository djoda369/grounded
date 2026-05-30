import streamlit as st
import base64
import time
import uuid
# Ensure these imports match your project structure
from conversation_util import initialize_deep_conversation, initialize_lite_conversation, deep_questions, lite_questions
from core.helper.interface import GAIA_IMG
from core.vault.conversation import DeepConversation, LiteConversation

# --- 1. CONFIG & ASSETS ---
st.set_page_config(page_title="Gaia AI", page_icon="🌱", layout="wide")



# --- 2. CUSTOM STYLES (The "Niver" Interface) ---
st.markdown(f"""
<style>
    header {{ visibility: hidden; }}

    /* Chat Layout */
    .assistant-block {{ display: flex; flex-direction: column; gap: 6px; max-width: 80%; margin-bottom: 12px; }}
    .chat-row {{ display: flex; margin-bottom: 12px; }}
    .chat-right {{ justify-content: flex-end; }}

    .avatar {{ width: 28px; height: 28px; border-radius: 50%; margin-right: 8px; border: 1px solid #6BB6FF; }}
    .gaia-name {{ font-size: 12px; color: #6BB6FF; font-weight: 600; }}

    .chat-bubble {{
        padding: 12px 16px; font-size: 14px; border-radius: 16px; 
        white-space: pre-wrap; word-wrap: break-word; backdrop-filter: blur(12px);
     Sans-serif; }}

    .assistant {{ background: rgba(255, 255, 255, 0.05); color: #E0E0E0; border: 1px solid rgba(255, 255, 255, 0.1); border-bottom-left-radius: 6px; }}
    .user {{ background: rgba(30, 144, 255, 0.15); color: white; border: 1px solid rgba(30, 144, 255, 0.3); border-bottom-right-radius: 6px; }}

    /* Thinking Dots */
    .thinking-container {{ display: flex; gap: 4px; padding: 12px 16px; background: rgba(255,255,255,0.05); border-radius: 16px; width: fit-content; }}
    .dot {{ width: 8px; height: 8px; background: #6BB6FF; border-radius: 50%; animation: dotPulse 1.4s infinite ease-in-out; }}
    .dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .dot:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes dotPulse {{ 0%, 80%, 100% {{ transform: scale(0.6); opacity: 0.3; }} 40% {{ transform: scale(1); opacity: 1; }} }}

    /* Footer */
    .footer {{ position: fixed; bottom: 10px; width: 100%; text-align: center; color: rgba(255,255,255,0.3); font-size: 10px; letter-spacing: 1px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC (AI Initialization) ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Extract URL params for logic
email = st.query_params.get("email", None)
question_key = st.query_params.get("question", None)

if "conversation" not in st.session_state:
    if email:
        st.session_state.conversation = DeepConversation(st.session_state.session_id, email)
        initial_text = initialize_deep_conversation(email)
    else:
        st.session_state.conversation = LiteConversation(st.session_state.session_id)
        initial_text = initialize_lite_conversation()

    # If a specific question was passed in URL, override initial prompt
    if question_key and question_key in (lite_questions if not email else deep_questions):
        initial_text = lite_questions.get(question_key) or deep_questions.get(question_key)

    # Optional: If you want Gaia to start with a greeting
    if not st.session_state.conversation.logs:
        st.session_state.conversation.assistant("What would you like to know?")

# --- 4. RENDER UI ---
st.title("Gaia AI")

# Display historical messages using custom HTML bubbles
for msg in st.session_state.conversation.logs:
    role = msg["role"]
    content = msg["content"]

    if role == "assistant":
        st.markdown(f"""
        <div class="assistant-block">
            <div><img src="data:image/png;base64,{GAIA_IMG}" class="avatar"><span class="gaia-name">Gaia</span></div>
            <div class="chat-bubble assistant">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    elif role == "user":
        st.markdown(f"""
        <div class="chat-row chat-right">
            <div class="chat-bubble user">{content}</div>
        </div>
        """, unsafe_allow_html=True)

# --- 5. CHAT INPUT & PROCESSING ---
if prompt := st.chat_input("Ask Gaia anything..."):
    # Append user message to the backend conversation object
    st.session_state.conversation.user(prompt)
    st.rerun()

# Handle AI Response Turn
if st.session_state.conversation.logs and st.session_state.conversation.logs[-1]["role"] == "user":
    # Show Thinking Dots
    with st.container():
        st.markdown(f"""
        <div class="assistant-block">
            <div><img src="data:image/png;base64,{GAIA_IMG}" class="avatar"><span class="gaia-name">Gaia is thinking...</span></div>
            <div class="thinking-container"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
        </div>
        """, unsafe_allow_html=True)

        # Call your actual AI logic
        # Replace this with your actual streaming or direct LLM call
        # e.g., response = llm_chat(prompt)
        time.sleep(1.5)  # Simulating latency
        response = "I'm processing your request regarding sustainability..."

        # Save response to backend
        st.session_state.conversation.assistant(response)
        st.rerun()

# Footer
st.markdown("""<div class="footer">GAIA MAY MAKE MISTAKES. VERIFY IMPORTANT INFO. © 2026 GROUNDED WORLD.</div>""",
            unsafe_allow_html=True)