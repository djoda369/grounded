import os
import string
import time
from typing import Dict

import rootpath
import streamlit
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from core.gpt.chatgpt import llm_stream, process_stream
from core.gpt.knowledge import read_slack
from core.helper.files import json_read_file
from core.vault.conversation import Conversation

from data.topics.GroundedWorld.reader import read_context_grounded
from email_popup import email_popup

approach = """
Roleplay as Gaia from GroundedWorld as you are talking to a potential client from GroundedWorld wanting to have a better understanding of GroundedWorld.
If the client has a question about GroundedWorld, ask follow up questions to understand their question better. Then if they have clarified their question we can recommend a service that GroundedWorld provides. If the client is interested in the solution, we can recommend sitting down for a 30 minute call using the following link <URL>.
Always try to reference any context of previous projects that Grounded World has done before to secure clients into understanding that Grounded World is the right partner.
Prioritize the context of both Grounded World and its experience and selected news over general information about the industry or problem so that any information mentioned can be linked back Grounded World.
"""


grounded_world = {'company': {'name': 'GroundedWorld',
                              'description': 'GroundedWorld is a B Corp certified social innovation and brand activation agency that specializes in transforming brand purpose into profit through sustainability marketing and social impact initiatives. The agency works globally with brands, retailers, startups, and nonprofits, helping them articulate and activate their purpose while promoting social impact and sustainability. Known for its commitment to social justice advocacy and a carbon net zero goal, GroundedWorld also invests in social enterprises and donates a portion of its revenues to nonprofits. The company offers a range of services, including brand purpose strategy, creative campaigns, shopper marketing, and sustainability consulting.',
                              'industry': 'Marketing and Advertising'}, 'websites': {
    'https://grounded.world/': 'GroundedWorld is a B Corp certified social innovation and brand activation agency that specializes in brand purpose marketing. They work globally with brands, retailers, startups, and nonprofits to articulate purpose, activate brand strategies, and accelerate social impact. Their services include sustainability marketing, social impact initiatives, brand activism, startup branding, and nonprofit marketing. The website features testimonials from clients, explains their method of transforming brand purpose into profit, and offers resources like guides on various marketing strategies.',
    'https://www.linkedin.com/company/groundedworld': 'GroundedWorld is a multi-award winning, B Corp certified social innovation and brand activation agency based in Westport, Connecticut. The agency focuses on transforming brand purpose into profit while creating value by promoting social impact and sustainability. Founded in 2018, the agency is women-led and aims to become carbon net zero certified. They open-source their intellectual property, invest in startup social enterprises they help accelerate, and donate 5% of their gross revenues to nonprofits annually. GroundedWorld offers services including brand purpose, strategy, creative campaigns, shopper marketing, and sustainability consulting. They work exclusively with purposeful brands, retailers, startups, and nonprofits. The agency is known for its commitment to sustainability and social justice advocacy.',
    'https://screening.mhanational.org/content/how-do-i-stay-grounded-in-reality/#:~:text=To%20be%20grounded%20in%20reality,living%20in%20the%20present%20moment.': 'The article focuses on techniques for staying grounded in reality, particularly when experiencing symptoms related to mental health conditions. It highlights causes of losing touch with reality, such as trauma, depression, panic attacks, and psychosis. The article suggests maintaining a sleep schedule for mental well-being, talking to friends as reality testers, using grounding techniques like observing surroundings, and staying present through meditation and exercise. It also discusses the connections between mind, body, food, and substance use. Overall, it offers practical self-help strategies for managing dissociative symptoms and emphasizes the importance of professional support when needed.',
    "https://steamcommunity.com/app/962130/discussions/0/5946473955236024434/#:~:text=posted%20by%20JamesFace%3A-,its%201%20%2D%204.,the%20other%20isn't%20online.": 'The Steam Community discussion is about the game "Grounded" and addresses a question about its co-op mode. A user named Aurora asks if four players are necessary for co-op or if it can be played with fewer. Responses indicate that the game supports 1-4 players in co-op mode, allowing progress to be saved to the game world, and letting friends access it even if the original host is offline. Players have separate inventories, and an Xbox account is needed for multiplayer. The discussion also talks about technical issues with Xbox account syncing.',
    'https://www.bcorporation.net/en-us/find-a-b-corp/company/grounded-world': "GroundedWorld is a certified B Corporation marketing agency based in Connecticut, USA. Since October 2019, it has specialized in design, branding activation, sustainability marketing, and social impact, helping well-known brands and startups articulate and activate their purpose. The agency is known for its flexibility and efficiency in adapting to client needs, and it's certified as ExO (Exponential Organizations) masters, offering strategies to grow businesses 10x faster.\n\nGroundedWorld achieved an overall B Impact Score of 116.7, well above the 80 points needed for B Corp certification and the ordinary business median score of 50.9. This score reflects the agency's performance across several categories: Governance (19.1), Workers (29.0), Community (51.2), Environment (7.2), and Customers (10.0). The agency excels particularly in Governance and Community, demonstrating strong ethics and social engagement. However, its environmental impact score suggests room for improvement."}}
