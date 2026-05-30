
import streamlit

from core.gpt.history import History
from core.helper.interface import streaming_logo_interface


if __name__ == "__main__":
    company_name = "Hello, I'm Gaia."
    emoji = "🌱"
    company_id = "fireflies"

    if "history" not in streamlit.session_state:
        streamlit.session_state.history = History()
        streamlit.session_state.history.assistant("What would you like to know?")

    # Main program logic (call this function when you want to start the thread)
    try:
        streaming_logo_interface(company_id)
    except KeyboardInterrupt:
        print("Program interrupted.")
