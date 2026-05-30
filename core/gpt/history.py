from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class History:

    def __init__(self):
        self.logs = []

    def system(self, message):
        self.add("system", message)

    def assistant(self, message):
        self.add("assistant", message)

    def user(self, message):
        self.add("user", message)

    def add(self, role, message):
        self.logs.append({'role': role, "content": message})

    def count(self):
        return len(self.logs)

    def extend(self, other):
        for element in other.logs:
            self.logs.append(element)


def langchain_history(history: History):
    logs = []
    for log in history.logs:
        if log["role"] == "user":
            logs.append(HumanMessage(log["content"]))
        elif log["role"] == "assistant":
            logs.append(AIMessage(log["content"]))
        elif log["role"] == "system":
            logs.append(SystemMessage(log["content"]))
    return logs
