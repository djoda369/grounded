import os

import rootpath
from pydantic import Field, BaseModel

from core.gpt.chatgpt import llm_strict
from core.gpt.document import get_named_history
from core.gpt.history import History
from path import DETECTED_PATH


class HubSpotContactData(BaseModel):
    first_name: str = Field(..., description="The contact's first name as recorded in HubSpot.")
    client_industry: str = Field(..., description="The industry or type of company the client belongs to, providing context on the business sector.")
    topic: str = Field(..., description="The primary discussion topic or theme relevant to the client, derived from the flow (e.g., Sustainability marketing, Social impact marketing).")


class GroundedProductData(BaseModel):
    grounded_product: str = Field(..., description="The GroundedWorld product or service most relevant to the client's needs or interest, as determined through HubSpot data.")
    grounded_product_benefits: str = Field(..., description="A list of key benefits provided by the selected GroundedWorld product or service that address the client's specific challenges or objectives.")


def extract_contact_details(text):
    history = History()
    history.system(text)
    return llm_strict(history, "gpt-4o", HubSpotContactData)


def extract_grounded_product(text):
    path = os.path.join(DETECTED_PATH, "templates", "services").replace("\\", "/")
    history = get_named_history(path, "Service")
    history.system(text)
    return llm_strict(history, "gpt-4o", GroundedProductData)


if __name__ == "__main__":
    contact = """Contact Profile:
Alex Smith is the Marketing Director at EcoSolutions Ltd., a medium-sized company based in San Francisco, CA, specializing in the Renewable Energy industry. Alex recently connected with GroundedWorld to discuss potential strategies in Sustainability Marketing, particularly with an interest in eco-friendly branding solutions.

Alex was last contacted on November 10, 2024 and is an active subscriber in HubSpot’s system. The company address is located at 123 Green Way, San Francisco, CA 94107, and Alex’s preferred contact details are alex.smith@example.com and phone +1-555-1234.

"""
    #print(extract_contact_details(contact))
    print(extract_grounded_product(contact))
