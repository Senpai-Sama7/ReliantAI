from crewai import Agent, Task, Crew, Process
from .llm import get_gemini_pro, get_gemini_flash
from .quality_standards import COPY_AGENT_QUALITY_RULES, OUTREACH_AGENT_QUALITY_RULES
from .tools.google_places import GooglePlacesTool
from .tools.pagespeed import PageSpeedTool
from .tools.gbp_scraper import GBPScraperTool
from .tools.schema_validator import SchemaValidatorTool
from .tools.twilio_sms import TwilioSMSTool
from .tools.resend_email import ResendEmailTool


def create_prospect_crew(prospect_data: dict) -> Crew:
    trade = prospect_data.get("trade", "hvac")
    city = prospect_data.get("city", "")
    state = prospect_data.get("state", "")
    business_name = prospect_data.get("business_name", "")
    place_id = prospect_data.get("place_id", "")
    phone = prospect_data.get("phone", "")
    email = prospect_data.get("email", "")

    google_places = GooglePlacesTool()
    pagespeed = PageSpeedTool()
    gbp_scraper = GBPScraperTool()
    schema_validator = SchemaValidatorTool()
    twilio_sms = TwilioSMSTool()
    resend_email = ResendEmailTool()

    business_researcher = Agent(
        role="Business Researcher",
        goal="Deeply research a local home services business using Google Places and GBP data",
        backstory=(
            "You're a data-obsessed investigator who treats every business like a case file. "
            "You pull Google Places data, parse reviews for patterns, check profile completeness, "
            "and cross-reference with PageSpeed scores. You don't guess — you extract. "
            "Your research is the foundation every other agent builds on."
        ),
        tools=[google_places, gbp_scraper, pagespeed],
        llm=get_gemini_flash(),
        verbose=True,
        allow_delegation=False,
    )

    competitor_analyst = Agent(
        role="Competitor Analyst",
        goal="Identify top competitors and find gaps in their digital presence",
        backstory=(
            "You're a market intelligence specialist. You find the 3-5 top competitors "
            "in a trade/area, analyze their keywords, content themes, and weaknesses. "
            "You don't just list competitors — you find the gaps we can exploit. "
            "Your output is the ammunition the CopyAgent uses to write killer copy."
        ),
        tools=[google_places],
        llm=get_gemini_flash(),
        verbose=True,
        allow_delegation=False,
    )

    copy_agent = Agent(
        role="Copy Agent",
        goal=(
            "Write Awwwards-level website copy, SEO metadata, and outreach SMS — "
            "specific, researched, and indistinguishable from a senior agency writer"
        ),
        backstory=(
            "You're a senior direct-response copywriter who spent a decade at top agencies "
            "before specializing in local home services. You hate generic AI copy — vague "
            "headlines, empty superlatives, template trust badges. Every line you write "
            "references something real: the owner's name, the city, a review theme, a license. "
            "Your headlines read like editorial. Your SMS messages feel like a neighbor "
            "who did their homework. Your work makes a preview site look like a $50k engagement."
        ),
        llm=get_gemini_pro(),
        verbose=True,
        allow_delegation=False,
    )

    site_builder_agent = Agent(
        role="Site Builder",
        goal="Assemble all research and copy into a registered preview site",
        backstory=(
            "You're the assembler. You take everything the research and copy agents produced "
            "and register it as a live preview site. You don't write prose — you structure data. "
            "Your job is to ensure the schema.org is valid, the slug is clean, "
            "and the preview URL works the moment you're done."
        ),
        tools=[schema_validator],
        llm=get_gemini_flash(),
        verbose=True,
        allow_delegation=False,
    )

    outreach_agent = Agent(
        role="Outreach Agent",
        goal=(
            "Send a first outreach SMS that feels hand-written — specific, under 155 chars, "
            "preview URL at the end — never automated or template-like"
        ),
        backstory=(
            "You're a thoughtful founder doing personal outreach, not a sales bot. "
            "You've seen thousands of cold texts die because they opened with 'Hi! We noticed...' "
            "You reference one specific fact about their business, bridge to value in plain language, "
            "and end with the full preview URL. If it could be sent unchanged to 100 businesses, "
            "you rewrite it until it couldn't."
        ),
        tools=[twilio_sms, resend_email],
        llm=get_gemini_flash(),
        verbose=True,
        allow_delegation=False,
    )

    t_research = Task(
        description=(
            f"Research {business_name} in {city}, {state} ({trade}).\n"
            f"Google Place ID: {place_id}\n\n"
            "1. Use google_places_search with place_id to get full details\n"
            "2. Use gbp_profile_scraper to get completeness score and reviews\n"
            "3. Use pagespeed_analyzer on their website URL\n\n"
            "Return a structured dict with:\n"
            "- name, phone, website, address, lat, lng\n"
            "- rating, review_count\n"
            "- reviews (top 5 with author, rating, text)\n"
            "- hours, summary, photos\n"
            "- profile_completeness (0-100)\n"
            "- review_response_rate\n"
            "- pagespeed_score, lcp, fid, cls, has_ssl"
        ),
        agent=business_researcher,
        expected_output="Structured business research data as a dictionary",
    )

    t_competitor = Task(
        description=(
            f"Analyze top 3-5 {trade} competitors in {city}, {state}.\n\n"
            "1. Use google_places_search to find competing businesses\n"
            "2. For each competitor: name, rating, review_count, website\n"
            "3. Identify content themes and gaps\n\n"
            "Return a list of competitor dicts with:\n"
            "- competitor_name, competitor_website\n"
            "- rating, review_count\n"
            "- top_keywords (list of strings)\n"
            "- content_themes (list of strings)\n"
            "- weaknesses (list of gaps we can exploit)"
        ),
        agent=competitor_analyst,
        expected_output="List of competitor analysis dictionaries",
    )

    t_copy = Task(
        description=(
            f"Write website copy for {business_name} ({trade}) in {city}, {state}.\n\n"
            f"{COPY_AGENT_QUALITY_RULES}\n\n"
            "Using the research and competitor data, produce a copy_package dict:\n\n"
            "1. HERO: headline (business name OR city + concrete outcome), subheadline "
            "(specific benefit + proof), trust_bar (3 items with certifications/licenses/times)\n"
            "2. SERVICES: 3-5 services with icon name, title, description (each with one concrete detail)\n"
            "3. ABOUT: owner_story paragraph (founder name, year, specific moment), trust_points (3 with numbers)\n"
            "4. REVIEWS: aggregate_line, individual reviews (3 items — use real review data when available)\n"
            "5. FAQ: 5 question/answer pairs a real homeowner in {city} would ask for {trade}\n"
            "6. SEO: title (60 chars max, name + city + service), description (155 chars max, benefit + CTA)\n"
            "7. OUTREACH SMS (< 155 chars)\n"
            "   Structure: '[Name], [specific observation] — [value]. [PREVIEW_URL]'\n"
            "   Constraint: PREVIEW_URL must appear at end. Never shorten it.\n\n"
            "Before returning: verify business name or city appears in headline; no banned phrases; "
            "every trust_bar item is specific (not 'Quality Service').\n\n"
            "Return as a JSON-compatible dict."
        ),
        agent=copy_agent,
        expected_output="Complete copy package dictionary with all sections",
    )

    t_site_build = Task(
        description=(
            "Register the prospect's preview site.\n\n"
            "Call SiteRegistrationService.register() with:\n"
            "- prospect_id from prospect_data\n"
            "- copy_package from the copy agent's output\n"
            "- research_data from the research agent's output\n"
            "- competitor_data from the competitor agent's output\n\n"
            "After registration, confirm:\n"
            "- slug is clean (lowercase, hyphens, no special chars)\n"
            "- preview_url contains preview.reliantai.org\n"
            "- schema_org was validated\n\n"
            "Return: {slug, preview_url, schema_valid}"
        ),
        agent=site_builder_agent,
        expected_output="Site registration result with slug and preview URL",
    )

    t_outreach = Task(
        description=(
            f"Send the first outreach SMS to {phone} for {business_name}.\n\n"
            f"{OUTREACH_AGENT_QUALITY_RULES}\n\n"
            "1. Use the SMS message from the copy agent's output\n"
            "2. Reject and rewrite if it contains banned openers, emoji, or generic praise\n"
            "3. Call send_sms with to={phone} and body=sms_message\n"
            "4. If email is available ({email}), also send via send_email\n\n"
            "Pre-send checklist:\n"
            "- Under 155 characters\n"
            "- One specific observation from research (not 'great reviews')\n"
            "- Full preview URL at the very end\n"
            "- Could NOT be sent unchanged to a different business\n\n"
            "Return: {sms_sent: bool, sms_sid: str, email_sent: bool}"
        ),
        agent=outreach_agent,
        expected_output="Outreach delivery confirmation",
    )

    crew = Crew(
        agents=[business_researcher, competitor_analyst, copy_agent, site_builder_agent, outreach_agent],
        tasks=[t_research, t_competitor, t_copy, t_site_build, t_outreach],
        process=Process.sequential,
        memory=True,
        max_rpm=10,
        verbose=True,
    )

    return crew
