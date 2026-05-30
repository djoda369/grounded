from pydantic import BaseModel, Field

from core.gpt.chatgpt import llm_strict
from core.gpt.history import History


class KeyValueModel(BaseModel):
    key: str = Field(..., description="Key name that of new information we found.")
    value: str = Field(..., description="Value of the new information that we found.")


class InformationModel(BaseModel):
    info: list[KeyValueModel] = Field(..., description="Information about text segmented into key value pairs.")


def convert_information(information_model: InformationModel, info=None):
    if info is None:
        info = {}
    for data in information_model.info:
        info[data.key] = data.value
    return info


def add_metadata(text: str, info=None):
    if info is None:
        info = {}
    history = History()
    history.system("Known: " + str(info))
    history.system("New: " + text)
    answers: dict = convert_information(llm_strict(history, "gpt-4o", InformationModel), info)
    return answers


if __name__ == "__main__":
    info = {
        "Name": "Grounded World",
        "Certification": "B Corp certified Business",
        "Focus": "Social innovation and brand activation",
        "Key Services": "Brand purpose articulation, commercial innovation, and social impact services",
        "Target Clients": "Brands, retailers, startups, and nonprofits"
    }
    text = "Grounded World is a B Corp certified social innovation and brand activation agency that focuses on brand purpose, commercial innovation, and social impact. They offer services to brands, retailers, startups, and nonprofits to help articulate purpose, activate brands, and accelerate impact. The agency emphasizes transforming purpose into profit through innovation and behavior change. They provide various resources and frameworks to guide sustainability marketing, social impact strategies, and brand activism."
    answers = add_metadata(text, info)
    for answer in answers:
        print(answer, ": ", answers[answer])