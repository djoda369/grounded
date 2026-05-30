import streamlit as st

from templates.bcorp import check_bcorp_status
from templates.meeting_data import extract_product_recommendation, extract_article_suggestions, extract_case_studies, \
    extract_meeting_takeaways, summarize_meeting, find_faq_points
from templates.planetpercent import check_planet_percent


def generate_email_html(data):
    html_template = f"""
    <html>
    <head>
        <title>Gaia Meeting Recap</title>
    </head>
    <body>
        <h1>Important: Gaia meeting recap & next steps in your {data['gaia_sql1_specific_result']} journey</h1>
        <p>Hi {data['firstname']},</p>
        <p>Thanks for taking the time to engage with Gaia today. We hope you found the session insightful and valuable for exploring how {data['gaia_sql1_topic']} can make a meaningful impact.</p>

        <h2>Meeting Recap: Your Goals and Pain Points</h2>
        <p>Gaia shared that your primary objectives are to:</p>
        <ul>
            <li>{data['gaia_sql1_objective_1']}</li>
            <li>{data['gaia_sql1_objective_2']}</li>
            <li>{data['gaia_sql1_objective_3']}</li>
        </ul>
        <p>She also noted a few specific challenges you’re facing:</p>
        <ul>
            <li>{data['gaia_sql1_pain_point_1']}</li>
            <li>{data['gaia_sql1_pain_point_2']}</li>
            <li>{data['gaia_sql1_pain_point_3']}</li>
        </ul>

        <h2>Getting Grounded</h2>
        <p>To give you a better sense of how we can help, here are some examples from our past work in {data['industry']} that address challenges similar to yours:</p>
        <ul>
            <li>{data['gaia_sql1_case_study_1']}</li>
            <li>{data['gaia_sql1_case_study_2']}</li>
        </ul>

        <h2>Further Reading to Support Your Goals</h2>
        <ul>
            <li><b>{data['gaia_sql1_article_title_1']}</b>: {data['gaia_sql1_article_description_1']}</li>
            <li><b>{data['gaia_sql1_article_title_2']}</b>: {data['gaia_sql1_article_description_2']}</li>
        </ul>

        <h2>Want to Learn More?</h2>
        <ul>
            <li>{data['gaia_sql1_faq_1']}</li>
            <li>{data['gaia_sql1_faq_2']}</li>
            <li>{data['gaia_sql1_faq_3']}</li>
            <li>{data['gaia_sql1_faq_4']}</li>
            <li>{data['gaia_sql1_faq_5']}</li>
        </ul>

        <h2>Our Suggested Solution for You</h2>
        <p>Based on your requirements, we believe that our {data['gaia_sql1_grounded_product']} could be a strong match for you. {data['grounded_product_benefits']}</p>

        <h2>Next Steps: Let’s Talk Strategy</h2>
        <p>We’d love to arrange a call with our co-founders, Phil White & Heidi Schoeneck, to discuss how we can further support your ambitions. Please feel free to schedule a time that works best for you here: [Link to Scheduling Tool]</p>

        <p>Thanks again for your interest. Please don’t hesitate to reach out with any questions in the meantime.</p>

        <p>Warm regards,</p>
        <p>Matt Deasy<br>Director of Growth and Engagement<br>Grounded</p>
    </body>
    </html>
    """
    return html_template


def process_transcript(meeting_transcript):
    company_data = {}

    # Step 1: Summarize the meeting
    meeting_summary = summarize_meeting(meeting_transcript)

    # Step 2: Extract meeting takeaways
    company_data = extract_meeting_takeaways(company_data, meeting_summary)

    # Step 3: Extract case studies
    company_data = extract_case_studies(company_data, meeting_summary)

    # Step 4: Extract article suggestions
    company_data = extract_article_suggestions(company_data, meeting_summary)

    # Step 5: Extract product recommendations
    company_data = extract_product_recommendation(company_data, meeting_summary)

    company_data = find_faq_points(company_data, meeting_summary)

    # TODO set name
    company_name: str = None
    if company_name:
        company_data["b_corp_certified"] = check_bcorp_status(company_name)
        company_data["n1__for_the_planet"] = check_planet_percent(company_name)

    print(company_data)

    return company_data


if __name__ == "__main__":

    # Initialize session state for company data
    if "company_data" not in st.session_state:
        st.session_state.company_data = {}

    # Title
    st.title("Meeting Transcript Analyzer")

    # Multiline input for meeting transcript
    meeting_transcript = st.text_area("Enter the meeting transcript here:", height=200)

    # Button to trigger analysis
    if st.button("Analyze Transcript"):
        if not meeting_transcript.strip():
            st.warning("Please enter a valid meeting transcript before analyzing.")
        else:
            with st.spinner("Analyzing the meeting transcript..."):
                st.session_state.company_data = process_transcript(meeting_transcript)
            st.success("Analysis complete!")

    # Display extracted information
    st.subheader("Extracted Company Data")
    if st.session_state["company_data"]:
        for key, value in st.session_state.company_data.items():
            st.text_input(key, value)
    else:
        st.info("No data to display yet. Please analyze a transcript.")

    st.subheader("Email")
    st.html(generate_email_html(st.session_state.company_data))
