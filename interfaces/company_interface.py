import string
import time

import streamlit as st

from core.gpt.chatgpt import llm_stream, process_stream
from core.gpt.history import History


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


def show_assistant():

    with st.spinner("Gaia: Mmm..."):
        stream = llm_stream(st.session_state.history)
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

        display_assistant_text(old_chunk) # Save final message in history
        return chunk


if __name__ == "__main__":

    company_name = "Patagonia"
    meeting_data = """Opening Remarks
Lisa Robinson (Patagonia):
Thanks for joining us today, Emma and Jacob. Patagonia has always championed sustainability, but we believe it’s time to take it to the next level. We want to engage a broader audience with our mission of “buy less, but better” and highlight the value of regenerative practices in the fashion industry. Your work with brands like Ocean Brands and The LYCRA Company caught our eye.

Emma Hart (GroundedWorld):
Thank you, Lisa. We’re thrilled to explore this opportunity. Patagonia is already a leader in this space, and we’d love to help amplify your impact. From what we understand, you’re aiming to bridge the gap between your purpose-driven philosophy and wider consumer engagement.

Discussion: Challenges and Opportunities
Tom Sanchez (Patagonia):
Exactly. We’ve found that while our loyal customer base appreciates our environmental stance, it can sometimes come across as niche or preachy to new audiences. We want to reframe sustainability as accessible, aspirational, and essential.

Jacob Lee (GroundedWorld):
That’s a fascinating challenge. We often find that bridging the "intention-action gap" is about storytelling—making the values relatable without overwhelming the audience. Have you considered creating narratives around the individuals in your supply chain, like the farmers or workers behind your regenerative cotton initiative?

Lisa Robinson (Patagonia):
That’s been on our radar, but we haven’t figured out how to do it without coming off as self-promotional.

Emma Hart (GroundedWorld):
That’s where co-creation can help. We could partner with grassroots organizations, workers, or even your customers to showcase their stories. It would feel authentic and inclusive. Our Belief, Purpose, and Pursuits framework could guide this process by aligning your brand purpose with measurable actions.

Campaign Ideas
Jacob Lee (GroundedWorld):
One idea we’d like to propose is a campaign centered on “The Lifecycle of Your Clothing.” Imagine a digital and physical storytelling experience where customers can see how each piece of Patagonia apparel impacts the planet positively. This could include repair programs, resale initiatives, and recycling options.

Tom Sanchez (Patagonia):
That aligns well with our Worn Wear program. Could we also incorporate educational components about fast fashion’s environmental impact?

Emma Hart (GroundedWorld):
Absolutely. We could include interactive elements, like tools for customers to calculate their carbon savings by choosing Patagonia over fast fashion brands.

Lisa Robinson (Patagonia):
I like where this is going. But we also need to make it visually stunning and emotionally engaging. Patagonia’s audience expects a strong aesthetic.

Jacob Lee (GroundedWorld):
That’s our specialty. We could create an immersive digital campaign with striking visuals—think drone footage of regenerative farms paired with high-quality portraits of the workers. We can also highlight Patagonia’s progress in a transparent, relatable way.

Execution Plan
Emma Hart (GroundedWorld):
To execute this, we’d start with a research phase to identify key audience segments and their pain points regarding sustainable fashion. Then, we’d co-create the campaign narrative with your team and partners, ensuring it’s rooted in authenticity and innovation.

Tom Sanchez (Patagonia):
Sounds like a solid approach. How long would this take to roll out?

Jacob Lee (GroundedWorld):
From research to launch, about four to six months. We’ll provide detailed metrics to track the campaign’s effectiveness, including engagement rates, carbon offset awareness, and sales from sustainable collections.

Closing Remarks
Lisa Robinson (Patagonia):
This feels like a partnership that could truly resonate with our customers and new audiences alike. Let’s proceed with an exploratory workshop to dive deeper into the strategy.

Emma Hart (GroundedWorld):
Fantastic. We’ll schedule a follow-up to map out next steps. We’re excited to work with Patagonia and help make sustainable fashion a global movement.

Meeting Adjourned
Action Items:

Schedule exploratory workshop (GroundedWorld).
Share initial customer insights and campaign goals (Patagonia).
Draft a project timeline and milestones (GroundedWorld)"""

    company_data = {'gaia_sql1_topic': 'Sustainability accessibility and campaign strategy', 'firstname': 'Patagonia', 'industry': 'Apparel', 'specific_result': 'Apparel', 'gaia_sql1_objective_1': 'Make sustainability more accessible, aspirational, and essential to a broader audience.', 'gaia_sql1_objective_2': "Enhance the 'buy less, but better' mission while overcoming perceptions of being niche or preachy.", 'gaia_sql1_objective_3': "Develop a campaign centered on 'The Lifecycle of Your Clothing' to include repair, resale, recycling programs, and education on fast fashion’s environmental impact.", 'gaia_sql1_pain_point_1': 'Patagonia struggles with being perceived as niche or preachy in their sustainability efforts.', 'gaia_sql1_pain_point_2': "Difficulty in making their 'buy less, but better' mission more accessible and essential to a broader audience.", 'gaia_sql1_pain_point_3': 'Need to make sustainability more aspirational and engaging to educate consumers about the environmental impact of fast fashion.', 'gaia_sql1_case_study_1': "The LYCRA Company's 'Keep in the Loop with LYCRA' campaign is relevant to Patagonia's goals as both focus on promoting sustainable practices in the apparel industry. The LYCRA Company addressed textile waste by developing new fibers from recycled content and aimed to foster industry-wide collaboration through education and innovation. Their campaign included partnerships, educational forums, and a focused narrative around circularity, much like Patagonia's interest in grassroots storytelling and lifecycle education. Patagonia could draw insights from LYCRA's approach to building collaborative platforms and thought-leadership initiatives, engaging stakeholders to drive change in sustainability perceptions within the fashion industry.", 'gaia_sql1_case_study_2': "This case study highlights a social impact campaign for the documentary 'Tribes on the Edge,' which aimed to raise awareness about the indigenous tribes of the Amazon rainforest and their critical role in protecting the environment. Like Patagonia's goals, this campaign leveraged storytelling and grassroots collaboration to make the issue relatable and important to a broader audience. The campaign organized private screenings and partnered with production and distribution channels to create personalized, impactful experiences. This approach is relevant to Patagonia's plan to co-create narratives with grassroots entities and educate audiences on sustainable practices.", 'gaia_sql1_article_title_1': 'Making Sustainability REAL for Consumers', 'gaia_sql1_article_description_1': 'This article explores how brands can connect with consumers by making sustainability relevant through innovative product design, data-driven tools, and creative marketing approaches. It features examples from Redfin, Mastercard, Doconomy, and Oatly that illustrate how companies are integrating environmental awareness into everyday consumer interactions.', 'gaia_sql1_article_title_2': 'Retail Activation for Good', 'gaia_sql1_article_description_2': 'This guide provides insights and principles for brands and retailers toeffectively communicate their sustainability commitments and engage shoppers at the point of purchase.', 'gaia_sql1_grounded_product': 'Sustain-Agility', 'grounded_product_benefits': "1. Aligns Patagonia's brand and social purpose with sustainability marketing and storytelling.\n2. Provides a strategic framework to activate brand purpose and generate consumer demand.\n3. Facilitates co-creation opportunities for commercial innovation and engaging campaigns."}

    newsletter = """Sustainable Fashion Insights: Paving the Way for a Greener Future

Dear Readers,

Welcome to this week's edition of Sustainable Fashion Insights, where we explore the latest developments and initiatives driving the fashion industry towards a more sustainable and responsible future. This edition is particularly relevant for our partners at Patagonia, as we delve into themes that align with your mission of "buy less, but better" and highlight the value of regenerative practices.

1. Reimagining Growth in the Textile Industry

The Textile Exchange's "Reimagining Growth Landscape Analysis" report challenges the traditional linear "take-make-waste" model, advocating for a shift towards a regenerative economy. This aligns with Patagonia's commitment to sustainability and offers a roadmap for integrating circular business models like repair, rental, and resale—key components of your Worn Wear program.

2. Circular Economy in Fashion

The Ellen MacArthur Foundation's "The Fashion ReModel" project emphasizes decoupling revenue from production, a concept that resonates with Patagonia's efforts to make sustainability accessible and aspirational. By focusing on product design and circular business models, this initiative supports extending the life of fashion products, a goal shared by Patagonia.

3. Avolta and Ecoalf Partnership

Avolta's collaboration with Ecoalf to create uniforms from recycled materials showcases a successful model of sustainability and innovation. This partnership reflects the kind of authentic storytelling and co-creation that Patagonia aims to achieve, particularly in highlighting the individuals behind sustainable practices.

4. Sustainability and Innovation in Fashion

Ecoalf's dedication to protecting natural resources and promoting a sustainable lifestyle mirrors Patagonia's values. This serves as an inspiring example of how brands can lead the charge in sustainable fashion, offering insights into how Patagonia can further engage with its audience through compelling narratives and visual storytelling.

5. Corporate Responsibility and ESG Commitment

Avolta's initiative with Ecoalf underscores the importance of integrating sustainability into core business models, a principle that Patagonia champions. This approach highlights the critical role of corporate responsibility in achieving long-term sustainability goals, providing a framework for Patagonia's ongoing efforts to bridge the gap between purpose-driven philosophy and consumer engagement.

As we continue to witness these transformative changes, it is clear that the fashion industry is on a promising path towards sustainability. We hope these insights inspire Patagonia to further engage with initiatives that prioritize the health of our planet and resonate with both loyal and new audiences.

Thank you for joining us in this journey towards a more sustainable future.

Warm regards,

Gaia
Editor, Sustainable Fashion Insights"""

    company_website = ['The page from Patagonia\'s website offers a wide range of outdoor clothing and gear for men, women, kids, and babies. It highlights their commitment to environmental responsibility, stating that "Earth Is Now Our Only Shareholder." The site provides information on free shipping for orders over $99, flexible shipping options, and a 2024 Gift Guide. Patagonia emphasizes their dedication to sustainability, activism, and supporting grassroots movements. The page also features various product categories, including jackets, vests, fleece, and accessories, along with options to shop by activity or collection. Additionally, it promotes their Worn Wear program, which encourages trading in and shopping for used gear.', 'The page on Patagonia\'s website offers a wide range of outdoor clothing and gear for men, women, kids, and babies. It highlights their commitment to environmental responsibility, stating that "Earth Is Now Our Only Shareholder." The site features various categories such as jackets, vests, fleece, and accessories, along with specialized collections like Nano Puff® and Better Sweater®. Patagonia emphasizes their Ironclad Guarantee, supporting grassroots activism, and offers free shipping on orders over $99. They also provide flexible shipping options to address environmental concerns. Additionally, the site includes sections for activism, sports, stories, and a gift guide for 2024.', "The page on Patagonia's website offers a wide range of outdoor clothing and gear for men, women, kids, and babies. It highlights their commitment to sustainability, with a focus on using recycled materials and supporting environmental activism. The site features various categories, including jackets, vests, fleece, and accessories, along with options for different sports and activities. Patagonia emphasizes their Ironclad Guarantee, ensuring the durability and longevity of their products. They also offer free shipping on orders over $99 and provide flexible shipping options. Additionally, the site promotes their 2024 Gift Guide and encourages customers to explore their activism initiatives and used gear options.", 'The page from Patagonia\'s website offers a comprehensive shopping experience for outdoor clothing and gear. It highlights free shipping on orders over $99 and emphasizes Patagonia\'s commitment to environmental responsibility, stating "Earth Is Now Our Only Shareholder." The site features a 2024 Gift Guide, promoting outdoor gear as ideal gifts. It provides various categories for shopping, including women\'s, men\'s, kids\' and baby clothing, packs and gear, and web specials. The page also includes sections on activism, sports, and stories, along with options to shop used gear and food. Additionally, it offers customer service resources, information about Patagonia\'s environmental and social initiatives, and a newsletter signup for exclusive offers and updates.', "The page on Patagonia's website offers a wide range of outdoor clothing and gear for men, women, kids, and babies. It highlights their commitment to sustainability, with a focus on using recycled materials and supporting environmental activism. The site features various categories, including jackets, vests, fleece, and accessories, along with options for different sports and activities. Patagonia emphasizes their Ironclad Guarantee, ensuring the durability and longevity of their products. They also offer free shipping on orders over $99 and provide flexible shipping options. Additionally, the site promotes their 2024 Gift Guide and encourages customers to explore their activism initiatives and used gear options.", "The page on Patagonia's website offers a wide range of outdoor clothing and gear for men, women, kids, and babies. It highlights their commitment to sustainability, with a focus on using recycled materials and supporting environmental activism. The site features various categories, including jackets, vests, fleece, and accessories, along with options for different sports and activities. Patagonia emphasizes their Ironclad Guarantee, ensuring the durability and longevity of their products. They also offer free shipping on orders over $99 and provide flexible shipping options. Additionally, the site promotes their 2024 Gift Guide and encourages customers to explore their activism initiatives and used gear options."]

    st.set_page_config(
        page_title=f"Gaia x {company_name} - GroundedWorld",
        page_icon="🌱",
        layout="wide",
    )

    if "message" not in st.session_state:
        st.session_state.question = st.empty()
        st.session_state.question_text = ""
        st.session_state.message = st.empty()
        st.session_state.answer = st.empty()

    if "history" not in st.session_state:
        st.session_state.history = History()

        st.session_state.history.system("Your name is Gaia, you are a marketing assistant for GroundedWorld.")

        st.session_state.history.system(f"You are speaking to a representative of {company_name}.")
        st.session_state.history.system(f"{company_name} background: {meeting_data}")
        for company_website_page in company_website:
            st.session_state.history.system(f"{company_name} website: {company_website_page}")

        for key in company_data:
            st.session_state.history.system(key.replace("_", " ") + ": " + company_data[key])
        st.session_state.history.system(f"{company_name} has received the following newsletter that might inspire their engagement: {newsletter}")

        st.session_state.history.system("Welcome the user and role-play as Gaia and use one emoji in your response.")
        st.session_state.chunk = show_assistant()
        st.session_state.turn = "user"

    response = st.session_state.answer.chat_input("...")
    if response and st.session_state.turn == "user":
        st.session_state.question_text = response
        print("text from user", response)
        st.session_state.history.user(response)
        st.session_state.history.system("Give a brief response to the user from Gaia's perspective:")
        st.session_state.turn = "assistant"

    if st.session_state.turn == "assistant":
        st.session_state.chunk = show_assistant()
        st.session_state.turn = "user"

    if st.session_state.question_text != "":
        st.session_state.question.markdown("Q: " + st.session_state.question_text)

    display_assistant_text(st.session_state.chunk)
