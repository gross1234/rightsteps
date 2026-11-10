#!/usr/bin/env python3
"""
Convivial Concierge - SEO / AEO site + account-based pages generator.

Reads the Homebase "Family Offices Investing in CRE" CSV and writes a static site
into ../ (the convivial/ folder):

  index.html                      home (indexable)
  family-offices/                 pillar page for family-office owners (indexable)
  solutions/<asset-class>/        one page per property type we serve (indexable)
  markets/<metro>/                one page per metro where these offices own/invest (indexable)
  for/<family-office>/            one private proposal page per family office (noindex)
  for/<family-office>/<property>/ one page per individual property (noindex, optional --properties)
  sitemap.xml, robots.txt, llms.txt

and, outside the site, an outreach CSV (--outreach) that maps every family office to
its fit score, its proposal URL, the best public page, and a personalised opener.

Usage:
  python3 convivial/_build/build.py --csv family_offices.csv \
      [--properties convivial/_build/properties.csv] [--outreach outreach.csv]

Standard library only.
"""
import argparse, csv, datetime, html, json, os, re, shutil, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)  # convivial/
CFG = json.load(open(os.path.join(HERE, "config.json")))
TODAY = datetime.date.today().isoformat()
BRAND = CFG["brand"]
BASE = CFG["base_url"].rstrip("/")

