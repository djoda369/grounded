import os

from pydantic import BaseModel

from core.gpt.history import History

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    OpenAIEmbeddings = None

load_dotenv()

openai_client = None
openai_embeddings = None


def get_openai_client():
    global openai_client
    if openai_client is not None:
        return openai_client
    if OpenAI is None:
        raise RuntimeError("The openai package is not installed.")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for LLM calls.")
    openai_client = OpenAI(api_key=api_key)
    return openai_client


def get_openai_embeddings():
    global openai_embeddings
    if openai_embeddings is not None:
        return openai_embeddings
    if OpenAIEmbeddings is None:
        raise RuntimeError("The langchain_openai package is not installed.")
    openai_embeddings = OpenAIEmbeddings()
    return openai_embeddings


def llm_question(query):
    logs = History()
    logs.user(query)
    answer = llm_chat(logs)
    return answer


def llm_chat(message_log: History, model_name: str = "gpt-4o"):
    # Use OpenAI's ChatCompletion API to get the chatbot's response
    response = get_openai_client().chat.completions.create(
        model=model_name,  # The name of the OpenAI chatbot model to use
        messages=message_log.logs,   # The conversation history up to this point, as a list of dictionaries
        max_tokens=3000,        # The maximum number of tokens (words or subwords) in the generated response
        stop=None,              # The stopping sequence for the generated response, if any (not used here)
        temperature=0.0,        # The "creativity" of the generated response (higher temperature = more creative)
    )

    # Find the first response from the chatbot that has text in it (some responses may not have text)
    for choice in response.choices:
        if "text" in choice:
            return choice.text

    # If no response with text is found, return the first response's content (which may be empty)
    return response.choices[0].message.content


def llm_stream(history, model_name: str = "gpt-4o"):

    # Initialize the stream
    stream = get_openai_client().chat.completions.create(
        model=model_name,  # Adjust model as needed
        messages=history.logs,
        stream=True  # Enable streaming
    )

    return stream


def llm_strict(history: History, model_name: str, base_model: type):
    completion = get_openai_client().beta.chat.completions.parse(
        model=model_name,
        messages=history.logs,
        response_format=base_model,
    )

    event = completion.choices[0].message.parsed
    return event


def process_stream(stream, openai=True):
    assistant_message = ""
    # Stream chunks and concatenate them
    for chunk in stream:
        if openai:
            if chunk.choices[0].delta.content is not None:
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    assistant_message += choice.delta.content
                yield assistant_message
        else:
            print(chunk)
            if chunk["answer"] is not None:
                assistant_message += chunk["answer"]
            yield assistant_message


def llm_summarize(text: str, instructions: str = "Summarize into one paragraph"):
    history = History()
    history.system(text)
    history.user(instructions)
    return llm_chat(history)