stella_mcccartney = {'company': {'name': 'Stella McCartney',
                                 'description': "Stella McCartney is a luxury fashion brand that offers a diverse range of high-end products including women's and children's clothing, handbags, shoes, accessories, and collaborations with Adidas. The company is well-known for its commitment to sustainability and incorporates eco-friendly practices into its operations. Customers can shop new arrivals, sale items, and exclusive collections. Stella McCartney also provides a robust online shopping experience with options for account management, order tracking, and customer support.",
                                 'industry': 'Fashion and Retail'}, 'websites': {
    'https://www.stellamccartney.com/gb/en/': "The Stella McCartney UK website offers a range of luxury fashion products including women’s and kids' clothing, handbags, shoes, and accessories. The site features sections for new arrivals, sales, exclusive collections like Stella's Gift Guide and Falabella Forever, as well as collaborations with Adidas. Stella McCartney emphasizes sustainability and offers information on social sustainability and circularity in their operations. Users can sign up for newsletters to receive information on private sales, new collections, and exclusive events. The website also has customer service options for shipping, returns, and exchanges, and encourages users to engage through social media and various digital touchpoints.",
    'https://www.stellamccartney.com/gb/en/newsletter-signup': "The Stella McCartney website offers a variety of categories for shopping, including Women's fashion, Handbags, Shoes, Accessories, Kids clothing, and Adidas by Stella McCartney. The website emphasizes its commitment to sustainability. It provides options for sale items, new arrivals, and exclusive collections like the Iconic Falabella. Users can create an account, manage their wishlist, and join a newsletter to receive updates on sales, new collections, and events. The website also includes a Store Locator feature, customer service contacts, and a detailed privacy policy concerning the handling of personal data. The homepage highlights key products like the Stella Ryder Shoulder Bag and Falabella Tiny Tote Bag and provides information on shipping details specific to the United Kingdom.",
    'https://www.stellamccartney.com/gb/en/legal/shipping-returns.html': "The website provides information on shipping and returns for Stella McCartney's online store, offering free express shipping on all orders within the UK. The shipping time is typically 2-3 business days using DHL Express. The website outlines shipping restrictions, noting that orders cannot be shipped to certain areas or P.O. Boxes. It also discusses policies for exchanges and returns. Additionally, visitors can sign up for newsletters to receive updates on private sales, new collections, and events. The website includes various categories for shopping, such as Stella Ryder, Falabella handbags, and collections for women, men, kids, and Adidas by Stella McCartney.",
    'https://www.stellamccartney.com/gb/en/on/demandware.store/Sites-smc-row-Site/en_GB/Page-LocaleFragment/': "The Stella McCartney website offers a wide range of products for women, children, and collaborations with Adidas, including clothing, handbags, shoes, and accessories. The site features new arrivals and sale items across these categories.\n\nThe main sections are:\n- Women's ready-to-wear, including dresses, coats, knitwear, and sportswear\n- Handbags with various styles including crossbody, totes, and mini bags\n- Footwear, featuring boots, sneakers, heels, and more\n- Accessories such as wallets, sunglasses, and belts\n- Adidas by Stella McCartney for activewear\n- Collections tailored for kids\n\nSpecial focuses include the iconic Falabella collection and the Stella Loves curated edits. The site emphasizes sustainability and offers newsletters for exclusive access to sales and new collections. The website features international shipping settings and provides customer service through various channels.",
    'https://www.stellamccartney.com/gb/en/gb/en/': "The Stella McCartney website is an online store that offers a wide range of fashion items across several categories including women's clothing, handbags, shoes, and accessories as well as children's and adidas collaborations. The site features sections for new arrivals, sale items, exclusive collections, and bestsellers. It highlights sustainable fashion practices and exclusive branded items such as the Iconic Falabella bags. Additionally, it provides information about the retailer's sustainable efforts and offers customer support options including a store locator, contact email, and phone support. The website also invites users to sign up for newsletters to receive updates on private sales and new collection launches.",
    'https://www.stellamccartney.com/gb/en/account': 'The Stella McCartney website offers a wide range of products, including women\'s, kids\', and Adidas-branded clothing, shoes, bags, and accessories. It features categories like "New In," "Sale," "Handbags," "Shoes," and special collections like Stella Loves series. It also highlights sustainability initiatives and offers customer services such as account management, order tracking, and customer support. The website includes promotions and exclusive offers through newsletter sign-ups. Users can manage cookies and privacy settings through a detailed options menu.'}}
