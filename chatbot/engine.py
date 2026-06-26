import re
from difflib import SequenceMatcher


# Simple string similarity used for fuzzy matching (currently available but not heavily used)
def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ----- INTENTS -----
# Simple regex-based patterns for common short interactions.
# These are checked first since they're fast and have predictable answers.
INTENTS = {
    "greeting": {
        "patterns": [
            r"\b(hi|hello|hey|akwaaba|good\s*(morning|afternoon|evening)|yo|sup)\b",
        ],
        "response": (
            "Akwaaba! Welcome to your Ghana travel guide!\n\n"
            "I'm your local guide to Ghana - ask me about:\n"
            "- **Destinations** - Accra, Kumasi, Cape Coast, Tamale, and more\n"
            "- **Attractions** - castles, national parks, beaches, waterfalls\n"
            "- **Culture** - festivals, food, kente, Adinkra symbols\n"
            "- **Practical tips** - transport, visas, safety, best time to visit\n"
            "- **Itineraries** - tell me how many days you have and what you love\n\n"
            "What can I help you plan today?"
        ),
    },
    "thanks": {
        "patterns": [r"\b(thank\s*(you)?|thanks|medaase|gracias)\b"],
        "response": (
            "Me daa ase! You're very welcome. If you have more questions "
            "as you plan your trip, just ask - that's what I'm here for. "
            "Safe travels, and enjoy Ghana!"
        ),
    },
    "goodbye": {
        "patterns": [r"\b(bye|goodbye|see\s*you|farewell|nantew|yoo)\b"],
        "response": (
            "Nantew yie! (Travel well!) Feel free to come back anytime "
            "you need more tips about Ghana. Akwaaba always!"
        ),
    },
}

