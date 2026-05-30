import base64
import time
import uuid

import streamlit as st
import streamlit.components.v1 as components

from conversation_util import initialize_deep_conversation, initialize_lite_conversation
from core.helper.interface import GAIA_IMG, streaming_logo_interface
from core.vault.conversation import DeepConversation, LiteConversation

st.set_page_config(page_title="Custom Chat UI", layout="wide")
# --- Custom CSS for alignment ---
st.markdown("""
<style>

* {
  box-sizing: border-box;
}
/* Targets the main background layer */
[data-testid="stAppViewContainer"], 
.main {
    background: transparent !important;
    background-color: transparent !important;
}

/* Targets the header/top bar */
[data-testid="stHeader"] {
    background: transparent !important;
}

/* Change this: */
div[data-testid="stBottomBlockContainer"] {
    background: transparent !important; /* Was #0E1117 */
    padding-top: 0px !important; 
}
html, body, [class*="css"] {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
}
/* Top Fade */
.main::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 100px;
    /* Match this gradient to your app's background color */
    z-index: 99;
    pointer-events: none; /* Allows you to click 'through' the fade */
}

/* Bottom Fade - Positioned above the input */
.main::after {
    content: "";
    position: fixed;
    bottom: 80px; /* Adjust this to where your chat input top edge sits */
    left: 0;
    right: 0;
    height: 100px; /* Height of the fade effect */
    z-index: 1; /* Lower than the chat input */
    pointer-events: none;
}

/* Adjust padding so the first/last messages aren't permanently hidden */
.stMainBlockContainer {
    padding-top: 80px !important;
    padding-bottom: 120px !important;
}
/* ─────────────────────────
   CHAT LAYOUT
───────────────────────── */

.chat-row {
  display: flex;
  margin-bottom: 12px;
}

.chat-right {
  justify-content: flex-end;
}

.assistant-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 80%; /* Increased slightly for better readability on long text */
  align-items: flex-start; /* This prevents the bubble from stretching full-width */
}

.chat-bubble {
  display: inline-block; /* Ensures the bubble wraps the text tightly */
  position: relative;
    z-index: 1;
  width: auto;           /* Allows width to be defined by content */
  max-width: 80%;
  padding: 12px 16px;
  font-size: 14px;
  border-radius: 16px;
  white-space: pre-wrap;
  word-wrap: break-word; /* Prevents long words from breaking the layout */

  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 6px 24px rgba(0,0,0,0.4);
}
/* ─────────────────────────
   AVATAR + NAME
───────────────────────── */

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  margin-right: 8px;
  box-shadow: 0 0 10px;
}

.name {
  font-size: 12px;
  font-weight: 600;
  color: #6BB6FF;
}

/* ─────────────────────────
   CHAT BUBBLES
───────────────────────── */


/* Assistant */
.chat-bubble.assistant {
  background: rgba(255, 255, 255, 0.05); /* Lighter glass effect */
  color: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px); /* Stronger blur for readability */
  border-bottom-left-radius: 6px;
}
/* FINAL OVERRIDE FOR TRANSPARENCY */
.stApp, .main, .stAppHeader, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: transparent !important;
    background: transparent !important;
}
/* User */
.chat-bubble.user {
  background: rgba(30,144,255,0.12);
  color: white;
  border-bottom-right-radius: 6px;

  border: 1px solid rgba(30,144,255,0.3);
  box-shadow: 0 0 14px rgba(30,144,255,0.2);
}
/* Target the wrapper around the input */
div[data-testid="stChatInput"] {
  border-radius: 20px;
  backdrop-filter: blur(8px);
  background-color: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(107, 182, 255, 0.2);
  transition: all 0.3s ease-in-out;
  animation: pulse-glow 4s infinite ease-in-out;
  z-index: 100 !important; /* Higher than the fade (1) */
  bottom: 20px !important; 
  background-color: #0E1117 !important; /* Give it a solid background or heavy blur */
  backdrop-filter: blur(20px);
}

/* Style the text area inside */
div[data-testid="stChatInput"] textarea {
  color: white !important;
  background-color: transparent !important;
}

/* Focus state: When the user clicks to type */
div[data-testid="stChatInput"]:focus-within {
  border-color: #6BB6FF !important;
  box-shadow: 0 0 15px rgba(107, 182, 255, 0.6) !important;
  transform: translateY(-2px);
}

/* The "Breathing" Animation */
@keyframes pulse-glow {
  0% {
    box-shadow: 0 0 5px rgba(107, 182, 255, 0.1);
    border-color: rgba(107, 182, 255, 0.2);
  }
  50% {
    box-shadow: 0 0 15px rgba(107, 182, 255, 0.3);
    border-color: rgba(107, 182, 255, 0.5);
  }
  100% {
    box-shadow: 0 0 5px rgba(107, 182, 255, 0.1);
    border-color: rgba(107, 182, 255, 0.2);
  }
}

/* Force the main container to be a flexbox that spans the full height */
[data-testid="stAppViewContainer"] > .main {
    display: flex;
    flex-direction: column;
}

.footer-disclaimer {
  position: fixed !important;
  bottom: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 40px; 
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  
  backdrop-filter: none !important;
  border-top: none !important;
  
  z-index: 999;
}

.footer-disclaimer p {
  /* White with 40% opacity for a professional, integrated look */
  color: rgba(255, 255, 255, 0.4) !important; 
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 9px; 
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin: 1px 0 !important;
  padding: 0;
  text-align: center;
}

/* Position the chat input so it doesn't overlap the text */
div[data-testid="stChatInput"] {
  bottom: 40px !important; /* Raised slightly to make room for the seamless footer */
  background-color: rgba(255, 255, 255, 0.03) !important;
}
.name {
  font-size: 11px;
  font-weight: 500;
  color: #FFFFFF !important; /* Pure white, 100% opaque */
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

div[data-testid="stChatInput"] {
  bottom: 0px !important; /* Matches footer height */
  background-color: transparent !important;
}

/* ── Thinking Dots ── */
.thinking-container {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(40, 44, 52, 0.4);
  border-radius: 16px;
  border-bottom-left-radius: 6px;
  width: fit-content;
  margin-bottom: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #FFFFFF;
  border-radius: 50%;
  display: inline-block;
  animation: dotPulse 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

/* Optional: Smooth out the scroll behavior */
html {
    scroll-behavior: smooth;
}
/* The keyframes you provided */
@keyframes dotPulse {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.25;
  }
  40% {
    transform: scale(1);
    opacity: 0.8;
  }
}
/* 1. THE CRUNCHED GRADIENT PANEL */
div[data-testid="stBottom"] {
    background: linear-gradient(
        to bottom,
        rgba(14, 17, 23, 0) 0%,       
        rgba(14, 17, 23, 0.2) 15%,    /* Lightened significantly */
        rgba(14, 17, 23, 0) 30%       /* Fades to fully transparent */
    ) !important;

    padding-top: 40px !important; 
    
    /* The Mask - Tightened to match the background */
    mask-image: linear-gradient(
        to bottom,
        rgba(0, 0, 0, 0) 0%, 
        rgba(0, 0, 0, 1) 25%          /* Text becomes fully opaque faster */
    );
    -webkit-mask-image: linear-gradient(
        to bottom,
        rgba(0, 0, 0, 0) 0%, 
        rgba(0, 0, 0, 1) 25%
    );

    pointer-events: none;
    z-index: 100;
}

/* 2. THE INTERNAL CONTAINER - Clean background */
div[data-testid="stBottomBlockContainer"] {
    background: #0E1117 !important; /* Ensure the base is solid behind the input */
    padding-top: 0px !important; 
}

/* 3. THE INTERACTIVE INPUT BOX */
div[data-testid="stChatInput"] {
    pointer-events: auto !important;
    background-color: rgba(255, 255, 255, 0.05) !important; /* Glass effect instead of #1E232D */
    backdrop-filter: blur(10px);
    border: 1px solid rgba(107, 182, 255, 0.2) !important;
    border-radius: 20px;
    z-index: 1001 !important;
    
    /* Tightened shadow for a smaller footprint */
    box-shadow: 0 -10px 20px rgba(0, 0, 0, 0.5);
}
</style>
""", unsafe_allow_html=True)
# --- GLOBAL INTERACTIVE DOT GRID ---
ASSISTANT_AVATAR = "gaia.png"
st.session_state.voice = None
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64_image("gaia.png")


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

    # Optional: If you want Gaia to start with a greeting
    if len(st.session_state.conversation.logs) == 1:
        st.session_state.conversation.assistant("What would you like to know?")


# then:

# --- Display messages ---
# Render messages
for msg in st.session_state.conversation.logs:
    if msg["role"] == "assistant":
        st.markdown(f"""
        <div class="assistant-block">
        <div>
            <img src="data:image/png;base64,{img_base64}" class="avatar">
            <span style="font-size: 12px;">Gaia</span>
        </div>
        <div class="chat-bubble assistant">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    elif msg["role"] == 'user':
        st.markdown(f"""
        <div class="chat-row chat-right">
            <div class="chat-bubble user">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

streaming_logo_interface(None)

st.markdown("""
<div class="footer-disclaimer">
  <p>Gaia may make mistakes. Verify important information.</p>
  <p>© 2026 Grounded World. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)