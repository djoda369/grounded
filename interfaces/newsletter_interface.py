import pandas as pd
import streamlit as st

from core.gpt.chatgpt import llm_chat
from core.gpt.history import History
from core.helper.files import json_read_file

CSV_FILE = "../communication/data/gaia_slack.csv"
JSON_FILE = "../communication/data/weekly_summaries.json"


if __name__ == "__main__":

    if "channels" not in st.session_state:
        # Step 1: Read the CSV file
        df = pd.read_csv(CSV_FILE)
        # Step 2: Fetch and store messages
        st.session_state.channels = {}
        for _, row in df.iterrows():
            category = row["Category"]
            channel = row["Channel"]
            channel_id = row["ID"]
            st.session_state.channels[channel_id] = category + " - " + channel

    st.title("Slack Channel Selector")

    # Dropdown to select a Slack channel
    selected_channel = st.selectbox(
        "Select a Slack channel:", options=list(st.session_state.channels.values())
    )

    if selected_channel:
        selected_channel_id = None
        for key in st.session_state.channels:
            if selected_channel == st.session_state.channels[key]:
                selected_channel_id = key
                break
        if selected_channel_id:
            st.markdown(f"Selected channel: **{st.session_state.channels[selected_channel_id]}**")

            # Text box to input customer information
            customer_info = st.text_area("Enter customer information:")

            # Button to show a message
            if st.button("Submit"):
                if customer_info:
                    with st.spinner("Loading..."):
                        json_data = json_read_file(JSON_FILE)
                        print(json_data)
                        newsletter = json_data[selected_channel_id]
                        history = History()
                        history.user("Newsletter: " + newsletter)
                        history.user("Customer: " + customer_info)
                        history.system("Customize the Newsletter to highlight the most relevant aspects to customer.")
                        history.system("In the footer mention that this newsletter was written by Gaia from GroundedWorld.")
                        st.markdown(llm_chat(history))
                else:
                    st.error("Please enter customer information before submitting.")