# ----- REGIONS -----
# Each region has keywords for matching, a main response, and optional subtopics.
# The matching logic picks the region with the most keyword hits.
REGIONS = {
    "accra": {
        "keywords": [
            "accra",
            "greater accra",
            "capital",
            "jamestown",
            "labadi",
            "osu",
            "kotoka",
        ],
        "name": "Accra & Greater Accra",
        "response": (
            "Accra is Ghana's vibrant capital and probably where your trip will start "
            "(we all fly into Kotoka International Airport).\n\n"
            "**Neighbourhoods worth your time:**\n"
            "- **Jamestown** - the historic heart with the lighthouse, colonial architecture, "
            "and an incredible fishing harbor. Go early morning (6-7am) to watch the canoes come in.\n"
            "- **Osu** - nightlife central, great restaurants, and Osu Castle. "
            "Grab some kelewele from a street vendor while you're there.\n"
            "- **Labadi / La Pleasure Beach** - the most popular beach in Accra. "
            "Lively on weekends; quieter on weekdays.\n\n"
            "**Local tip:** Traffic in Accra is no joke - a 10km trip can take an hour. "
            "Use Uber/Bolt rather than driving yourself."
        ),
        "subtopics": {
            "jamestown": (
                "Jamestown is Accra's oldest district, home to the Jamestown Lighthouse "
                "(climb it for panoramic views), colonial-era buildings, and a bustling fishing harbor. "
                "The Brazil House showcases Afro-Brazilian heritage. "
                "Best visited on a Saturday morning when the fishing boats return."
            ),
            "nightlife": (
                "Osu is the nightlife hub - lots of bars and lounges like +233 Jazz Bar & Grill. "
                "For a more local vibe, try spots in Dzorwulu or East Legon. "
                "Most places pick up after 10pm."
            ),
        },
    },
    "kumasi": {
        "keywords": [
            "kumasi",
            "ashanti",
            "manhyia",
            "kejetia",
            "asanteman",
            "bonwire",
            "kente",
        ],
        "name": "Kumasi & Ashanti Region",
        "response": (
            "Kumasi is the heart of Ashanti culture and Ghana's second-largest city. "
            "It's a completely different energy from Accra - more traditional, more relaxed.\n\n"
            "**Can't miss:**\n"
            "- **Manhyia Palace Museum** - the seat of the Asantehene (the Ashanti king). "
            "Fantastic overview of Ashanti history.\n"
            "- **Kejetia Market** - one of the largest open-air markets in West Africa. "
            "Go with a local guide and prepare to get lost for hours.\n"
            "- **Bonwire** - the center of kente cloth weaving. Watch master weavers at work "
            "and buy direct (much better prices than in Accra).\n\n"
            "If you're there on a Sunday, the Asantehene's procession at Manhyia Palace "
            "(Akwasidae festival, every 6 weeks) is spectacular."
        ),
        "subtopics": {
            "kente": (
                "Bonwire village is the spiritual home of kente cloth. "
                "Each pattern carries symbolic meaning. A small piece takes days to make, "
                "which explains the price. Quality kente is not cheap, and shouldn't be."
            ),
        },
    },
    "cape_coast": {
        "keywords": [
            "cape coast",
            "elmina",
            "castle",
            "slave",
            "slave trade",
            "central region",
            "kakum",
            "canopy walkway",
        ],
        "name": "Cape Coast & Central Region",
        "response": (
            "Cape Coast and Elmina are home to the most significant historical sites in Ghana "
            "- the slave trade castles. These deserve more than a quick visit.\n\n"
            "**Cape Coast Castle** - the larger of the two, with an excellent museum. "
            "The tour takes you through the dungeons where enslaved Africans were held before "
            "the Middle Passage. The 'Door of No Return' is a moment you won't forget. "
            "Give yourself 2 hours minimum.\n\n"
            "**Elmina Castle (St. George's Castle)** - older than Cape Coast, built by the "
            "Portuguese in 1482. The guided tour here is very good.\n\n"
            "**Practical tip:** Hire a guide at the entrance (included in entry fee). "
            "Go early at 9am to avoid crowds and heat. Bring water.\n\n"
            "Both towns also have colourful fishing harbours well worth a walk through afterward "
            "- it helps to see Ghanaian life continuing vibrantly right next to these sites."
        ),
        "subtopics": {
            "kakum": (
                "Kakum National Park is just outside Cape Coast. The canopy walkway is the main "
                "draw - you're 40m up, walking across rope bridges between giant trees. "
                "Go early (6am if you can) for the best wildlife spotting. "
                "The walkway itself takes about 45 minutes."
            ),
        },
    },
    "volta": {
        "keywords": [
            "volta",
            "wli falls",
            "wli",
            "afadjato",
            "ho",
            "tafi atome",
            "monkey sanctuary",
        ],
        "name": "Volta Region",
        "response": (
            "The Volta Region is Ghana's most scenic area - rolling green hills, "
            "waterfalls, and a completely different vibe from the coast.\n\n"
            "**Wli Falls** - the highest waterfall in West Africa (about 80m). "
            "The hike to the lower falls is easy (30 min), the upper falls is tougher (2 hrs). "
            "Go in the dry season when the water is clear.\n\n"
            "**Mount Afadjato** - Ghana's highest peak (885m). The hike takes 2-3 hours up "
            "and is manageable for most fitness levels. Hire a guide in the village.\n\n"
            "**Tafi Atome Monkey Sanctuary** - community-run conservation where Mona monkeys "
            "roam freely. They'll eat right out of your hand."
        ),
    },
    "northern": {
        "keywords": [
            "northern",
            "tamale",
            "mole",
            "mole national park",
            "larabanga",
            "safari",
            "elephant",
            "savannah",
        ],
        "name": "Northern Region & Mole National Park",
        "response": (
            "Mole National Park is Ghana's premier safari destination - think elephants, "
            "antelopes, baboons, and if you're lucky, lions and leopards.\n\n"
            "**The experience:** Walking safari with an armed guide or driving safari. "
            "Walking is incredible - tracking elephants on foot gets the heart going. "
            "Best sightings at the waterhole near the lodge at dawn and dusk.\n\n"
            "**Larabanga Mosque** - one of the oldest mosques in West Africa "
            "(Sudano-Sahelian style, 15th century). Please ask before photographing.\n\n"
            "**Getting there:** Fly Accra-Tamale (1 hr, ~$100-150), then drive 2 hrs to Mole. "
            "Or STC bus from Accra (12 hrs). Book Mole Lodge well in advance."
        ),
    },
    "western": {
        "keywords": ["western", "busua", "axim", "nzulezu", "dixcove", "surf"],
        "name": "Western Region",
        "response": (
            "The Western Region has Ghana's best beach towns and a laid-back energy.\n\n"
            "**Busua** - a classic beach town with great surf (rent boards on the beach), "
            "fresh lobster, and a backpacker vibe. Quieter than the Accra beaches.\n\n"
            "**Axim** - further west, even quieter than Busua. "
            "Great for doing nothing for a few days.\n\n"
            "**Nzulezu Stilt Village** - a UNESCO-protected village built entirely on stilts "
            "over Lake Tadane. You get there by canoe (30 min). "
            "The village has been there for over 500 years."
        ),
    },
    "eastern": {
        "keywords": [
            "eastern",
            "akosombo",
            "lake volta",
            "boti falls",
            "akwapim",
            "koforidua",
        ],
        "name": "Eastern Region",
        "response": (
            "The Eastern Region is where Ghanaians go for weekend getaways - "
            "lush forests, hills, and Lake Volta.\n\n"
            "**Akosombo** - home to the Akosombo Dam, which created Lake Volta "
            "(one of the world's largest man-made lakes). The lake cruise is beautiful "
            "late afternoon.\n\n"
            "**Boti Falls** - a twin waterfall (male and female) in a lovely forest setting. "
            "About 45 min from Koforidua.\n\n"
            "**Getting there:** Very accessible from Accra - most destinations are "
            "1-2 hours by car or tro-tro."
        ),
    },
}