aventon = {'company': {'name': 'Aventon Bikes',
                       'description': 'Aventon Bikes specializes in electric bikes designed for various purposes including commuting, off-road adventures, cargo transport, and more. They offer different categories like commuter, fat tire, folding, and lightweight ebikes. The company provides extensive support and customer service, featuring free shipping, 2-year warranties, and financing options. Aventon stands out with safety certifications, a large network of dealers for expert support, and strong community engagement through blogs, events, and rider reviews. They also offer a range of accessories and components.',
                       'industry': 'Electric Bicycle Manufacturing'}, 'websites': {
    'https://www.aventon.com/': "Aventon Bikes offers a variety of electric bikes designed for different purposes such as commuting, off-road, and cargo hauling. The site features multiple categories like commuter, fat tire, folding, and lightweight ebikes. It also provides information about warranties, shipping, return policies, and various accessories including racks, bags, and maintenance tools. Users can explore detailed product information, view best sellers, and take advantage of financing options. Aventon emphasizes safety with TUV certification and boasts accolades from Time Magazine as a top ebike brand. The site promotes a community with articles, rewards, and customer reviews. There's an emphasis on technology with features such as the ACU technology and A100 Mid-Drive Motor for customized riding experiences.",
    'https://www.aventon.com/collections/ebikes/': "Aventon offers a wide range of electric bikes for various purposes, such as commuting, off-road adventures, and cargo transport. They provide different models including folding, cruiser, and step-through ebikes. The website details their products' features, such as motor power, range, and top speed, and highlights benefits like free shipping, 2-year warranty, and financing options. Aventon emphasizes safety certifications and customer service support, including registration, FAQs, and warranty information. Additionally, they provide comparisons and guides to assist customers in selecting the best ebike for their needs, along with accessories and components available for purchase.",
    'https://www.aventon.com/pages/bike-registration/': 'The Aventon website provides information about their electric bikes (eBikes), including various models and categories like commuter, fat tire, folding, cargo, and lightweight eBikes. The website also offers customer support resources such as bike registration, FAQs, manuals, and warranty details. Visitors can explore accessories and components related to eBikes. Additionally, the site highlights community engagement through blogs, press coverage, and rider reviews. Customers can register their Aventon bikes for warranty and receive updates about deals and gear. The company emphasizes safety, with certifications and award recognitions featured.',
    'https://www.aventon.com/pages/warranty/': "The Aventon website outlines the warranty terms for their electric bikes. It offers a 2-year warranty on Aventon-branded frames, components, and batteries, extendable to a lifetime warranty on frames for original purchasers who register their bikes within 90 days of purchase. The warranty applies to defects in materials and workmanship under normal use, and it covers subsequent owners with specific terms. It does not cover normal wear and tear, damage from crashes, or improper use. Third-party components are not covered, and shipping damage is not covered unless reported within 30 days. Aventon has a clear process for warranty claims, requiring proof of original purchase, and offers free shipping for warranty claims. The warranty terms also include disclaimers limiting Aventon's liability.",
    'https://www.aventon.com/pages/share/': "Aventon Bikes' website offers a range of electric bikes and accessories tailored for various uses, including commuting, off-road adventures, and folding for convenience. They emphasize safety with TUV certification and provide comprehensive support such as a 2-year warranty, free shipping, and responsive customer service. The site includes product categories, customer reviews, a referral program, and purchasing options like financing. Additionally, they promote community engagement through blogs, events, and rewards for loyal customers. Current promotions include significant discounts on specific models, which are time-limited.",
    'https://www.aventon.com/pages/electric-bike-shop-dealer-locator': "The Aventon website offers a range of electric bikes categorized by type such as commuter, fat tire, folding, cruise, step-through, cargo & utility, lightweight, and more. It emphasizes a network of over 1,800 bike shops where users can find expert advice, service, and test rides. This includes a dealer locator tool to find shops by city, zip code, or county. There's a focus on promotions, warranties, and a safety award designation. The site also features various accessories and components for bikes. Additional information includes blog and press content, community engagement, and details about the company. Aventon provides support via contact options, FAQs, shipping and return policies, and a warranty overview."}}