# --------------------------------------------------------------------------------------
# Property types. `fit` (0-5) = how naturally concierge sells into this asset class.
# Copy here is the source for every solution page, proposal page and FAQ answer.
# REVIEW IT: it should only promise services Convivial actually delivers.
# --------------------------------------------------------------------------------------
SEGMENTS = {
    "multifamily": {
        "name": "Multifamily & luxury residential",
        "short": "multifamily",
        "fit": 5,
        "kw": ["multifamily", "multi-family", "apartment", "residential", "sfr", "single-family",
               "condo", "workforce", "affordable", "co-living", "branded residence", "build-to-rent",
               "rental", "luxury residential", "housing"],
        "h1": "Resident concierge for multifamily and luxury residential properties",
        "title": "Resident Concierge Services for Apartments & Luxury Multifamily",
        "answer": ("Convivial Concierge runs resident concierge for apartment, condo and build-to-rent "
                   "communities: front-desk hospitality, package and errand handling, move-in welcomes, "
                   "resident events and on-demand requests. Owners use it to support renewals and premium "
                   "positioning without adding headcount to the property management team."),
        "people": "residents",
        "programs": [
            ("Front-desk hospitality", "Hosts at the lobby desk, or a virtual concierge for smaller buildings, who greet residents and guests by name."),
            ("Packages, deliveries and errands", "Package intake, dry cleaning, grocery and pet-care coordination handled before it reaches the leasing office."),
            ("Move-in and renewal moments", "Welcome arrivals, neighbourhood guides and small touches timed around the renewal window."),
            ("Resident events and community", "A monthly calendar that gets neighbours to know each other, which is what makes people stay."),
            ("On-demand requests", "Dinner reservations, home services and travel help booked through one trusted contact."),
        ],
        "outcomes": ["A stronger renewal conversation", "An amenity story that supports premium rents",
                     "Fewer non-maintenance requests landing on the leasing team",
                     "Monthly reporting on requests, response times and resident sentiment"],
        "faq": [
            ("What does a resident concierge do in an apartment building?",
             "A resident concierge is the building's host. They greet residents and guests, take in packages, handle errands and reservations, run community events and act as one point of contact for anything that is not a maintenance ticket. The goal is that living in the building feels like staying at a good hotel."),
            ("Is concierge worth it for a mid-size multifamily property?",
             "Usually, if the staffing model fits the building. Mid-size communities often use a hybrid model with part-time on-site hours plus a virtual concierge, which keeps cost per door low while still giving residents a person to call."),
            ("How is a concierge different from property management?",
             "Property management runs leasing, rent, maintenance and compliance. Concierge runs the resident experience. Convivial works alongside your existing or third-party property manager rather than replacing them."),
            ("Can concierge be added to a building we just acquired?",
             "Yes. Adding concierge is one of the fastest ways to reposition a value-add acquisition, because it changes how the building feels in the first 90 days without any capital work."),
            ("How is a resident concierge program priced?",
             "Each property is scoped on its own. Pricing depends on unit count, hours of coverage and whether the desk is staffed, virtual or hybrid. Request a proposal for a specific property to get a number."),
        ],
    },
    "mixed_use": {
        "name": "Mixed-use districts & master-planned communities",
        "short": "mixed-use",
        "fit": 5,
        "kw": ["mixed-use", "mixed use", "master-planned", "master planned", "urban infill", "district"],
        "h1": "Concierge for mixed-use districts and master-planned communities",
        "title": "Concierge Services for Mixed-Use Developments & Master-Planned Communities",
        "answer": ("Convivial Concierge gives a mixed-use property one hospitality team that serves residents, "
                   "office tenants, shoppers and visitors at once. That covers guest services, district events, "
                   "retailer partnerships and resident and tenant concierge, so the place feels run as one "
                   "neighbourhood rather than as separate buildings."),
        "people": "residents, tenants and visitors",
        "programs": [
            ("One team across every use", "The same hosts serve the residential lobby, the office lobby and the plaza, so service is consistent everywhere."),
            ("District events and programming", "Markets, seasonal events and tenant mixers that bring foot traffic to your retail."),
            ("Retail and restaurant partnerships", "Resident and tenant perks with your own retailers, so spending stays on site."),
            ("Visitor and guest services", "Wayfinding, parking help, deliveries and a welcome for first-time visitors."),
            ("Owner and VIP services", "White-glove handling for principals, investors and VIP tenants touring the property."),
        ],
        "outcomes": ["A district that feels managed as one place", "Footfall and dwell time for the retail",
                     "A differentiator in residential and office leasing", "One report across all uses"],
        "faq": [
            ("What does a concierge do at a mixed-use development?",
             "A mixed-use concierge team serves everyone on site: residents, office tenants, shoppers and visitors. They run guest services, events, retailer partnerships and day-to-day requests so the whole district feels like one hospitality-led place."),
            ("Why use one concierge provider across a mixed-use property?",
             "One provider means one standard of service, one events calendar and one report. It also lets resident and tenant perks drive spending at your own retailers instead of competing with them."),
            ("Can concierge help lease up retail in a mixed-use project?",
             "It helps by creating reasons to visit, such as events, perks and programming that build traffic. Prospective retail tenants see an active, managed place rather than an empty ground floor."),
            ("Do you work with the master developer or the property managers?",
             "Either. Convivial typically reports to the owner or master developer and coordinates day to day with each building's property manager."),
            ("How is mixed-use concierge priced?",
             "It is scoped by the uses on site, hours of coverage and number of desks. Request a proposal for the specific district."),
        ],
    },
    "hospitality": {
        "name": "Hotels, resorts & branded residences",
        "short": "hospitality",
        "fit": 5,
        "kw": ["hotel", "hospitality", "resort", "marina", "golf", "boutique"],
        "h1": "Guest concierge and experience programs for hotels, resorts and branded residences",
        "title": "Outsourced Hotel Concierge & Guest Experience Services",
        "answer": ("Convivial Concierge staffs, extends or fully runs the concierge desk for hotels, resorts and "
                   "branded residences. That means local experience curation, VIP arrivals, reservations, seasonal "
                   "coverage and owner services for residence buyers, all delivered to your brand standard."),
        "people": "guests and owners",
        "programs": [
            ("Concierge desk staffing", "Full or partial coverage of the desk, including seasonal peaks and overnight."),
            ("Local experience curation", "A vetted book of restaurants, guides and experiences, kept current."),
            ("VIP arrivals and special occasions", "Pre-arrival planning, amenities and in-stay surprises for your highest-value guests."),
            ("Branded residence owner services", "Year-round concierge for residence owners, including when they are not in town."),
            ("Group and event support", "Itineraries and on-site hosting for weddings, retreats and corporate groups."),
        ],
        "outcomes": ["Guest review scores that mention people by name", "Concierge coverage without full-time headcount",
                     "A sales story for branded residences", "Reporting on requests and guest feedback"],
        "faq": [
            ("Can a hotel outsource its concierge desk?",
             "Yes. Many independent and family-owned hotels outsource all or part of the concierge desk to a specialist, which gives them trained coverage and a curated local network without carrying full-time headcount through slow seasons."),
            ("What do branded residence owners expect from concierge?",
             "Owners expect hotel-level service at home: reservations, home readiness before arrival, help with deliveries and vendors, and someone who knows them. Convivial provides that year-round, including while owners are away."),
            ("Will outsourced concierge follow our brand standards?",
             "It should. Convivial trains to your service standards, scripts and uniform, so guests experience your brand rather than ours."),
            ("Do you cover seasonal or overnight shifts?",
             "Coverage is set property by property, including seasonal peaks and extended hours."),
            ("How is hotel concierge priced?",
             "By hours of coverage, number of positions and scope. Request a proposal for a specific property."),
        ],
    },
    "office": {
        "name": "Office & tenant experience",
        "short": "office",
        "fit": 4,
        "kw": ["office", "class a"],
        "h1": "Tenant experience and lobby concierge for office buildings",
        "title": "Office Building Concierge & Tenant Experience Services",
        "answer": ("Convivial Concierge runs lobby hospitality, visitor welcome, amenity-floor hosting, tenant events "
                   "and workplace requests for office buildings. Owners use it to compete in the flight to quality, "
                   "to make tours feel hospitality-grade and to give tenants a reason to come in and renew."),
        "people": "tenants and their guests",
        "programs": [
            ("Lobby hospitality and visitor welcome", "A host instead of a security desk: guests are greeted, registered and walked up."),
            ("Amenity floor hosting", "Staffing for lounges, conference centres, fitness and rooftop spaces so they actually get used."),
            ("Tenant events and programming", "Regular events that make the building a community and bring people back to the office."),
            ("Workplace requests", "Reservations, gifts, car service and errands for tenant employees and executives."),
            ("Leasing tour support", "A hospitality-led welcome for every broker tour."),
        ],
        "outcomes": ["Tours that feel like walking into a hotel", "Amenities that tenants actually use",
                     "A better renewal conversation", "Data on tenant engagement for the leasing team"],
        "faq": [
            ("What is tenant experience in commercial real estate?",
             "Tenant experience is everything a tenant's employees and guests feel in the building beyond the lease: the welcome in the lobby, the amenities, events and services. In a flight-to-quality market it is a leasing and retention tool, not a nice-to-have."),
            ("What does an office building concierge do?",
             "An office concierge greets and registers visitors, hosts the amenity spaces, runs tenant events and handles requests such as reservations, gifts and car service for tenant employees."),
            ("Does concierge help office leasing?",
             "It helps on two fronts. Tours feel hospitality-grade, which matters to decision makers comparing Class A options, and engaged tenants are easier to renew."),
            ("Can concierge replace our security desk?",
             "Concierge usually works alongside security. Some owners move to a hospitality-forward front desk with security in a supporting role. That is a decision made per building."),
            ("How is office concierge priced?",
             "By building size, desk hours and amenity scope. Request a proposal for a specific building."),
        ],
    },
    "senior": {
        "name": "Senior living",
        "short": "senior living",
        "fit": 4,
        "kw": ["senior", "assisted living", "independent living", "55+", "active adult"],
        "h1": "Lifestyle concierge for senior living and active-adult communities",
        "title": "Concierge & Lifestyle Services for Senior Living Communities",
        "answer": ("Convivial Concierge provides non-clinical lifestyle concierge for senior living and active-adult "
                   "communities: errands, transportation booking, outings, events and coordination with residents' "
                   "families. Care stays with your operator; we make daily life feel more like a good hotel."),
        "people": "residents and their families",
        "programs": [
            ("Lifestyle concierge", "Appointments, reservations, gifts and errands, handled by a familiar face."),
            ("Outings and events", "Calendars of trips, classes and social events that residents look forward to."),
            ("Family coordination", "A point of contact for families arranging visits, deliveries and celebrations."),
            ("Transportation booking", "Rides and drivers arranged and confirmed."),
            ("Move-in welcome", "A gentler first month for new residents and their families."),
        ],
        "outcomes": ["A hospitality story that helps sales tours", "Happier families", "Less non-care work on care staff",
                     "Reporting on resident requests and engagement"],
        "faq": [
            ("Is concierge in senior living a clinical service?",
             "No. Convivial's concierge is non-clinical lifestyle and hospitality service. Care and medical services stay with your licensed operator."),
            ("What does a senior living concierge do?",
             "They handle errands, appointments, transportation booking, outings and events, and they act as a point of contact for families."),
            ("Does concierge help senior living occupancy?",
             "It gives sales teams a tangible hospitality story on tours and keeps residents and families happier, which supports referrals."),
            ("Can you work alongside our operator?",
             "Yes. Concierge coordinates with your operator's staff and does not replace them."),
            ("How is senior living concierge priced?",
             "By community size and hours. Request a proposal for a specific community."),
        ],
    },
    "student": {
        "name": "Student housing",
        "short": "student housing",
        "fit": 4,
        "kw": ["student"],
        "h1": "Resident concierge for purpose-built student housing",
        "title": "Concierge Services for Purpose-Built Student Housing",
        "answer": ("Convivial Concierge runs move-in day operations, high-volume package handling, community events "
                   "and parent communications for purpose-built student housing, so the leasing team can focus on "
                   "pre-leasing for next year."),
        "people": "students and parents",
        "programs": [
            ("Move-in day operations", "Scheduling, welcome and hosting for the busiest weekend of the year."),
            ("Package room management", "High-volume intake and pickup that does not swamp the front desk."),
            ("Community events", "Events that build a community and drive word-of-mouth pre-leasing."),
            ("Parent communications", "A trusted contact that parents can reach."),
            ("Front-desk hospitality", "Staffed or virtual coverage for extended hours."),
        ],
        "outcomes": ["Smoother move-in", "Word-of-mouth that helps pre-leasing", "Leasing staff freed from the package room",
                     "Reporting by semester"],
        "faq": [
            ("What does concierge do in student housing?",
             "Concierge runs the front desk, packages, move-in logistics and community events, and is a point of contact for parents."),
            ("Does concierge help student housing pre-leasing?",
             "Residents who enjoy the community renew and refer friends, and a well-run move-in is a strong first impression."),
            ("Can you staff just move-in season?",
             "Yes. Coverage can be scoped seasonally or year-round."),
            ("Do you work alongside our property manager?",
             "Yes. Concierge complements the on-site management team."),
            ("How is student housing concierge priced?",
             "By bed count, hours and season. Request a proposal for a specific property."),
        ],
    },
    "life_science": {
        "name": "Life science, medical office & healthcare",
        "short": "life science and medical office",
        "fit": 3,
        "kw": ["life science", "lab", "r&d", "medical", "healthcare", "ambulatory", "behavioral health"],
        "h1": "Concierge for life science campuses and medical office buildings",
        "title": "Concierge Services for Life Science Campuses & Medical Office Buildings",
        "answer": ("Convivial Concierge provides lobby hosting, patient and visitor wayfinding, amenity programming and "
                   "tenant services for life science campuses and medical office buildings, so the people arriving "
                   "find the building calm and easy to use."),
        "people": "tenants, patients and visitors",
        "programs": [
            ("Visitor and patient welcome", "Greeting, wayfinding and escort for first-time visitors."),
            ("Campus amenity programming", "Events and hosted spaces that help life science tenants recruit and retain staff."),
            ("Tenant services", "Reservations, deliveries and errands for tenant teams."),
            ("Tour support", "A hospitality-grade welcome for leasing tours."),
        ],
        "outcomes": ["A calmer arrival experience", "A recruiting tool for tenants", "Better tours", "Engagement reporting"],
        "faq": [
            ("Do medical office buildings use concierge?",
             "Increasingly, yes. A lobby host who handles wayfinding and welcome makes a medical office building easier for patients to use and reflects well on every practice in it."),
            ("What does a life science campus concierge do?",
             "They host amenity spaces, run campus events and handle tenant requests, which helps tenants compete for scientific talent."),
            ("Is this a clinical or security service?",
             "No. It is a hospitality service that works alongside your security and building operations."),
            ("How is it priced?",
             "By building, hours and scope. Request a proposal for a specific property."),
        ],
    },
    "retail": {
        "name": "Retail centres & lifestyle destinations",
        "short": "retail",
        "fit": 3,
        "kw": ["retail", "shopping", "grocery", "lifestyle center", "entertainment"],
        "h1": "Guest services and concierge for retail centres and lifestyle destinations",
        "title": "Guest Services & Concierge for Shopping Centers and Lifestyle Destinations",
        "answer": ("Convivial Concierge runs guest services for retail centres and lifestyle destinations: a staffed "
                   "guest-services desk, hands-free shopping, events, visitor and tourism programs and retailer "
                   "support, so shoppers stay longer and come back."),
        "people": "shoppers and retailers",
        "programs": [
            ("Guest services desk", "Information, gift cards, lost and found, stroller and wheelchair loans."),
            ("Hands-free shopping and carry-out", "Purchases held and delivered to the car, home or hotel."),
            ("Events and activations", "Seasonal programming that gives people a reason to visit."),
            ("Visitor and tourism programs", "Hotel and tour partnerships that bring visitors in."),
            ("Retailer support", "A hospitality partner for the retailers on site."),
        ],
        "outcomes": ["Longer visits", "A destination story for leasing", "Happier retailers", "Footfall and request reporting"],
        "faq": [
            ("What do guest services do at a shopping centre?",
             "Guest services handle information, gift cards, lost and found, mobility and stroller loans, hands-free shopping and events, so visitors have an easier, longer visit."),
            ("Can concierge increase shopping centre traffic?",
             "Programming and visitor partnerships give people reasons to come and stay longer. That is the part concierge directly drives."),
            ("Do you staff guest-services desks?",
             "Yes. Coverage is scoped per centre."),
            ("How is it priced?",
             "By hours, desks and programming scope. Request a proposal for a specific centre."),
        ],
    },
    "industrial": {
        "name": "Industrial & logistics",
        "short": "industrial",
        "fit": 1,
        "kw": ["industrial", "logistics", "warehouse", "distribution", "flex", "cold storage", "data center",
               "manufacturing"],
        "page": False,
    },
    "storage": {
        "name": "Self-storage, land & net lease",
        "short": "self-storage",
        "fit": 0,
        "kw": ["self-storage", "storage facilit", "land", "net lease", "nnn", "parking", "farmland", "timber",
               "ranch", "mobile home", "manufactured housing", "agricultur"],
        "page": False,
    },
}
SERVED = [k for k, s in SEGMENTS.items() if s.get("page", True)]

