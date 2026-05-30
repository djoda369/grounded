import streamlit as st

from analyzer.cold_email import EmailAnalyzer

# List of common free/public email providers
free_email_domains = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "protonmail.com", "live.com"
}


def is_business_email(email):
    """Check if the email is a business email."""
    print(email)
    if "@" not in email:
        return False
    domain = email.split("@")[1]
    return domain not in free_email_domains


def email_popup():
    # Check for email in the query parameters
    email_field = st.empty()
    button_field = st.empty()
    message_field = st.empty()
    email = st.query_params.get("email", None)  # Extract the first value or None

    # If email is not present, prompt the user to input it
    if not email:
        message_field.warning("Email is required to continue.")

        # Input box to collect the email
        email = email_field.text_input("Please enter your business email address:")

        # Once email is entered, validate it
        if button_field.button("Submit"):
            if email:
                if is_business_email(email):
                    st.query_params["email"] = email
                    email_field.empty()
                    button_field.empty()
                    message_field.empty()
                    return email
                else:
                    message_field.error("Please enter a valid business email address. Free email providers are not allowed.")
            else:
                message_field.error("Please enter a valid email address.")

    else:
        if is_business_email(email):
            email_field.empty()
            button_field.empty()
            message_field.empty()
            return email
        else:
            message_field.error("Free email providers are not allowed. Please use a business email.")

    return None