# ----- TOPICS -----
# General knowledge topics (non-region-specific).
# The "itinerary" topic has is_itinerary=True so it's handled by a separate function.
TOPICS = {
    "food": {
        "keywords": [
            "food",
            "eat",
            "jollof",
            "fufu",
            "banku",
            "waakye",
            "kelewele",
            "red red",
            "tilapia",
            "restaurant",
            "cuisine",
            "meal",
        ],
        "response": (
            "Ghanaian food is fantastic - hearty, spicy, and full of flavour. "
            "Here's what you need to try:\n\n"
            "- **Waakye** (wah-chay) - rice and beans with shito (spicy sauce), "
            "spaghetti, egg, fish, and fried plantain. Breakfast of champions.\n"
            "- **Fufu and light soup** - pounded cassava and plantain balls in "
            "tomato-based soup. Eat with your right hand - pinch, dip, swallow.\n"
            "- **Banku and tilapia** - fermented corn/cassava dough balls with "
            "grilled tilapia and pepper sauce. A Friday night classic.\n"
            "- **Jollof** - Ghana's version is spicier than Nigeria's. "
            "(And yes, Ghana's is better - ask any Ghanaian!)\n"
            "- **Kelewele** - spiced fried plantain chunks. Perfect street snack.\n\n"
            "**Where to eat:** Chop bars and roadside stalls have the most authentic food. "
            "In Accra, try Buka or Azmera for upmarket Ghanaian food."
        ),
    },
    "visa": {
        "keywords": [
            "visa",
            "passport",
            "entry",
            "immigration",
            "border",
        ],
        "response": (
            "**Visa info for Ghana:**\n\n"
            "Most nationalities need a visa to enter Ghana. You can apply online "
            "through the Ghana Immigration Service e-visa portal before you travel.\n\n"
            "**What you typically need:**\n"
            "- Valid passport (6+ months validity)\n"
            "- Completed online application\n"
            "- Passport photos\n"
            "- Proof of yellow fever vaccination (required!)\n"
            "- Return flight ticket\n\n"
            "Visa rules and fees change frequently, so always check the official "
            "Ghana Immigration Service website for current requirements."
        ),
    },
    "transport": {
        "keywords": [
            "transport",
            "tro-tro",
            "tro tro",
            "bus",
            "taxi",
            "uber",
            "bolt",
            "getting around",
            "get around",
            "travel between",
            "stc bus",
            "flight",
            "drive",
            "driving",
            "commute",
        ],
        "response": (
            "**Getting around Ghana:**\n\n"
            "- **Tro-tros** - shared minibuses, the most common and cheapest way to travel "
            "between towns. They leave when full, can be cramped, but they're an experience.\n"
            "- **Uber/Bolt** - work well in Accra and Kumasi. Reliable and reasonably priced.\n"
            "- **STC buses** - the most comfortable intercity option. Book ahead online.\n"
            "- **Domestic flights** - Accra-Kumasi-Tamale routes. Quick but more expensive.\n\n"
            "**Local tip:** Road travel is slower than distances suggest - Accra to Kumasi "
            "is 250km but takes 4-5 hours by bus. Factor in traffic and road conditions."
        ),
    },
    "safety": {
        "keywords": [
            "safe",
            "safety",
            "security",
            "scam",
            "danger",
            "risk",
            "crime",
        ],
        "response": (
            "**Safety in Ghana:**\n\n"
            "Ghana is one of the safest countries in West Africa for travellers. "
            "People are genuinely friendly and helpful.\n\n"
            "**Common-sense precautions:**\n"
            "- Watch your belongings in crowded markets and busy areas\n"
            "- Use registered taxis or ride-hailing apps (Uber/Bolt) at night\n"
            "- Don't walk alone on deserted beaches after dark\n"
            "- Be wary of 'helpful' strangers at bus stations offering to buy your ticket\n"
            "- Keep valuables in your hotel safe\n\n"
            "The most common 'scam' is price inflation for tourists - always agree on "
            "a price before getting into a taxi or buying from a market stall."
        ),
    },
    "best_time": {
        "keywords": [
            "best time",
            "weather",
            "season",
            "rainy",
            "dry",
            "when to go",
            "climate",
        ],
        "response": (
            "**Best time to visit Ghana:**\n\n"
            "The main dry season runs **November to March** - this is the best time "
            "for travel. The harmattan (dry, dusty wind from the Sahara) can reduce "
            "visibility but temperatures are pleasant.\n\n"
            "There's a shorter dry period in **August**.\n\n"
            "The rainy seasons (April-July and September-October) can make rural roads "
            "difficult and some attractions less accessible, but the landscape is "
            "incredibly green and there are fewer tourists.\n\n"
            "**For wildlife:** Visit Mole National Park in the dry season (Nov-Mar) "
            "when animals gather around waterholes.",
        ),
    },
    "culture": {
        "keywords": [
            "culture",
            "tradition",
            "festival",
            "etiquette",
            "custom",
            "homowo",
            "akwasidae",
            "hogbetsotso",
            "damba",
            "adinkra",
        ],
        "response": (
            "**Ghanaian culture and etiquette:**\n\n"
            "- **Greetings matter** - always greet people before asking for something. "
            "A simple 'Good morning' or 'Akwaaba' goes a long way.\n"
            "- **Right hand rule** - use your right hand to give, receive, eat, and point. "
            "The left hand is considered unclean.\n"
            "- **Dress modestly** at religious sites and in rural areas.\n"
            "- **Ask before photographing** people - it's polite and expected.\n"
            "- **Elder respect** - use your right hand when shaking hands, and "
            "you can support your right wrist with your left hand as a sign of respect.\n\n"
            "**Festivals:** Homowo (Ga), Akwasidae (Ashanti), Hogbetsotso (Anlo-Ewe), "
            "Damba (Northern). Dates vary yearly - check current schedules."
        ),
    },
    "language": {
        "keywords": [
            "language",
            "twi",
            "ga",
            "ewe",
            "speak",
            "phrase",
            "learn",
            "how to say",
            "pronounce",
        ],
        "response": (
            "**Useful Ghanaian phrases:**\n\n"
            "**Twi (Ashanti Region / widespread):**\n"
            "- Akwaaba - Welcome\n"
            "- Me daa ase - Thank you\n"
            "- Wo ho te sen? - How are you?\n"
            "- Me ho ye - I'm fine\n"
            "- Yoo - Okay / Alright\n\n"
            "**Ga (Accra region):**\n"
            "- Oshee - Well done / Greetings\n"
            "- Ny3 mi - I'm fine\n"
            "- Ete sen? - How is it?\n\n"
            "**Ewe (Volta Region):**\n"
            "- Woeez3 - Welcome\n"
            "- Akpe - Thank you\n"
            "- Efua? - How are you?\n\n"
            "Ghanaians appreciate any attempt at local phrases - even just 'Akwaaba' "
            "will get you smiles."
        ),
    },
    "itinerary": {
        "keywords": [
            "itinerary",
            "plan",
            "trip",
            "days",
            "route",
            "schedule",
            "tour",
        ],
        "response": None,
        "is_itinerary": True,  # flag: handled by get_itinerary_reply() instead
    },
}