# Metro normalisation. Matched against HQ city and the free-text geographic focus.
METROS = {
    "new-york": ("New York City", "NY", ["new york", "nyc", "manhattan", "brooklyn", "queens", "bronx", "greenwich",
                                          "stamford", "westchester", "long island", "rye", "scarsdale", "jersey city",
                                          "hoboken", "tri-state"],
                 ["Manhattan", "Brooklyn", "Long Island City", "Westchester", "Greenwich and Stamford", "Jersey City"]),
    "south-florida": ("South Florida", "FL", ["miami", "fort lauderdale", "boca raton", "palm beach", "coral gables",
                                               "aventura", "south florida", "delray", "bal harbour", "sunny isles",
                                               "brickell", "hollywood, fl"],
                      ["Brickell", "Miami Beach", "Coral Gables", "Fort Lauderdale", "Boca Raton", "Palm Beach"]),
    "dallas-fort-worth": ("Dallas-Fort Worth", "TX", ["dallas", "fort worth", "plano", "frisco", "irving", "dfw",
                                                     "las colinas", "southlake"],
                          ["Uptown", "Victory Park", "Las Colinas", "Plano", "Frisco", "Fort Worth"]),
    "houston": ("Houston", "TX", ["houston", "the woodlands", "sugar land"],
                ["Downtown", "Galleria", "River Oaks", "The Woodlands", "Energy Corridor"]),
    "austin": ("Austin", "TX", ["austin"], ["Downtown", "The Domain", "East Austin", "South Congress"]),
    "san-antonio": ("San Antonio", "TX", ["san antonio"], ["Downtown", "The Pearl", "Stone Oak"]),
    "chicago": ("Chicago", "IL", ["chicago", "evanston", "oak brook", "northbrook", "lake forest"],
                ["The Loop", "River North", "West Loop", "Gold Coast", "North Shore"]),
    "atlanta": ("Atlanta", "GA", ["atlanta", "buckhead", "alpharetta"],
                ["Buckhead", "Midtown", "Alpharetta", "Perimeter Center"]),
    "los-angeles": ("Los Angeles", "CA", ["los angeles", "beverly hills", "santa monica", "pasadena", "century city",
                                         "west hollywood", "malibu", "culver city"],
                    ["Beverly Hills", "Century City", "Santa Monica", "Downtown LA", "Pasadena"]),
    "orange-county": ("Orange County", "CA", ["newport beach", "irvine", "orange county", "costa mesa"],
                      ["Newport Beach", "Irvine", "Costa Mesa"]),
    "san-diego": ("San Diego", "CA", ["san diego", "la jolla"], ["Downtown", "La Jolla", "UTC"]),
    "bay-area": ("San Francisco Bay Area", "CA", ["san francisco", "palo alto", "menlo park", "cupertino",
                                                  "san jose", "oakland", "silicon valley", "bay area", "atherton",
                                                  "woodside", "mountain view"],
                 ["San Francisco", "Palo Alto", "Menlo Park", "San Jose", "Oakland"]),
    "seattle": ("Seattle", "WA", ["seattle", "bellevue", "kirkland", "redmond", "puget sound"],
                ["Downtown", "South Lake Union", "Bellevue", "Kirkland"]),
    "boston": ("Boston", "MA", ["boston", "cambridge", "wellesley"],
               ["Back Bay", "Seaport", "Cambridge", "Wellesley"]),
    "washington-dc": ("Washington, DC", "DC", ["washington", "bethesda", "arlington", "mclean", "alexandria",
                                               "chevy chase", "dc metro", "northern virginia", "tysons"],
                      ["Downtown DC", "Georgetown", "Bethesda", "Arlington", "Tysons"]),
    "denver": ("Denver", "CO", ["denver", "boulder", "aspen", "vail"], ["LoDo", "Cherry Creek", "RiNo", "Boulder"]),
    "phoenix-scottsdale": ("Phoenix & Scottsdale", "AZ", ["phoenix", "scottsdale", "tempe", "paradise valley"],
                           ["Scottsdale", "Downtown Phoenix", "Tempe", "Paradise Valley"]),
    "tampa-bay": ("Tampa Bay", "FL", ["tampa", "st. petersburg", "st petersburg", "clearwater", "sarasota"],
                  ["Downtown Tampa", "Water Street", "St. Petersburg", "Sarasota"]),
    "southwest-florida": ("Naples & Southwest Florida", "FL", ["naples", "fort myers", "southwest florida", "marco island"],
                          ["Naples", "Fort Myers", "Bonita Springs"]),
    "nashville": ("Nashville", "TN", ["nashville", "franklin, tn"], ["The Gulch", "Downtown", "Midtown", "Franklin"]),
    "charlotte": ("Charlotte", "NC", ["charlotte"], ["Uptown", "SouthPark", "South End"]),
    "philadelphia": ("Philadelphia", "PA", ["philadelphia", "main line"], ["Center City", "University City", "Main Line"]),
    "minneapolis": ("Minneapolis-St. Paul", "MN", ["minneapolis", "st. paul", "twin cities"],
                    ["Downtown Minneapolis", "North Loop", "St. Paul"]),
    "salt-lake-city": ("Salt Lake City", "UT", ["salt lake", "park city", "lehi"], ["Downtown", "Park City", "Lehi"]),
    "orlando": ("Orlando", "FL", ["orlando", "winter park"], ["Downtown", "Winter Park", "Lake Nona"]),
}
MIN_OFFICES_FOR_MARKET_PAGE = 5

