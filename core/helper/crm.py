import os
from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.associations import BatchInputPublicObjectId
from hubspot.crm.contacts import SimplePublicObjectInput, Filter, FilterGroup, PublicObjectSearchRequest

from templates.meeting_data import hubspot_1_column_names

load_dotenv()

# Initialize client
hubspot_client = HubSpot(access_token=os.environ["HUBSPOT_ACCESS_TOKEN_PRODUCTION"])


def get_company_associations_to_notes(company_ids):
    """Retrieve associations between companies and notes."""
    batch_ids = BatchInputPublicObjectId([{'id': str(c)} for c in company_ids])
    return hubspot_client.crm.associations.batch_api.read(
        from_object_type="company",
        to_object_type="note",
        batch_input_public_object_id=batch_ids
    )


def get_note_details(note_id):
    """Fetch the details of a specific note by ID."""
    return hubspot_client.crm.objects.basic_api.get_by_id(
        object_type="note",
        object_id=note_id,
        properties=["hs_note_body", "hs_title"]  # Properties for note content and title
    )


def create_hubspot_customer(email, first_name=None, last_name=None, company=None):
    """
    Creates a new customer in HubSpot using the provided email and optional details.

    Args:
        api_key (str): Your HubSpot API key.
        email (str): The customer's email address (required).
        first_name (str): The customer's first name (optional).
        last_name (str): The customer's last name (optional).
        company (str): The customer's company name (optional).

    Returns:
        dict: The response from the HubSpot API.
    """


    # Prepare contact properties
    properties = {
        "email": email
    }
    if first_name:
        properties["firstname"] = first_name
    if last_name:
        properties["lastname"] = last_name
    if company:
        properties["company"] = company

    contact_input = SimplePublicObjectInput(properties=properties)

    try:
        # Create the contact
        response = hubspot_client.crm.contacts.basic_api.create(simple_public_object_input_for_create=contact_input)
        print("Customer created successfully!")
        return response.to_dict()
    except Exception as e:
        print(f"Error creating customer: {e}")
        return None


def get_contact_id_by_email(email):
    """
    Retrieves the HubSpot contact ID for a given email address.

    Args:
        email (str): The email address of the contact.

    Returns:
        str: The contact ID if found, or None if no contact is found.
    """
    # Define the search filter
    search_filter = Filter(property_name="email", operator="EQ", value=email)
    filter_group = FilterGroup(filters=[search_filter])
    search_request = PublicObjectSearchRequest(filter_groups=[filter_group], properties=["email"])

    try:
        # Perform the search
        response = hubspot_client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        results = response.results

        if results:
            contact_id = results[0].id  # Assuming the first result is the desired contact
            print(f"Contact found with ID: {contact_id}")
            return contact_id
        else:
            print(f"No contact found with email: {email}")
            return None
    except Exception as e:
        print(f"Error searching for contact: {e}")
        return None


def set_custom_property(contact_id, property_name, value):
    """
    Updates a custom property for a HubSpot contact.

    Args:
        contact_id (str): The ID of the contact to update.
        property_name (str): The custom property to update.
        value: The value to set for the custom property.

    Returns:
        dict: The response from the HubSpot API.
    """
    properties = {
        property_name: value
    }
    return set_custom_properties(contact_id, properties)


def set_custom_properties(contact_id, properties):
    """
    Updates a custom property for a HubSpot contact.

    Args:
        contact_id (str): The ID of the contact to update.
        property_name (str): The custom property to update.
        value: The value to set for the custom property.

    Returns:
        dict: The response from the HubSpot API.
    """

    update_input = SimplePublicObjectInput(properties=properties)

    try:
        # Update the contact
        response = hubspot_client.crm.contacts.basic_api.update(contact_id=contact_id, simple_public_object_input=update_input)
        print(f"Contact '{contact_id}' updated successfully!")
        return response.to_dict()
    except Exception as e:
        print(f"Error updating contact '{contact_id}': {e}")
        return None


def get_company_data(contact_id):
    return get_custom_properties(contact_id, list(hubspot_1_column_names.keys()))


def get_custom_properties(contact_id, property_names):
    """
    Retrieves specified properties for a HubSpot contact.

    Args:
        contact_id (str): The ID of the contact to retrieve.
        property_names (list): A list of property names to fetch.

    Returns:
        dict: A dictionary containing the requested properties and their values, or None if an error occurs.
    """
    try:
        # Fetch the contact's properties
        response = hubspot_client.crm.contacts.basic_api.get_by_id(
            contact_id=contact_id,
            properties=property_names
        )
        # Extract the properties
        contact_properties = response.properties
        print(f"Contact '{contact_id}' properties retrieved successfully!")
        return {prop: contact_properties.get(prop) for prop in property_names}
    except Exception as e:
        print(f"Error retrieving properties for contact '{contact_id}': {e}")
        return None


def prepare_email_1_user(contact_id: str):
    set_custom_property(contact_id, "sql1_send_email", True)


def prepare_email_2_user(contact_id: str):
    set_custom_property(contact_id, "sql2_send_email", True)


def create_user(email):
    contact_id = get_contact_id_by_email(email)
    if not contact_id:
        result = create_hubspot_customer(email)
        if result:
            contact_id = result["id"]  # Retrieve the contact ID from the creation response
    return contact_id


# Example usage
if __name__ == "__main__":
    email = "tom@grounded.world"
    create_user(email)

