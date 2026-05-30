
import streamlit as st

from core.helper.crm import get_contact_id_by_email, get_company_data, set_custom_properties, prepare_email_2_user, \
    prepare_email_1_user, create_user
from core.vault.conversation import DeepConversation, LiteConversation
from templates.meeting_data import hubspot_1_column_names, analyze_second_meeting, analyze_first_meeting

roleplay_prompt = "Roleplay as Gaia an marketing assistant from grounded (always write grounded not Grounded) that helps clients understand the services of grounded.world."

lite_questions = {
    "q1": "What are the biggest sustainability issues and challenges faced by the fashion, textile, and apparel industry?",
    "q2": "How can the fashion, textile, and apparel industry reduce its carbon emissions?",
    "q3": "Why is circularity so important for the fashion industry?",
    "q4": "Tell me the different ways that consumers expect fashion brands and retailers to be more sustainable.",
    "q5": "Explain some of the labor laws and practices that are being violated around the world by the fashion industry.",
    "q6": "What are the most important pieces of policy and legislation that are having a material impact on the fashion industry today?",
    "q7": "What is an intention- action gap and how do i quantify it?",
    "q8": "How can I make my brand or business more sustain-agile?",
    "q9": "How can we get better at activating brand purpose and sustainability at retail?",
    "q10": "Explain to me what a flywheel of impact is and how it works to scale revenue and impact?"
}

deep_questions = {
    "q1": "gaia_sql1_faq_1",
    "q2": "gaia_sql1_faq_2",
    "q3": "gaia_sql1_faq_3",
    "q4": "gaia_sql1_faq_4",
    "q5": "gaia_sql1_faq_5",
    "q6": "gaia_sql1_faq_6"
}


def initialize_company_data(email: str):
    contact_id = get_contact_id_by_email(email)
    if not contact_id:
        return
    return get_company_data(contact_id)


def initialize_conversation_company_data(conversation: DeepConversation, company_data: dict):
    if company_data:
        for key, value in company_data.items():
            if key in hubspot_1_column_names:
                conversation.system("Customer Information " + str(hubspot_1_column_names[key]) + ": " + str(value))


def initialize_deep_conversation(email):
    st.session_state.company_data = initialize_company_data(email)
    initialize_conversation_company_data(st.session_state.conversation, st.session_state.company_data)
    st.session_state.conversation.system(roleplay_prompt)

    if not st.session_state.company_data:
        return


def initialize_lite_conversation():
    st.session_state.conversation.system(roleplay_prompt)


def lite_function(email: str, conversation: LiteConversation):
    contact_id = create_user(email)
    company_data = analyze_first_meeting(conversation)
    set_custom_properties(contact_id, company_data)
    prepare_email_1_user(contact_id)


def deep_function(conversation: DeepConversation):
    contact_id = get_contact_id_by_email(conversation.email)
    company_data = get_company_data(contact_id)
    company_data = analyze_second_meeting(conversation, company_data)
    set_custom_properties(contact_id, company_data)
    prepare_email_2_user(contact_id)
