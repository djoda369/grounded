import base64
import html

import streamlit as st

st.set_page_config(page_title="Custom Chat UI", layout="wide")

st.title("Gaia Chat UI")

# --- Custom CSS for alignment ---
st.markdown("""
<style>

.msg-row {
  display: flex;
  flex-direction: column;
  max-width: 50%;
  opacity: 0;
  animation: fadeIn 0.35s ease-out forwards;
}

.msg-row.bot {
  align-self: flex-start;
}

.msg-row.user {
  align-self: flex-end;
  align-items: flex-end;
}

.msg-sender {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
}

.msg-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.msg-sender-name {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
}

.msg-bubble {
  padding: 10px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.7;
}

.msg-row.bot .msg-bubble {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px 18px 18px 4px;
  backdrop-filter: blur(40px) saturate(1.6);
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.msg-row.user .msg-bubble {
  background: rgba(77,168,255,0.08);
  border: 1px solid rgba(77,168,255,0.12);
  border-radius: 18px 18px 4px 18px;
  backdrop-filter: blur(40px) saturate(1.6);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

</style>
""", unsafe_allow_html=True)
# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "What would you like to know?"}]
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64_image("gaia.png")

# then:

# --- Display messages ---
# Render messages
# --- Display messages ---
chat_html = '<div class="chat-container">'

for msg in st.session_state.messages:
    content = html.escape(msg["content"])

    if msg["role"] == "assistant":
        chat_html += f"""
        <div class="msg-row bot">
            <div class="msg-sender">
                <div class="msg-avatar">
                    <img src="data:image/png;base64,{img_base64}">
                </div>
                <div class="msg-sender-name">Gaia</div>
            </div>
            <div class="msg-bubble">{content}</div>
        </div>
        """
    else:
        chat_html += f"""
        <div class="msg-row user">
            <div class="msg-bubble">{content}</div>
        </div>
        """

chat_html += "</div>"

st.markdown(chat_html, unsafe_allow_html=True)
# Input
if prompt := st.chat_input("Ask Gaia anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = "Thanks for reaching out! 🌱"
    st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()