# Default advice shown when no specific trip details are given
ITINERARY_ADVICE = (
    "I'd love to help plan your Ghana itinerary! To give you the best advice, I need:\n\n"
    "1. **How many days** do you have?\n"
    "2. **What are your interests?** (history, nature, beaches, culture, food)\n"
    "3. **What's your pace?** (packed schedule or relaxed)\n"
    "4. **Where are you starting from?** (usually Accra)\n\n"
    "Here's a **classic 5-day Ghana loop** to give you ideas:\n\n"
    "**Day 1-2: Accra** - Jamestown, Osu, Labadi Beach, Kwame Nkrumah Mausoleum\n"
    "**Day 3: Cape Coast** - Cape Coast Castle, Kakum National Park canopy walkway\n"
    "**Day 4: Kumasi** - Manhyia Palace, Kejetia Market, Bonwire kente village\n"
    "**Day 5: Return to Accra** - stop at Akosombo/Lake Volta on the way\n\n"
    "For longer trips (10+ days), you can add Mole National Park in the north "
    "or the Volta Region for hiking and waterfalls."
)


# Generates a personalised itinerary based on the user's message.
# Extracts day count, number of people, and interests from the text.
def get_itinerary_reply(message: str) -> str:
    days = re.findall(r"(\d+)\s*days?", message.lower())
    people = re.findall(r"(\d+)\s*(people|persons?|of us|travellers?)", message.lower())

    interests = []
    interest_keywords = {
        "history": ["history", "castle", "heritage", "slave", "colonial"],
        "nature": [
            "nature",
            "hiking",
            "waterfall",
            "park",
            "wildlife",
            "safari",
            "beach",
        ],
        "beach": ["beach", "swim", "surf", "coast"],
        "culture": ["culture", "festival", "tradition", "kente", "ashanti"],
        "food": ["food", "eat", "cooking", "cuisine"],
    }
    for category, keywords in interest_keywords.items():
        if any(k in message.lower() for k in keywords):
            interests.append(category)

    day_count = int(days[0]) if days else None

    if day_count:
        if day_count <= 3:
            return (
                f"With {day_count} days, I'd focus on **Accra and Cape Coast** - "
                "they're close enough to avoid wasting time on the road.\n\n"
                "**Day 1: Accra** - arrive, settle in, explore Jamestown and Osu\n"
                "**Day 2: Cape Coast** - Cape Coast Castle + Kakum canopy walkway\n"
                "**Day 3: Accra** - Labadi Beach, Kwame Nkrumah Mausoleum, departure\n\n"
                "This keeps travel manageable and hits the highlights!"
            )
        elif day_count <= 7:
            return (
                f"Great - {day_count} days gives you room for **Accra, Cape Coast, and Kumasi**.\n\n"
                f"**Day 1:** Arrive Accra, settle in\n"
                f"**Day 2:** Accra - Jamestown, Osu, independence square\n"
                f"**Day 3:** Cape Coast - castle tour + Elmina\n"
                f"**Day 4:** Kakum canopy walkway, then drive toward Kumasi\n"
                f"**Day 5:** Kumasi - Manhyia Palace, Kejetia Market\n"
                f"**Day 6:** Bonwire kente village, return to Accra\n"
                f"**Day 7:** Relax at Labadi Beach or departure\n\n"
                f"This is a manageable loop. Want me to adjust anything?"
            )
        else:
            return (
                f"{day_count} days is plenty for a thorough Ghana trip! "
                "You can add the **Volta Region** or **Mole National Park**.\n\n"
                "Would you like me to focus more on nature, history, or a mix? "
                "Tell me your preferences and I'll build a detailed plan."
            )

    return ITINERARY_ADVICE


