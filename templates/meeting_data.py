import os

import rootpath
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pydantic import Field, BaseModel

from core.gpt.chatgpt import llm_strict
from core.gpt.document import get_pages
from core.gpt.history import History
from path import DETECTED_PATH

hubspot_1_column_names = {
    "gaia_sql1_topic": "Topic",
    "gaia_sql1_objective_1": "Objective 1",
    "gaia_sql1_objective_2": "Objective 2",
    "gaia_sql1_objective_3": "Objective 3",
    "gaia_sql1_pain_point_1": "Pain Point 1",
    "gaia_sql1_pain_point_2": "Pain Point 2",
    "gaia_sql1_pain_point_3": "Pain Point 3",
    "gaia_sql1_specific_result": "Company specific Result",
    "gaia_sql1_case_study_1": "Case Study 1",
    "gaia_sql1_case_study_2": "Case Study 2",
    "gaia_sql1_article_title_1": "Article Title 1",
    "gaia_sql1_article_description_1": "Article Description 1",
    "gaia_sql1_article_title_2": "Article Title 2",
    "gaia_sql1_article_description_2": "Article Description 2",
    "gaia_sql1_grounded_product": "Grounded Product",
    "grounded_product_benefits": "Product Benefits"
}


class MeetingSummary(BaseModel):
    summary: str = Field(..., description="Summary of the meeting stating the most important points.")


class MeetingObjectives(BaseModel):
    first_objective: str = Field(...,
                                 description="Primary objective from the meeting that is clarified with the client.")
    second_objective: str = Field(...,
                                  description="Secondary major objective from the meeting that has been identified for the client.")
    third_objective: str = Field(...,
                                 description="Additional objective that has been mentioned in the meeting with the client.")


class ClientFAQ(BaseModel):
    first_FAQ: str = Field(..., description="First potential question the client might have about GroundedWorld")
    second_FAQ: str = Field(..., description="Second potential question the client might have about GroundedWorld")
    third_FAQ: str = Field(..., description="Third potential question the client might have about GroundedWorld")
    fourth_FAQ: str = Field(..., description="Fourth potential question the client might have about GroundedWorld")
    fifth_FAQ: str = Field(..., description="Fifth potential question the client might have about GroundedWorld")



class MeetingPainpoints(BaseModel):
    first_painpoint: str = Field(...,
                                 description="Primary pain point from the meeting that is clarified with the client.")
    second_painpoint: str = Field(...,
                                  description="Secondary major pain point from the meeting that has been identified for the client.")
    third_painpoint: str = Field(...,
                                 description="Additional pain point that has been mentioned in the meeting with the client.")


class MeetingMeta(BaseModel):
    topic_conversation: str = Field(...,
                                    description="Major topic of conversation during the meeting that we can reference in future emails.")
    industry: str = Field(..., description="Industry that our client is currently operating in.")
    specific_result: str = Field(...,
                                 description="Specific Result that is mentioned as the outcome of the collaboration with the client.")


class CaseStudySuggestion(BaseModel):
    description: str = Field(...,
                             description="A concise overview of a previous case study that is similar to the company's current situation, highlighting key aspects of the case that are relevant.")


#    result: str = Field(..., description="An explanation of how the approach or solutions from the case study can address the company's objective or pain points, detailing the potential benefits or resolutions.")


class ArticleSuggestion(BaseModel):
    title: str = Field(...,
                       description="Title of article that is referenced.")
    description: str = Field(...,
                             description="Short description of article that is being referenced.")

    # summary: str = Field(..., description="A condensed version of a related article that addresses the company's specific pain points or objectives, highlighting the most relevant insights.")
    # link: str = Field(..., description="Direct link to the full article, provided for further reading and reference.")


class ProductRecommendation(BaseModel):
    grounded_product: str = Field(..., description="Name of the recommended GroundedWorld product to the client.")
    product_benefits: str = Field(..., description="Short list of product benefits for the client.")



class EmailTemplate(BaseModel):
    title: str = Field(..., description="Title to be send to the client as a folowup from the meeting they just had.")
    message: str = Field(...,
                         description="Write HTML email message that will be received by the client summing up the experience and advice from the articles and case studies that apply to their company.")


def summarize_meeting(history: History):
    return llm_strict(history, "gpt-4o", MeetingSummary)