meatable = {'company': {'name': 'Meatable',
                        'description': "Meatable is focused on creating real meat products through advanced biotechnological methods without the use of livestock. Their innovative solutions address environmental and societal issues tied to traditional meat production, offering a scalable, sustainable process that significantly reduces water and land usage, and greenhouse gas emissions. The company's proprietary technology, opti-ox™, enables efficient production of muscle and fat cells from pluripotent stem cells, providing a sustainable alternative to conventional meat production.",
                        'industry': 'Cultivated Meat Production'}, 'websites': {
    'https://www.meatable.com/': "Meatable is a company focused on creating real meat products through scientific innovation without the use of livestock, aiming for sustainable meat production. Their website highlights their solutions for environmental and societal issues tied to traditional meat production, presenting their proprietary technology as a scalable and eco-friendly alternative. They offer partnership opportunities through an asset-light, pure licensing model. The site also promotes a future event scheduled for February 13, 2025, labeled as an 'Invitation Only Event.'",
    'https://www.meatable.com/the-solution/': 'Meatable is addressing the environmental and societal concerns associated with current agricultural production methods, especially regarding livestock farming. The website outlines issues such as water misuse, land degradation, greenhouse gas emissions, and food insecurity linked to traditional meat production. Meatable proposes solutions through innovative approaches that promise to decrease environmental impact significantly, such as reducing greenhouse gas emissions by 75%, using 99% less land, and requiring over 95% less water. The company also highlights its efforts to eliminate the risk of zoonotic diseases, improve food security, and create a highly scalable, sustainable meat production process without the need for animal slaughter. To learn more about their market positioning, scientific differentiation, and other strategic areas, interested parties are encouraged to contact Meatable.',
    'https://www.meatable.com/the-science/': "Meatable is a company focused on producing real meat products without the need for livestock through advanced biotechnological methods. Their innovative technology, opti-ox™, allows them to grow muscle and fat cells efficiently from pluripotent stem cells. This process is significantly faster and more efficient than traditional livestock production, with 100% efficiency and improved feed conversion rates. The website outlines Meatable's proprietary technology, market opportunities, and their strategic approaches to R&D, commercial, and regulatory aspects. Additionally, they invite stakeholders to contact them for more detailed information about their competitive positioning in the market.",
    'https://www.meatable.com/the-opportunity/': 'The Meatable website presents an opportunity for partners in the meat industry to join efforts in revolutionizing meat production through advanced technology. Meatable focuses on producing real meat using their proprietary opti-ox™ technology that differentiates pluripotent stem cells into muscle and fat cells efficiently, without harming animals or the environment. They emphasize a growth potential in the global meat market, projecting a 70% increase by 2050. Their asset-light, pure-licensing model allows industry partners to license their technology, integrating seamlessly with existing meat value chains. Meatable aims to address global demand sustainably, offering technology that matches the taste and quality of traditional meat. The site encourages interested parties to contact them for more information.',
    'https://www.meatable.com/the-news/': "Meatable is a cultivated meat company focused on developing lab-grown meat products using advanced biotechnology. The website provides information about their mission to create real meat through scientific innovation, with the goal of providing sustainable solutions to the meat industry. The site includes sections on their scientific approach, opportunities in the market, and news updates. Recent updates highlight investment partnerships with companies like Betagro and Desmos Capital Partners, strategic appointments, and achievements such as being named to TIME's Best Inventions of 2024 list. Meatable is also preparing for an invite-only event scheduled for February 13, 2025. Contact information is available for journalists and potential collaborators.",
    'https://www.meatable.com/the-journey/': 'The website for Meatable focuses on their journey and achievements in the field of cultivated meat production. Meatable is a company utilizing biotechnology and science to create real meat without traditional animal farming. It highlights its leadership team, including CEO Jeff Tripician and co-founder Daan Luining, as well as its strategic partners and investors. The page also outlines their key milestones, like securing funding, partnerships, and product developments. Upcoming events such as an invite-only event on February 13, 2025, are also mentioned. The company emphasizes its commitment to solving pressing issues related to sustainable meat production.'}}


