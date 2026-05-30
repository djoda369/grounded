import string
import time

import streamlit as st

from core.gpt.chatgpt import llm_stream, process_stream
from core.gpt.history import History


def find_new_word(previous, current):
    if previous == current:
        return None

    translator = str.maketrans('', '', string.punctuation)
    previous_normalized = previous.translate(translator)
    current_normalized = current.translate(translator)

    # Split the strings into words
    previous_words = set(previous_normalized.split())
    current_words = set(current_normalized.split())

    # Find the word(s) in current but not in previous
    new_words = current_words - previous_words
    return new_words


def show_assistant():
    with st.spinner("Thinking..."):
        stream = llm_stream(st.session_state.history)
        print(stream)
        answers = process_stream(stream)
        chunk = ""
        old_chunk = ""
        for chunk in answers:
            print(chunk)
            added_words = find_new_word(old_chunk, chunk)
            print("added", added_words)
            if added_words:
                old_chunk = old_chunk + " "
                new_word = added_words.pop()
                n_letters = len(new_word)
                time_per_word = 0.2
                time_per_letter = time_per_word / n_letters
                for letter in new_word:
                    st.session_state.message.title(old_chunk + letter)  # Update progressively
                    time.sleep(time_per_letter)
                    old_chunk += letter
            else:
                old_chunk = chunk

        st.session_state.history.assistant(chunk)  # Save final message in history
        return chunk


if __name__ == "__main__":

    st.set_page_config(
        page_title="Gaia - GroundedWorld",
        page_icon="🌱",
        layout="wide",
    )

    if "message" not in st.session_state:
        st.session_state.message = st.empty()
        st.session_state.answer = st.empty()

    if "history" not in st.session_state:
        st.session_state.history = History()
        st.session_state.history.system("Your name is Gaia, you are a marketing assistant for GroundedWorld.")
        st.session_state.history.system("Welcome the user and role-play as Gaia and use one emoji in your response.")
        st.session_state.chunk = show_assistant()
        st.session_state.turn = "user"

    response = st.session_state.answer.chat_input("...")
    if response and st.session_state.turn == "user":
        print("text from user", response)
        st.session_state.history.user(response)
        st.session_state.history.system("Give a brief response to the user from Gaia's perspective:")
        st.session_state.turn = "assistant"

    if st.session_state.turn == "assistant":
        st.session_state.chunk = show_assistant()
        st.session_state.turn = "user"

    st.session_state.message.title(st.session_state.chunk)