# --------------------------------------------------------------------------------------
esc = html.escape


def slugify(s):
    s = re.sub(r"\(.*?\)", "", s).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:70].strip("-") or "office"


def cta_href():
    if CFG.get("booking_url"):
        return CFG["booking_url"]
    return "mailto:" + CFG["contact_email"]


def cta_href_for(subject):
    if CFG.get("booking_url"):
        return CFG["booking_url"]
    from urllib.parse import quote
    return "mailto:%s?subject=%s" % (CFG["contact_email"], quote(subject))


def segments_for(text):
    t = " " + text.lower() + " "
    found = []
    for key, s in SEGMENTS.items():
        for kw in s["kw"]:
            if kw == "land":
                hit = re.search(r"\bland\b", t) is not None
            elif kw == "lab":
                hit = re.search(r"\blab\b", t) is not None
            else:
                hit = kw in t
            if hit:
                found.append(key)
                break
    # "senior housing" / "student housing" should not also count as generic multifamily
    if ("senior" in found or "student" in found) and "multifamily" in found:
        cleaned = re.sub(r"(senior|student) housing", "", t)
        if not any(kw in cleaned for kw in SEGMENTS["multifamily"]["kw"]):
            found.remove("multifamily")
    if not found and re.search(r"commercial|diversified|real estate|\bre\b|cre", t):
        found = ["office", "mixed_use"]
        return found, True
    return found, False


def metros_for(*texts):
    t = " ".join(x.lower() for x in texts if x)
    out = []
    for key, (_, _, kws, _) in METROS.items():
        for kw in kws:
            if kw == "washington" and "washington state" in t:
                continue
            if re.search(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])", t):
                out.append(key)
                break
    return out


def load_offices(path):
    rows = list(csv.reader(open(path, encoding="utf-8-sig")))
    hi = next(i for i, r in enumerate(rows) if r and r[0].strip() == "#")
    hdr = [h.strip() for h in rows[hi]]
    offices, seen = [], Counter()
    for r in rows[hi + 1:]:
        if not r or not r[0].strip().isdigit():
            continue
        d = {k: (v or "").strip() for k, v in zip(hdr, r)}
        name = d["Family Office Name"]
        if not name:
            continue
        slug = slugify(name)
        seen[slug] += 1
        if seen[slug] > 1:
            slug = "%s-%d" % (slug, seen[slug])
        segs, guessed = segments_for(d["RE Asset Classes"])
        hq = d["HQ City"] if d["HQ City"].lower() not in ("unknown", "undisclosed", "") else ""
        hq_metros = metros_for(hq + ", " + d["HQ State"]) if hq else []
        focus_metros = metros_for(d["Geographic Focus"])
        mets = list(dict.fromkeys(hq_metros + focus_metros))
        served = [s for s in segs if s in SERVED]
        served.sort(key=lambda s: -SEGMENTS[s]["fit"])
        fit = score(d, segs, guessed)
        offices.append(dict(row=d, name=name, slug=slug, segs=segs, served=served, guessed=guessed,
                            metros=mets, hq_metros=hq_metros, fit=fit))
    return offices


def score(d, segs, guessed):
    """0-100 fit score: how good a target this office is for property concierge."""
    best = 2.5 if guessed else max([SEGMENTS[s]["fit"] for s in segs] or [0])
    breadth = 0 if guessed else sum(1 for s in segs if SEGMENTS[s]["fit"] >= 3)
    sc = best * 10 + min(breadth, 3) * 4
    style = (d.get("Investment Style", "") + " " + d.get("Notes", "")).lower()
    if re.search(r"\bhold\b|long-term|long term|operat|own and manage|owner-operat|generational|legacy", style):
        sc += 12  # owners who hold and operate buy services; pure allocators don't
    if "direct" in style:
        sc += 6
    elif re.search(r"\bfund\b|\blp\b|allocat|passive", style):
        sc -= 10
    ac = d.get("RE Asset Classes", "").lower()
    if re.search(r"credit|debt|mezzanine|lending", ac) and (guessed or best < 3):
        sc -= 25
    sc += {"Tier 1": 10, "Tier 2": 5}.get(d.get("Tier", ""), 0)
    return int(max(0, min(100, sc)))


def possessive(name):
    return name + ("'" if name.endswith("s") else "'s")


# --------------------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------------------
def rel(depth):
    return "../" * depth if depth else "./"


def jsonld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