def find_new_word(previous, current):
    if previous == current:
        return None

    translator = str.maketrans('', '', string.punctuation)
    previous_normalized = previous.translate(translator)
    current_normalized = current.translate(translator)

    # Split the strings into words
    previous_words = set(previous_normalized.split())
    current_words = set(current_normalized.split())

    # Find the word(s) in current but not in previous
    new_words = current_words - previous_words
    return new_words


def display_assistant_text(text):
    word_count = len(text.split(" "))
    if word_count <= 50:  # Title for first 15 words
        st.session_state.message.title(text)
    elif word_count <= 150:  # Larger subtitle for 15-50 words
        st.session_state.message.subheader(text)
    else:  # Normal text after 50 words
        st.session_state.message.markdown(text)


def get_stream(user_prompt: str, deep_dive: bool):
    response_stream = None
    if st.session_state.catalog and deep_dive:
        with st.spinner("Diving Deeper..."):
            print("langchain", len(streamlit.session_state.catalog))
            pages = [Document(page_content=name) for name in streamlit.session_state.catalog]
            print(len(pages))
            if len(pages) > 0:
                db = FAISS.from_documents(pages, OpenAIEmbeddings())
                response = db.similarity_search(user_prompt, k=1)[0]
                channels = st.session_state.catalog[response.page_content]
                if isinstance(channels, dict) or isinstance(channels, Dict):
                    pages = [Document(page_content=name) for name in channels]
                    if len(pages) > 0:
                        db = FAISS.from_documents(pages, OpenAIEmbeddings())
                        response = db.similarity_search(user_prompt, k=1)[0]
                        path = channels[response.page_content]
                        print(path)
                        pages = read_slack(path)
                        if len(pages) > 0:
                            db = FAISS.from_documents(pages, OpenAIEmbeddings())
                            for result in db.similarity_search(user_prompt, k=5):
                                text = result.page_content
                                if "url" in response.metadata:
                                    text = response.metadata["url"] + ": " + text
                                st.session_state.conversation.system(text)
                            st.session_state.conversation.system(approach)
                            response_stream = llm_stream(st.session_state.conversation)
                else:
                    print("others", channels)
                    pages = read_slack(channels)
                    if len(pages) > 0:
                        db = FAISS.from_documents(pages, OpenAIEmbeddings())
                        for result in db.similarity_search(user_prompt, k=5):
                            text = result.page_content
                            if "url" in response.metadata:
                                text = response.metadata["url"] + ": " + text
                            st.session_state.conversation.system(text)
                        st.session_state.conversation.system(approach)
                        response_stream = llm_stream(st.session_state.conversation)

    if not response_stream:
        with st.spinner("Loading..."):
            st.session_state.conversation.system(approach)
            response_stream = llm_stream(st.session_state.conversation)
    return response_stream