def extract_first_meeting_takeaways(company_data: dict, meeting_summary: MeetingSummary):
    history = History()
    history.system("Meeting summary: " + meeting_summary.summary)

    if "gaia_sql1_topic" not in company_data:
        meeting_meta: MeetingMeta = llm_strict(history, "gpt-4o", MeetingMeta)
        if "gaia_sql1_topic" not in company_data:
            company_data["gaia_sql1_topic"] = meeting_meta.topic_conversation

    if "gaia_sql1_objective_1" not in company_data or "gaia_sql1_objective_2" not in company_data or "gaia_sql1_objective_3" not in company_data:
        meeting_objectives: MeetingObjectives = llm_strict(history, "gpt-4o", MeetingObjectives)
        if "gaia_sql1_objective_1" not in company_data:
            company_data["gaia_sql1_objective_1"] = meeting_objectives.first_objective
        if "gaia_sql1_objective_2" not in company_data:
            company_data["gaia_sql1_objective_2"] = meeting_objectives.second_objective
        if "gaia_sql1_objective_3" not in company_data:
            company_data["gaia_sql1_objective_3"] = meeting_objectives.third_objective

    if "gaia_sql1_pain_point_1" not in company_data or "gaia_sql1_pain_point_2" not in company_data or "gaia_sql1_pain_point_3" not in company_data:
        meeting_painpoints: MeetingPainpoints = llm_strict(history, "gpt-4o", MeetingPainpoints)
        if "gaia_sql1_pain_point_1" not in company_data:
            company_data["gaia_sql1_pain_point_1"] = meeting_painpoints.first_painpoint
        if "gaia_sql1_pain_point_2" not in company_data:
            company_data["gaia_sql1_pain_point_2"] = meeting_painpoints.second_painpoint
        if "gaia_sql1_pain_point_3" not in company_data:
            company_data["gaia_sql1_pain_point_3"] = meeting_painpoints.third_painpoint

    return company_data


def extract_second_meeting_takeaways(company_data: dict, meeting_summary: MeetingSummary):
    history = History()
    history.system("Meeting summary: " + meeting_summary.summary)

    if "gaia_sql1_topic" not in company_data or "industry" not in company_data or "specific_result" not in company_data:
        meeting_meta: MeetingMeta = llm_strict(history, "gpt-4o", MeetingMeta)
        if "gaia_sql1_topic" not in company_data:
            company_data["gaia_sql1_topic"] = meeting_meta.topic_conversation
        if "industry" not in company_data:
            company_data["industry"] = meeting_meta.industry
        if "specific_result" not in company_data:
            company_data["gaia_sql1_specific_result"] = meeting_meta.industry

    if "gaia_sql1_objective_1" not in company_data or "gaia_sql1_objective_2" not in company_data or "gaia_sql1_objective_3" not in company_data:
        meeting_objectives: MeetingObjectives = llm_strict(history, "gpt-4o", MeetingObjectives)
        if "gaia_sql1_objective_1" not in company_data:
            company_data["gaia_sql1_objective_1"] = meeting_objectives.first_objective
        if "gaia_sql1_objective_2" not in company_data:
            company_data["gaia_sql1_objective_2"] = meeting_objectives.second_objective
        if "gaia_sql1_objective_3" not in company_data:
            company_data["gaia_sql1_objective_3"] = meeting_objectives.third_objective

    if "gaia_sql1_pain_point_1" not in company_data or "gaia_sql1_pain_point_2" not in company_data or "gaia_sql1_pain_point_3" not in company_data:
        meeting_painpoints: MeetingPainpoints = llm_strict(history, "gpt-4o", MeetingPainpoints)
        if "gaia_sql1_pain_point_1" not in company_data:
            company_data["gaia_sql1_pain_point_1"] = meeting_painpoints.first_painpoint
        if "gaia_sql1_pain_point_2" not in company_data:
            company_data["gaia_sql1_pain_point_2"] = meeting_painpoints.second_painpoint
        if "gaia_sql1_pain_point_3" not in company_data:
            company_data["gaia_sql1_pain_point_3"] = meeting_painpoints.third_painpoint

    return company_data


def extract_case_studies(company_data, meeting_summary: MeetingSummary):
    if "gaia_sql1_case_study_1" in company_data and "gaia_sql1_case_study_2" in company_data:
        return company_data

    path = os.path.join(DETECTED_PATH, "templates", "use_cases").replace("\\", "/")
    new_db = FAISS.from_documents(get_pages(path), OpenAIEmbeddings())

    for index, document in enumerate(new_db.similarity_search(meeting_summary.summary, k=2)):
        if f"gaia_sql1_case_study_{index+1}" in company_data:
            continue
        history = History()
        history.system("Meeting Summary: " + meeting_summary.summary)
        history.system("Case Study: " + document.page_content)
        suggestion = llm_strict(history, "gpt-4o", CaseStudySuggestion)
        company_data[f"gaia_sql1_case_study_{index+1}"] = suggestion.description

    return company_data


def extract_article_suggestions(company_data, meeting_summary: MeetingSummary):
    if "gaia_sql1_article_title_1" in company_data and "gaia_sql1_article_description_1" in company_data and \
            "gaia_sql1_article_title_2" in company_data and "gaia_sql1_article_description_2" in company_data:
        return company_data

    path = os.path.join(DETECTED_PATH, "templates", "articles").replace("\\", "/")
    new_db = FAISS.from_documents(get_pages(path), OpenAIEmbeddings())

    for index, document in enumerate(new_db.similarity_search(meeting_summary.summary, k=2)):
        if f"gaia_sql1_article_title_{index+1}" in company_data and f"gaia_sql1_article_description_{index}" in company_data:
            continue
        history = History()
        history.system("Meeting Summary: " + meeting_summary.summary)
        history.system("Article: " + document.page_content)
        suggestion: ArticleSuggestion = llm_strict(history, "gpt-4o", ArticleSuggestion)
        company_data[f"gaia_sql1_article_title_{index+1}"] = suggestion.title
        company_data[f"gaia_sql1_article_description_{index+1}"] = suggestion.description

    return company_data