ORG = {
    "@type": "Organization",
    "@id": BASE + "/#org",
    "name": BRAND,
    "legalName": CFG["legal_name"],
    "url": BASE + "/",
    "email": CFG["contact_email"],
    "slogan": CFG["tagline"],
    "areaServed": CFG["areas_served"],
    "knowsAbout": ["resident concierge", "tenant experience", "property concierge services",
                   "hospitality services for real estate", "amenity programming", "family office real estate"],
}
if CFG.get("phone"):
    ORG["telephone"] = CFG["phone"]


def page(path, depth, title, desc, body, schema=None, index=True, crumbs=None):
    canonical = BASE + "/" + path
    r = rel(depth)
    graph = [ORG]
    if crumbs:
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + "/" + p}
            for i, (n, p) in enumerate(crumbs)]})
    graph += schema or []
    robots = "index,follow,max-snippet:-1" if index else "noindex,nofollow"
    crumb_html = ""
    if crumbs and len(crumbs) > 1:
        parts = []
        for n, p in crumbs[:-1]:
            parts.append('<a href="%s%s">%s</a>' % (r, p, esc(n)))
        parts.append("<span>%s</span>" % esc(crumbs[-1][0]))
        crumb_html = '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>' % " / ".join(parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(BRAND)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/site.css">
{jsonld({"@context": "https://schema.org", "@graph": graph})}
</head>
<body>
<header class="top"><div class="wrap">
<a class="logo" href="{r}">{esc(BRAND)}</a>
<nav><a href="{r}family-offices/">Family offices</a><a href="{r}solutions/">Property types</a><a href="{r}markets/">Markets</a><a class="btn sm" href="{esc(cta_href())}">Request a proposal</a></nav>
</div></header>
<main class="wrap">
{crumb_html}
{body}
</main>
<footer><div class="wrap">
<p><strong>{esc(BRAND)}</strong>, {esc(CFG["tagline"])}</p>
<p><a href="{r}family-offices/">For family offices</a> · <a href="{r}solutions/">Property types</a> · <a href="{r}markets/">Markets</a> · <a href="mailto:{esc(CFG["contact_email"])}">{esc(CFG["contact_email"])}</a></p>
<p class="fine">© {datetime.date.today().year} {esc(CFG["legal_name"])} dba {esc(BRAND)}. Updated {TODAY}.</p>
</div></footer>
</body>
</html>
"""


def faq_html(faqs):
    out = ['<section class="faq"><h2>Frequently asked questions</h2>']
    for q, a in faqs:
        out.append('<details><summary><h3>%s</h3></summary><p>%s</p></details>' % (esc(q), esc(a)))
    out.append("</section>")
    return "\n".join(out)


def faq_schema(faqs, url):
    return {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}


def service_schema(name, desc, url, audience=None, area=None):
    s = {"@type": "Service", "@id": url + "#service", "name": name, "description": desc,
         "serviceType": "Property concierge services", "provider": {"@id": BASE + "/#org"},
         "url": url, "areaServed": area or CFG["areas_served"]}
    if audience:
        s["audience"] = {"@type": "BusinessAudience", "audienceType": audience}
    return s


def answer_box(text):
    return '<div class="answer"><p class="eyebrow">The short answer</p><p>%s</p></div>' % esc(text)


def program_grid(programs):
    return '<div class="grid">' + "".join(
        '<div class="card"><h3>%s</h3><p>%s</p></div>' % (esc(t), esc(d)) for t, d in programs) + "</div>"


def write(rel_path, content):
    full = os.path.join(SITE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


FO_FAQ = [
    ("Why do family offices use concierge services for their real estate?",
     "Family offices tend to hold buildings for decades, so the reputation of each property is tied to the family name. A hospitality-grade concierge program protects that reputation, supports renewals and premium rents, and gives the family one consistent standard of service across the portfolio, whoever the property manager is."),
    ("How should a family office roll out concierge across a portfolio?",
     "Start with one property where residents or tenants are most visible, such as a flagship residential tower, a Class A office lobby or a mixed-use district. Run a 90-day pilot with clear measures, then roll the same standard out to the rest of the portfolio."),
    ("Does Convivial Concierge replace our property manager?",
     "No. Convivial works alongside your in-house team or third-party property manager. Property management keeps leasing, maintenance and compliance; Convivial runs the resident, tenant and guest experience."),
    ("Which property types benefit most from concierge?",
     "Multifamily and luxury residential, mixed-use districts, hotels and branded residences, and Class A office benefit most. Senior living, student housing, medical office and retail centres also benefit with programs scoped for them."),
    ("What does the family office receive as owner?",
     "A monthly report per property on requests handled, response times, events run and resident or tenant feedback, plus a single point of contact for the principals."),
    ("How is concierge priced for a portfolio?",
     "Each property is scoped on size, hours and staffing model (staffed, virtual or hybrid), and portfolio rollouts are priced together. Request a proposal for one property to start."),
]


def build_home(offices):
    url = BASE + "/"
    seg_cards = "".join(
        '<a class="card link" href="solutions/%s/"><h3>%s</h3><p>%s</p></a>' % (
            k.replace("_", "-"), esc(SEGMENTS[k]["name"]), esc(SEGMENTS[k]["answer"].split(". ")[0].rstrip(".") + "."))
        for k in SERVED)
    body = f"""
<section class="hero">
<p class="eyebrow">Property concierge for family-office real estate</p>
<h1>Hospitality-grade concierge for the buildings families hold for generations</h1>
<p class="lede">{esc(BRAND)} runs resident, tenant and guest concierge for apartment towers, office lobbies, mixed-use districts, hotels and branded residences, working alongside your property manager.</p>
<p><a class="btn" href="{esc(cta_href())}">Request a proposal for a property</a> <a class="btn ghost" href="family-offices/">How we work with family offices</a></p>
</section>
{answer_box(BRAND + " is a property concierge company. We put trained hospitality staff, on site or virtual, into residential, office, mixed-use and hospitality properties to run the resident, tenant and guest experience: front-desk welcome, packages and errands, reservations, events and VIP service. We report monthly to the owner.")}
<h2>Property types we serve</h2>
<div class="grid">{seg_cards}</div>
<h2>How it works</h2>
<ol class="steps">
<li><strong>Pick one property.</strong> We visit, then scope hours, staffing model and programs.</li>
<li><strong>Run a 90-day pilot.</strong> We agree up front on measures: requests handled, response time, event attendance and satisfaction.</li>
<li><strong>Roll out the standard.</strong> One standard of service across the portfolio, with one report.</li>
</ol>
{faq_html(FO_FAQ[:4])}
"""
    schema = [{"@type": "WebSite", "@id": url + "#site", "url": url, "name": BRAND, "publisher": {"@id": BASE + "/#org"}},
              service_schema(BRAND + " property concierge", CFG["tagline"], url, "Real estate owners and family offices"),
              faq_schema(FO_FAQ[:4], url)]
    write("index.html", page("", 0, f"{BRAND} | Property Concierge for Family Office Real Estate",
                             "Resident, tenant and guest concierge for multifamily, office, mixed-use and hospitality properties owned by family offices. Request a proposal for a property.",
                             body, schema))


def build_pillar(offices):
    path = "family-offices/"
    url = BASE + "/" + path
    mix = Counter(s for o in offices for s in o["served"])
    total = len(offices)
    mix_lines = "".join("<li><strong>%s</strong>: held by %d%% of them</li>" % (
        esc(SEGMENTS[k]["name"]), round(100 * v / total)) for k, v in mix.most_common() if k in SERVED)
    body = f"""
<h1>Concierge services for family office real estate portfolios</h1>
{answer_box("Family offices use " + BRAND + " to put one hospitality standard across the properties they own: resident concierge in residential, tenant experience in office, guest services in hotels and mixed-use. We work alongside your property managers, start with a 90-day pilot at one property, and report to the family office monthly.")}
<h2>Why family-office owners are different</h2>
<p>Institutional funds usually sell a building within five to seven years. Families often hold for decades, and many hold assets that carry the family name. That changes the maths on service. Concierge is less a line item and more a way to protect the long-term reputation and income of a property.</p>
<ul class="checks">
<li><strong>Long holds:</strong> resident and tenant loyalty compounds over decades.</li>
<li><strong>Reputation:</strong> the experience in the lobby reflects on the family.</li>
<li><strong>Mixed portfolios:</strong> residential, office, retail and hospitality under one owner need one standard.</li>
<li><strong>Lean teams:</strong> a single partner instead of building hospitality skills in-house.</li>
</ul>
<h2>What family offices in commercial real estate hold</h2>
<p>In a sample of {total:,} US family offices that invest in commercial real estate, these are the property types where concierge applies:</p>
<ul>{mix_lines}</ul>
<p>See the program for each: {", ".join('<a href="../solutions/%s/">%s</a>' % (k.replace("_", "-"), esc(SEGMENTS[k]["short"])) for k in SERVED)}.</p>
<h2>How a portfolio rollout works</h2>
<ol class="steps">
<li><strong>Portfolio review:</strong> we sort your properties by where concierge adds the most, which is usually the flagship residential or mixed-use asset.</li>
<li><strong>One-property pilot:</strong> 90 days, with measures agreed up front.</li>
<li><strong>Standardise:</strong> the same service standard, brand and reporting across every property.</li>
<li><strong>Owner reporting:</strong> one monthly report for the principals, by property.</li>
</ol>
<p><a class="btn" href="{esc(cta_href_for("Concierge for our portfolio"))}">Request a portfolio review</a></p>
{faq_html(FO_FAQ)}
"""
    schema = [service_schema("Concierge services for family office real estate", FO_FAQ[0][1], url, "Family offices"),
              faq_schema(FO_FAQ, url)]
    write(path + "index.html", page(path, 1, f"Concierge Services for Family Office Real Estate | {BRAND}",
                                    "How family offices add resident, tenant and guest concierge across their real estate portfolios: a 90-day pilot at one property, then one standard everywhere.",
                                    body, schema, crumbs=[("Home", ""), ("Family offices", path)]))


def build_solutions():
    links = []
    for k in SERVED:
        s = SEGMENTS[k]
        slug = k.replace("_", "-")
        path = f"solutions/{slug}/"
        url = BASE + "/" + path
        others = " · ".join('<a href="../%s/">%s</a>' % (o.replace("_", "-"), esc(SEGMENTS[o]["short"]))
                            for o in SERVED if o != k)
        body = f"""
<h1>{esc(s["h1"])}</h1>
{answer_box(s["answer"])}
<h2>What {esc(BRAND)} runs at {esc(s["short"])} properties</h2>
{program_grid(s["programs"])}
<h2>What the owner gets</h2>
<ul class="checks">{"".join("<li>%s</li>" % esc(x) for x in s["outcomes"])}</ul>
<h2>Built for family-office owners</h2>
<p>Family offices usually hold their {esc(s["short"])} buildings for the long term, so service quality compounds. We start with a 90-day pilot at one property, agree on the measures up front, and report monthly to the principals and the property manager. <a href="../../family-offices/">How we work with family offices</a>.</p>
<p><a class="btn" href="{esc(cta_href_for("Concierge proposal: " + s["short"] + " property"))}">Request a proposal for a {esc(s["short"])} property</a></p>
{faq_html(s["faq"])}
<p class="related">Other property types: {others}</p>
"""
        schema = [service_schema(s["title"], s["answer"], url, "Owners of " + s["short"] + " real estate"),
                  faq_schema(s["faq"], url)]
        write(path + "index.html", page(path, 2, f'{s["title"]} | {BRAND}', s["answer"][:155].rsplit(" ", 1)[0] + "…",
                                        body, schema, crumbs=[("Home", ""), ("Property types", "solutions/"), (s["name"], path)]))
        links.append((s["name"], path, s["answer"]))
    body = "<h1>Concierge programs by property type</h1>" + answer_box(
        BRAND + " scopes concierge differently for each property type. Choose yours to see what we run, what the owner gets and common questions.") + \
        '<div class="grid">' + "".join('<a class="card link" href="../%s"><h3>%s</h3><p>%s</p></a>' % (p, esc(n), esc(a.split(". ")[0].rstrip(".") + "."))
                                       for n, p, a in links) + "</div>"
    write("solutions/index.html", page("solutions/", 1, f"Concierge Services by Property Type | {BRAND}",
                                       "Resident, tenant and guest concierge programs for multifamily, office, mixed-use, hotels, senior living, student housing, medical office and retail.",
                                       body, crumbs=[("Home", ""), ("Property types", "solutions/")]))
    return links


def build_markets(offices):
    by_metro = defaultdict(list)
    for o in offices:
        for m in o["metros"]:
            by_metro[m].append(o)
    built = []
    for key, (name, st, _, subs) in METROS.items():
        os_ = by_metro.get(key, [])
        if len(os_) < MIN_OFFICES_FOR_MARKET_PAGE:
            continue
        mix = Counter(s for o in os_ for s in o["served"])
        top = [k for k, _ in mix.most_common() if k in SERVED][:4] or ["multifamily", "office", "mixed_use"]
        path = f"markets/{key}/"
        url = BASE + "/" + path
        sub_txt = ", ".join(subs[:-1]) + " and " + subs[-1] if len(subs) > 1 else subs[0]
        top_names = [SEGMENTS[k]["short"] for k in top]
        top_txt = ", ".join(top_names[:-1]) + " and " + top_names[-1] if len(top_names) > 1 else top_names[0]
        ans = (f"{BRAND} provides resident, tenant and guest concierge for {top_txt} properties in {name}, "
               f"including {sub_txt}. We staff on-site or virtual concierge, run events and amenities, "
               f"and report monthly to the owner, working alongside your property manager.")
        faqs = [
            (f"Who provides concierge services for apartment buildings in {name}?",
             f"{BRAND} provides resident concierge for multifamily and luxury residential buildings across {name}, including {sub_txt}, with staffed, virtual or hybrid coverage scoped per building."),
            (f"Is there a tenant experience provider for office buildings in {name}?",
             f"Yes. {BRAND} runs lobby hospitality, amenity hosting and tenant events for office owners in {name}."),
            (f"Do family offices in {name} use concierge for their properties?",
             f"Family offices that own real estate in {name} hold most of it for the long term, which makes resident and tenant experience a durable lever. {BRAND} starts with a 90-day pilot at one property."),
            (f"How much does property concierge cost in {name}?",
             f"It depends on building size, hours and staffing model. {BRAND} scopes each property individually. Request a proposal with the address to get a number."),
        ]
        cards = program_grid([(SEGMENTS[k]["name"], SEGMENTS[k]["answer"].split(". ")[0].rstrip(".") + ".") for k in top])
        body = f"""
<h1>Property concierge in {esc(name)}</h1>
{answer_box(ans)}
<h2>Where we work in {esc(name)}</h2>
<p>{esc(sub_txt)}, and anywhere else in the metro an owner has a building that deserves a host.</p>
<h2>What owners here ask us for most</h2>
<p>Real estate family offices active in {esc(name)} lean toward {esc(top_txt)}. These are the programs we run for them:</p>
{cards}
<p>See the full programs: {" · ".join('<a href="../../solutions/%s/">%s</a>' % (k.replace("_", "-"), esc(SEGMENTS[k]["short"])) for k in top)}</p>
<p><a class="btn" href="{esc(cta_href_for("Concierge proposal: " + name + " property"))}">Request a proposal for a {esc(name)} property</a></p>
{faq_html(faqs)}
"""
        schema = [service_schema(f"Property concierge services in {name}", ans, url, "Real estate owners",
                                 {"@type": "City", "name": name}),
                  faq_schema(faqs, url)]
        write(path + "index.html", page(path, 2, f"Property Concierge Services in {name} | {BRAND}",
                                        f"Resident, tenant and guest concierge for {top_txt} properties in {name}: {sub_txt}. Request a proposal.",
                                        body, schema, crumbs=[("Home", ""), ("Markets", "markets/"), (name, path)]))
        built.append((key, name, path, len(os_)))
    body = "<h1>Markets we serve</h1>" + answer_box(
        BRAND + " serves owners across the United States. These are the metros where real estate family offices own and invest the most.") + \
        '<div class="grid">' + "".join('<a class="card link" href="../%s"><h3>%s</h3></a>' % (p, esc(n)) for _, n, p, _ in built) + "</div>"
    write("markets/index.html", page("markets/", 1, f"Property Concierge Markets | {BRAND}",
                                     "Metros where " + BRAND + " provides resident, tenant and guest concierge for family-office-owned real estate.",
                                     body, crumbs=[("Home", ""), ("Markets", "markets/")]))
    return built


def build_proposals(offices, market_paths, properties):
    for o in offices:
        d = o["row"]
        path = f"for/{o['slug']}/"
        served = o["served"]
        props = properties.get(o["slug"], [])
        if served:
            cards = []
            for k in served:
                s = SEGMENTS[k]
                cards.append('<div class="card"><h3>At your %s properties</h3><ul>%s</ul><p><a href="../../solutions/%s/">The full %s program</a></p></div>' % (
                    esc(s["short"]), "".join("<li><strong>%s</strong>: %s</li>" % (esc(t), esc(x)) for t, x in s["programs"][:3]),
                    k.replace("_", "-"), esc(s["short"])))
            seg_html = '<div class="grid">' + "".join(cards) + "</div>"
        else:
            seg_html = "<p>Your portfolio leans toward asset classes where concierge plays a smaller role. If you hold any residential, office, mixed-use or hospitality property, that is where we would start.</p>"
        if o["guessed"]:
            seg_html = "<p>Public sources describe your real estate only broadly, so here are the two programs owners most often start with. Tell us which properties you hold and we will tailor this page to them.</p>" + seg_html
        skipped = [SEGMENTS[s]["short"] for s in o["segs"] if s not in SERVED]
        skip_note = ("<p class=\"fine\">We have left out your %s holdings, where concierge is not usually the right fit.</p>" % esc(", ".join(skipped))) if skipped else ""
        mk = [(METROS[m][0], market_paths[m]) for m in o["metros"] if m in market_paths]
        mk_html = ("<p>More on how we work in " + ", ".join('<a href="../../%s">%s</a>' % (p, esc(n)) for n, p in mk) + ".</p>") if mk else ""
        prop_html = ""
        if props:
            prop_html = "<h2>Properties we have looked at</h2><div class=\"grid\">" + "".join(
                '<a class="card link" href="%s/"><h3>%s</h3><p>%s</p></a>' % (p["slug"], esc(p["name"]), esc(", ".join(x for x in [p["type_name"], p["city"]] if x)))
                for p in props) + "</div>"
        lead = served[0] if served else None
        pilot = ("your flagship %s property" % SEGMENTS[lead]["short"]) if lead else "one property"
        port = d["RE Asset Classes"] or "commercial real estate"
        geo = d["Geographic Focus"] or "your markets"
        body = f"""
<p class="eyebrow">Prepared for {esc(o["name"])} · not a public page</p>
<h1>A concierge program for {esc(possessive(o["name"]))} properties</h1>
<p class="lede">You hold {esc(port.lower())} across {esc(geo)}. Here is how {esc(BRAND)} would bring one hospitality standard to those buildings, alongside your property managers.</p>
{seg_html}
{skip_note}
{prop_html}
<h2>A proposed first step</h2>
<ol class="steps">
<li><strong>Choose {esc(pilot)}.</strong> We walk it and scope hours, staffing and programs.</li>
<li><strong>90-day pilot.</strong> Measures agreed up front, reported monthly to you and the property manager.</li>
<li><strong>Portfolio standard.</strong> If it works, the same standard rolls out to the rest of the portfolio, with one report.</li>
</ol>
{mk_html}
<p><a class="btn" href="{esc(cta_href_for("Concierge pilot for " + o["name"]))}">Book a 20-minute portfolio call</a></p>
<p><a href="../../family-offices/">How we work with family offices</a></p>
"""
        write(path + "index.html", page(path, 2, f"{BRAND} for {o['name']}", f"A concierge program proposal prepared for {o['name']}.",
                                        body, index=False))
        for p in props:
            s = SEGMENTS.get(p["seg"]) if p["seg"] in SERVED else None
            ppath = f"{path}{p['slug']}/"
            facts = ", ".join(x for x in [p["type_name"], p["size"], p["city"]] if x)
            if s:
                inner = f"""{program_grid(s["programs"])}
<h2>What {esc(o["name"])} gets as the owner</h2><ul class="checks">{"".join("<li>%s</li>" % esc(x) for x in s["outcomes"])}</ul>"""
            else:
                inner = "<p>We would scope a program for this property on a site visit.</p>"
            pbody = f"""
<p class="eyebrow">Prepared for {esc(o["name"])} · not a public page</p>
<h1>Concierge at {esc(p["name"])}</h1>
<p class="lede">{esc(facts)}. {esc(p["notes"])}</p>
{inner}
<h2>Pilot at {esc(p["name"])}</h2>
<p>A 90-day pilot with measures agreed up front: requests handled, response time, event attendance and {esc(s["people"] if s else "occupant")} satisfaction. Reported monthly to {esc(o["name"])} and the property manager.</p>
<p><a class="btn" href="{esc(cta_href_for("Concierge pilot at " + p["name"]))}">Book a walk-through of {esc(p["name"])}</a></p>
<p><a href="../">Back to the {esc(o["name"])} portfolio proposal</a></p>
"""
            write(ppath + "index.html", page(ppath, 3, f"Concierge at {p['name']} | {BRAND}",
                                             f"A concierge pilot proposal for {p['name']}, prepared for {o['name']}.", pbody, index=False))


def load_properties(path, offices):
    if not path or not os.path.exists(path):
        return {}
    by_name = {o["name"].lower(): o["slug"] for o in offices}
    slugs = {o["slug"] for o in offices}
    out = defaultdict(list)
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        r = {k: (v or "").strip() for k, v in r.items()}
        key = r.get("family_office", "")
        slug = by_name.get(key.lower()) or (slugify(key) if slugify(key) in slugs else None)
        if not slug or not r.get("property_name"):
            print("  ! properties: no family office matches %r, skipped" % key, file=sys.stderr)
            continue
        segs, _ = segments_for(r.get("property_type", ""))
        seg = next((s for s in segs if s in SERVED), segs[0] if segs else "")
        out[slug].append(dict(name=r["property_name"], slug=slugify(r["property_name"]), city=r.get("city", ""),
                              type_name=r.get("property_type", ""), size=r.get("size", ""),
                              notes=r.get("notes", ""), seg=seg))
    return out


# --------------------------------------------------------------------------------------
# Outreach sheet
# --------------------------------------------------------------------------------------
def first_sentence(t, n=220):
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:n].rsplit(" ", 1)[0] + "…") if len(t) > n else t


def write_outreach(offices, market_paths, out_path):
    cols = ["fit_score", "priority", "tier", "family_office", "hq", "primary_property_type", "property_types_served",
            "markets", "decision_makers", "company_email", "company_phone", "linkedin", "website",
            "proposal_url", "best_public_page", "market_page", "subject_line", "opening_line", "talking_point_recent_activity"]
    rows = []
    for o in sorted(offices, key=lambda x: -x["fit"]):
        d = o["row"]
        lead = None if o["guessed"] else (o["served"][0] if o["served"] else None)
        pri = "A" if o["fit"] >= 80 else "B" if o["fit"] >= 65 else "C" if o["fit"] >= 45 else "D - skip"
        mk = next((m for m in o["metros"] if m in market_paths), None)
        if lead:
            subj = f"A hospitality standard for {possessive(o['name'])} {SEGMENTS[lead]['short']} properties"
            opener = (f"When a family holds {SEGMENTS[lead]['short']} property for the long term, the experience in the lobby ends up carrying the family name. "
                      f"We run resident and tenant concierge for owners like that, and I put together a one-page idea for a 90-day pilot at one of your buildings: "
                      f"{BASE}/for/{o['slug']}/")
        else:
            subj = f"Concierge for {possessive(o['name'])} properties"
            opener = f"I put together a short note on where concierge could fit in {o['name']}'s portfolio: {BASE}/for/{o['slug']}/"
        rows.append({
            "fit_score": o["fit"], "priority": pri, "tier": d.get("Tier", ""), "family_office": o["name"],
            "hq": ", ".join(x for x in [d["HQ City"], d["HQ State"]] if x),
            "primary_property_type": SEGMENTS[lead]["name"] if lead else "",
            "property_types_served": "; ".join(SEGMENTS[s]["short"] for s in o["served"]),
            "markets": "; ".join(METROS[m][0] for m in o["metros"]),
            "decision_makers": d.get("Key Decision Maker(s)", ""), "company_email": d.get("Company Email", ""),
            "company_phone": d.get("Company Phone", ""), "linkedin": d.get("LinkedIn", ""),
            "website": d.get("Website / Source", ""),
            "proposal_url": f"{BASE}/for/{o['slug']}/",
            "best_public_page": f"{BASE}/solutions/{lead.replace('_', '-')}/" if lead else f"{BASE}/family-offices/",
            "market_page": f"{BASE}/{market_paths[mk]}" if mk else "",
            "subject_line": subj, "opening_line": opener,
            "talking_point_recent_activity": first_sentence(d.get("Recent Activity (2023-2025)", "")),
        })
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return rows


# --------------------------------------------------------------------------------------
def build_meta(solution_links, markets):
    idx = ["", "family-offices/", "solutions/", "markets/"] + [p for _, p, _ in solution_links] + [p for _, _, p, _ in markets]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in idx:
        sm.append(f"<url><loc>{BASE}/{p}</loc><lastmod>{TODAY}</lastmod></url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"""# {BRAND}
# Answer engines are welcome: these pages are written to be quoted.
User-agent: *
Allow: /
Disallow: /for/

User-agent: GPTBot
Allow: /
Disallow: /for/

User-agent: OAI-SearchBot
Allow: /
Disallow: /for/

User-agent: ChatGPT-User
Allow: /
Disallow: /for/

User-agent: ClaudeBot
Allow: /
Disallow: /for/

User-agent: Claude-SearchBot
Allow: /
Disallow: /for/

User-agent: PerplexityBot
Allow: /
Disallow: /for/

User-agent: Google-Extended
Allow: /
Disallow: /for/

Sitemap: {BASE}/sitemap.xml
""")
    lines = [f"# {BRAND}", "", f"> {BRAND} ({CFG['legal_name']}) is a property concierge company. It provides resident, tenant and guest "
             "concierge, on site or virtual, for multifamily, office, mixed-use, hotel, senior living, student housing, medical office "
             "and retail properties, with a focus on real estate owned by family offices. It works alongside the owner's property "
             "manager, starts with a 90-day pilot at one property, and reports monthly to the owner.", "",
             f"Contact: {CFG['contact_email']}", "", "## Key pages", "",
             f"- [Concierge for family office real estate]({BASE}/family-offices/): why long-hold owners use concierge and how a portfolio rollout works", ]
    for n, p, a in solution_links:
        lines.append(f"- [{n}]({BASE}/{p}): {a.split('. ')[0].rstrip('.')}.")
    lines += ["", "## Markets", ""]
    for _, n, p, _ in markets:
        lines.append(f"- [Property concierge in {n}]({BASE}/{p})")
    write("llms.txt", "\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Homebase family offices CSV")
    ap.add_argument("--properties", default=os.path.join(HERE, "properties.csv"),
                    help="optional per-property CSV (family_office,property_name,property_type,city,size,notes)")
    ap.add_argument("--outreach", default=None, help="where to write the outreach CSV (keep it out of the public site)")
    a = ap.parse_args()

    for d in ("for", "solutions", "markets", "family-offices"):
        shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)

    offices = load_offices(a.csv)
    props = load_properties(a.properties, offices)
    build_home(offices)
    build_pillar(offices)
    sol = build_solutions()
    mk = build_markets(offices)
    market_paths = {k: p for k, _, p, _ in mk}
    build_proposals(offices, market_paths, props)
    build_meta(sol, mk)
    if a.outreach:
        rows = write_outreach(offices, market_paths, a.outreach)
        pri = Counter(r["priority"] for r in rows)
        print("outreach: %s  %s" % (a.outreach, dict(sorted(pri.items()))))
    print("offices: %d  solution pages: %d  market pages: %d  proposal pages: %d  property pages: %d" % (
        len(offices), len(sol), len(mk), len(offices), sum(len(v) for v in props.values())))
    if "convivialconcierge.com" in BASE or "convivialconcierge.com" in CFG["contact_email"]:
        print("WARNING: base_url / contact_email are still the placeholders in _build/config.json", file=sys.stderr)


if __name__ == "__main__":
    main()
