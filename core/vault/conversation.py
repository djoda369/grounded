import os

import rootpath
from pydantic import Field, BaseModel

from core.gpt.chatgpt import llm_strict
from core.gpt.history import History
from core.vault.json_vault import JSONVault
from path import DETECTED_PATH


class SummarizeConversation(BaseModel):
    summary: str = Field(..., description="Summarize the key points of the conversation so far.")


class Conversation(History):

    def __init__(self, id: str, folder: str = None):
        super().__init__()
        if folder:
            path = os.path.join(DETECTED_PATH, "data", "conversation", folder).replace("\\", "/")
        else:
            path = os.path.join(DETECTED_PATH, "data", "conversation").replace("\\", "/")
        self.vault = JSONVault(id, path)
        self.logs = self.vault.get("logs", [])

    def add(self, role, message):
        super().add(role, message)
        self.vault.set("logs", self.logs)

        
class LiteConversation(Conversation):

    def __init__(self, id: str):
        super().__init__(id, "lite")
        self.email_requested = self.vault.get("email_requested", False)
        self.got_email = self.vault.get("got_email", self.vault.get("got_emal", False))

    def has_email(self):
        return self.got_email

    def set_has_email(self, has_email):
        self.got_email = has_email
        self.vault.set("got_email", self.got_email)

    def is_requested(self):
        return self.email_requested

    def set_requested(self, value):
        self.email_requested = value
        self.vault.set("email_requested", self.email_requested)


class DeepConversation(Conversation):

    def __init__(self, id: str, email: str = None):
        super().__init__(id, "deep")
        self.email = self.vault.get("email", email)
        print(self.email)
        if email:
            self.email = email
            self.vault.set("email", email)

    def get(self, key):
        return self.vault.get(key, None)


def summarize(conversation: Conversation):
    answer = llm_strict(conversation, "gpt-4o", SummarizeConversation)
    return answer.summary


if __name__ == "__main__":
    conversation = Conversation('zeeuwed')
    conversation.system("Hello How are you doing?")
    print(summarize(conversation))