def show_assistant(deep_dive: bool, user_response: str = None):

    with st.spinner("Gaia: Mmm..."):
        print("logs")
        for log in st.session_state.conversation.logs:
            print(log)
        if user_response:
            stream = get_stream(user_response, deep_dive)
        else:
            st.session_state.conversation.system(approach)
            stream = llm_stream(st.session_state.conversation)
        answers = process_stream(stream)
        chunk = ""
        old_chunk = ""
        word_count = 0  # Initialize word count

        for chunk in answers:
            added_words = find_new_word(old_chunk, chunk)
            if added_words:
                old_chunk = old_chunk + " "
                new_word = added_words.pop()
                n_letters = len(new_word)
                time_per_word = 0.125
                time_per_letter = time_per_word / n_letters
                for letter in new_word:
                    # Dynamically adjust text size based on progress
                    word_count += 1
                    display_assistant_text(old_chunk + letter)

                    time.sleep(time_per_letter)
                    old_chunk += letter
            else:
                old_chunk = chunk

        display_assistant_text(old_chunk)
        # Save final message in conversation
        st.session_state.conversation.assistant(old_chunk)
        return chunk


def show_chat(email, deepdive, email_analyzer):

    if "message" not in st.session_state:
        st.session_state.question = st.empty()
        st.session_state.question_text = ""
        st.session_state.message = st.empty()
        st.session_state.answer = st.empty()

    if "conversation" not in st.session_state:
        st.session_state.conversation = Conversation(email)
        if email_analyzer.metadata:
            text = "Context for user you are currently talking to from " + email
            for key, value in email_analyzer.metadata.items():
                text += str(key) + ": " + str(value) + "\n"
            st.session_state.conversation.system(text)

        st.session_state.conversation.system("Your name is Gaia, you are a marketing assistant for GroundedWorld.")
        st.session_state.conversation.system("GroundedWorld is " + grounded_world["company"]["description"])
        texts = read_context_grounded()
        for text in texts:
            st.session_state.conversation.system("GroundedWorld context: " + text)

        st.session_state.conversation.system(f"You are speaking to a representative of {st.session_state.company_data['name']}.")
        st.session_state.conversation.system(st.session_state.company_data["name"] + ": " + st.session_state.company_data["description"])

        for key in st.session_state.company_data:
            st.session_state.conversation.system(key.replace("_", " ") + ": " + st.session_state.company_data[key])

        st.session_state.conversation.system(f"Welcome the client from {st.session_state.company_data['name']} and role-play as Gaia from GroundedWorld, and use one emoji in your response.")
        st.session_state.chunk = show_assistant(deepdive)
        st.session_state.turn = "user"

    response = st.session_state.answer.chat_input("...")
    if response and st.session_state.turn == "user":
        st.session_state.question_text = response
        print("text from user", response)
        st.session_state.conversation.user(response)
        st.session_state.turn = "assistant"

    if st.session_state.turn == "assistant":
        st.session_state.chunk = show_assistant(deepdive, response)
        st.session_state.turn = "user"

    if st.session_state.question_text != "":
        st.session_state.question.markdown("Q: " + st.session_state.question_text)

    display_assistant_text(st.session_state.chunk)


def show_interface(email, email_analyzer):
    input_title = st.empty()
    input_company = st.empty()
    input_message = st.empty()
    start_button = st.empty()

    if "company_data" not in st.session_state:

        input_title.title("Gaia Meeting Interface")
        companies = [stella_mcccartney["company"], aventon["company"], meatable["company"]]
        options = [company["name"] + " - " + company["industry"] for company in companies]
        company_name = input_company.selectbox("Company", options, index=0)

        if start_button.button("Start Gaia"):
            company_index = -1
            company = None
            for index, option in enumerate(options):
                if company_name == option:
                    company_index = index
                    company = companies[index]

            if company:
                print("starting")
                with st.spinner("Loading..."):
                    input_message.info("Processing Transcript")
                    st.session_state.company_data = company

    if "company_data" in st.session_state:
        # Clear the screen
        input_title.empty()
        input_company.empty()  # Remove everything inside it
        input_message.empty()
        start_button.empty()

        # Show chat interface
        col1, col2 = st.columns([5, 1])
        with col1:
            input_title.empty()

        with col2:
            deepdive = st.checkbox("Deep dive", value=False)

        show_chat(email, deepdive, email_analyzer)


if __name__ == "__main__":
    st.set_page_config(
        page_title=f"Gaia - Grounded World",
        page_icon="🌱",
        layout="wide",
    )
    container = st.container()
    with container:
        email, email_analyzer = email_popup()

        if email:
            container = st.empty()
            show_interface(email, email_analyzer)