# Handles practical-advice topics (cost, SIM cards, etc.)
# These are checked separately from the main TOPICS because they need dynamic info.
def get_practical_reply(message: str) -> str | None:
    money_keywords = [
        "cost",
        "price",
        "money",
        "expensive",
        "cheap",
        "budget",
        "how much",
        "cedi",
    ]
    if any(k in message.lower() for k in money_keywords):
        return (
            "**Money in Ghana:**\n\n"
            "The currency is the **Ghanaian Cedi (GHS)**. "
            "ATMs work in cities (Ecobank, Stanbic are reliable); less so in rural areas.\n\n"
            "**Rough daily budgets:**\n"
            "- Budget traveller: $30-50/day\n"
            "- Mid-range: $60-120/day\n"
            "- Luxury: $150+/day\n\n"
            "Exchange rates fluctuate a lot, so check xe.com for the current rate "
            "before you go. US dollars are easily exchanged at forex bureaus "
            "(better rates than hotels)."
        )

    sim_keywords = [
        "sim",
        "phone",
        "mobile",
        "data",
        "internet",
        "network",
        "mtn",
        "vodafone",
    ]
    if any(k in message.lower() for k in sim_keywords):
        return (
            "**SIM cards in Ghana:**\n\n"
            "You can buy a SIM at the airport or any MTN/Vodafone/AirtelTigo shop. "
            "You'll need your passport for registration.\n\n"
            "**MTN** has the best coverage nationwide, including rural areas. "
            "Data is cheap - around GHS 30-50 (about $2.50-4) for a decent weekly bundle.\n\n"
            "**Pro tip:** Buy your SIM at the airport MTN booth when you arrive - "
            "it's quick and they handle registration on the spot."
        )

    return None


def get_web_reply() -> str | None:
    return None