def extract_product_recommendation(company_data, meeting_summary: MeetingSummary):
    if "gaia_sql1_grounded_product" in company_data and "grounded_product_benefits" in company_data:
        return company_data

    path = os.path.join(DETECTED_PATH, "templates", "products").replace("\\", "/")
    new_db = FAISS.from_documents(get_pages(path), OpenAIEmbeddings())

    for index, document in enumerate(new_db.similarity_search(meeting_summary.summary, k=1)):
        history = History()
        history.system("Meeting Summary: " + meeting_summary.summary)
        history.system("Article: " + document.page_content)
        suggestion: ProductRecommendation = llm_strict(history, "gpt-4o", ProductRecommendation)
        company_data["gaia_sql1_grounded_product"] = suggestion.grounded_product
        company_data["grounded_product_benefits"] = suggestion.product_benefits

    return company_data


def find_faq_points(company_data, meeting_summary: MeetingSummary):
    history = History()
    history.system("Meeting: " + meeting_summary.summary)
    for key, value in company_data.items():
        history.system(str(key) + ": " + str(value))

    result: ClientFAQ = llm_strict(history, "gpt-4o", ClientFAQ)
    company_data["gaia_sql1_faq_1"] = result.first_FAQ
    company_data["gaia_sql1_faq_2"] = result.second_FAQ
    company_data["gaia_sql1_faq_3"] = result.third_FAQ
    company_data["gaia_sql1_faq_4"] = result.fourth_FAQ
    company_data["gaia_sql1_faq_5"] = result.fifth_FAQ
    return company_data


def analyze_first_meeting(history: History, company_data=None):
    if company_data is None:
        company_data = {}
    meeting_summary: MeetingSummary = summarize_meeting(history)

    company_data = extract_first_meeting_takeaways(company_data, meeting_summary)
    company_data = extract_article_suggestions(company_data, meeting_summary)
    company_data = find_faq_points(company_data, meeting_summary)
    return company_data


def analyze_second_meeting(history: History, company_data=None):
    if company_data is None:
        company_data = {}
    meeting_summary: MeetingSummary = summarize_meeting(history)

    company_data = extract_first_meeting_takeaways(company_data, meeting_summary)
    company_data = extract_second_meeting_takeaways(company_data, meeting_summary)
    company_data = extract_case_studies(company_data, meeting_summary)
    company_data = extract_article_suggestions(company_data, meeting_summary)
    company_data = extract_product_recommendation(company_data, meeting_summary)
    company_data = find_faq_points(company_data, meeting_summary)

    return company_data


if __name__ == "__main__":
    meeting = """Meeting Transcript:

Contact Profile:
Alex Smith is the Marketing Director at EcoSolutions Ltd., a medium-sized company based in San Francisco, CA, specializing in the Renewable Energy industry. Alex recently reached out to GroundedWorld to explore potential strategies for improving their marketing and brand presence in the eco-friendly space.

Meeting Overview: EcoSolutions is currently facing significant challenges in growing their brand awareness within the sustainability sector. The company’s eco-friendly products, although innovative, are not attracting the level of engagement they had anticipated from their target market, and they lack a clear strategy for positioning themselves as leaders in the renewable energy industry.

Pain Points Discussed:

Lack of Effective Branding Strategy:
EcoSolutions has struggled with defining a unique selling proposition (USP) for their eco-friendly products. Despite their commitment to sustainability, they feel their branding does not differentiate them enough in a competitive market.

Low Customer Engagement:
Despite offering a strong product line, EcoSolutions has faced challenges in engaging their customer base, with low interaction rates on social media and limited organic traffic on their website. They have expressed frustration with their current marketing efforts not yielding the desired results.

Difficulty in Educating Consumers about Sustainability Benefits:
Alex noted that there is a significant knowledge gap among their target audience regarding the importance of sustainability. Many potential customers do not fully understand the long-term benefits of renewable energy, which limits the effectiveness of their marketing campaigns.

Need for Better Content Strategy:
EcoSolutions has acknowledged a gap in their content marketing strategy, which lacks a compelling narrative and does not effectively communicate the company’s commitment to sustainability. They want to create more engaging content that resonates with their audience and drives higher conversion rates.

Meeting Objective:
To develop a comprehensive marketing strategy for EcoSolutions Ltd. that addresses their branding challenges, enhances customer engagement, and educates consumers on the benefits of sustainability in renewable energy.

Goals:

Improve brand awareness by establishing EcoSolutions as a thought leader in the renewable energy industry.
Increase customer engagement and website traffic through targeted content marketing and social media strategies.
Educate the target audience on the long-term benefits of eco-friendly products, encouraging more sustainable purchasing decisions.
"""

    history = History()
    history.system(meeting)
    print(analyze_first_meeting(history))