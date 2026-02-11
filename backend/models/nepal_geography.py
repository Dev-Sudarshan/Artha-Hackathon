"""Nepal geography data — 77 districts with municipalities.

Used by the semantic extractor for validation and fuzzy correction
of district / municipality names extracted from citizenship cards.
"""

from typing import Dict, List, Optional

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None


# ---------------------------------------------------------------- data ---

# District → list of municipalities/metro/sub-metro
NEPAL_GEOGRAPHY: Dict[str, List[str]] = {
    # Province 1 (Koshi)
    "Taplejung": ["Phungling", "Aathrai Triveni", "Sidingba", "Phaktanglung",
                  "Mikwakhola", "Meringden", "Maiwakhola", "Sirijangha",
                  "Pathribhara Yangwarak"],
    "Panchthar": ["Phidim", "Hilihang", "Kummayak", "Miklajung",
                  "Falgunanda", "Tumbewa", "Yangwarak"],
    "Ilam": ["Ilam", "Deumai", "Mai", "Suryodaya", "Fakphokthum",
             "Mangsebung", "Chulachuli", "Rong", "Sandakpur",
             "Maijogmai"],
    "Jhapa": ["Mechinagar", "Bhadrapur", "Birtamod", "Damak",
              "Kankai", "Arjundhara", "Shivasatakshi", "Gauradaha",
              "Buddhashanti", "Haldibari", "Jhapa", "Barhadashi",
              "Kachankawal", "Gaurigunj", "Kamal"],
    "Morang": ["Biratnagar", "Sunbarshi", "Belbari", "Urlabari",
               "Pathari Shanischare", "Rangeli", "Letang",
               "Ratuwamai", "Sunawarshi", "Gramthan", "Jahada",
               "Dhanpalthan", "Kerabari", "Budhiganga", "Kanepokhari",
               "Miklajung", "Katahari"],
    "Sunsari": ["Inaruwa", "Itahari", "Dharan", "Duhabi",
                "Barahachhetra", "Koshi", "Gadhi", "Barju",
                "Bhokraha Narsingh", "Harinagar", "Dewanganj",
                "Ramdhuni"],
    "Dhankuta": ["Dhankuta", "Pakhribas", "Mahalaxmi", "Sahidbhumi",
                 "Chaubise", "Sangurigadhi", "Khalsa Chhintang Sahidbhumi"],
    "Terhathum": ["Myanglung", "Laligurans", "Aathrai", "Chhathar",
                  "Menchayam", "Phedap"],
    "Sankhuwasabha": ["Khandbari", "Chainpur", "Dharmadevi",
                      "Madi", "Panchakhapan", "Makalu",
                      "Chichila", "Bhotkhola", "Sabhapokhari",
                      "Silichong"],
    "Bhojpur": ["Bhojpur", "Shadanand", "Tyamke Maiyunm",
                "Arun", "Hatuwagadhi", "Ramprasad Rai",
                "Aamchowk", "Pauwadungma", "Salpasilichho"],
    "Solukhumbu": ["Solududhkunda", "Necha Salyan", "Dudhakaushika",
                   "Mahakulung", "Sotang", "Thulung Dudhkoshi",
                   "Mapya Dudhkoshi", "Likhu Pike", "Khumbu Pasang Lhamu"],
    "Okhaldhunga": ["Siddhicharan", "Khiji Demba", "Manebhanjyang",
                    "Champadevi", "Sunkoshi", "Likhu", "Molung",
                    "Chisankhugadhi"],
    "Khotang": ["Diktel Rupakot Majhuwagadhi", "Halesi Tuwachung",
                "Khotehang", "Diprung Chuichumma", "Aiselukharka",
                "Jantedhunga", "Kepilasgadhi", "Rawabesi",
                "Sakela", "Barahapokhari", "Lamidanda"],
    "Udayapur": ["Triyuga", "Katari", "Chaudandigadhi",
                 "Belaka", "Udayapurgadhi", "Rautamai",
                 "Tapli", "Limchungbung"],

    # Province 2 (Madhesh)
    "Saptari": ["Rajbiraj", "Kanchanrup", "Dakneshwori",
                "Bodebarsain", "Shambhunath", "Surunga",
                "Hanumannagar Kankalini", "Bishnupur",
                "Khadak", "Agnisair Krishna Savaran",
                "Balan Bihul", "Chhinnamasta",
                "Mahadeva", "Rupani", "Tilathi Koiladi",
                "Saptakoshi", "Rajgadh", "Tirhut"],
    "Siraha": ["Siraha", "Lahan", "Golbazar", "Mirchaiya",
               "Dhangadhimai", "Kalyanpur", "Karjanha",
               "Sukhipur", "Bhagwanpur", "Aurahi",
               "Bariyarpatti", "Lakshmipur Patari",
               "Naraha", "Bishnupur", "Arnama",
               "Sakhuwa Prasauni", "Navrajpur"],
    "Dhanusha": ["Janakpurdham", "Chhireshwornath",
                 "Ganeshman Charnath", "Dhanushadham",
                 "Mithila", "Sabaila", "Kamala",
                 "Nagarain", "Bateshwar", "Janaknandini",
                 "Lakshminiya", "Mithila Bihari", "Hansapur",
                 "Aurahi", "Dhanauji",
                 "Mukhiyapatti Musaharniya"],
    "Mahottari": ["Jaleshwar", "Bardibas", "Gaushala",
                  "Loharpatti", "Balwa", "Manara Siswa",
                  "Aurahi", "Bhangaha", "Matihani",
                  "Ramgopalpur", "Mahottari", "Pipra",
                  "Samsi", "Ekdara", "Sonama"],
    "Sarlahi": ["Malangwa", "Hariwan", "Ishworpur",
                "Lalbandi", "Barahathwa", "Godaita",
                "Balara", "Bagmati", "Kabilasi",
                "Chandranagar", "Dhankaul", "Parsa",
                "Bishnu", "Bramhapuri", "Ramnagar",
                "Chakraghatta", "Basbariya", "Kaudena"],
    "Rautahat": ["Gaur", "Chandrapur", "Garuda",
                 "Brindaban", "Gujara", "Dewahi Gonahi",
                 "Ishanath", "Katahariya", "Madhav Narayan",
                 "Maulapur", "Paroha", "Phatuwa Bijayapur",
                 "Rajdevi", "Rajpur", "Yamunamai",
                 "Durga Bhagwati", "Baudhimai"],
    "Bara": ["Kalaiya", "Jeetpur Simara", "Kolhabi",
             "Nijgadh", "Mahagadhimai", "Simraungadh",
             "Pachrauta", "Pheta", "Prasauni",
             "Adarshakotwal", "Karaiyamai", "Devtal",
             "Parwanipur", "Suwarna", "Baragadhi",
             "Bishrampur"],
    "Parsa": ["Birgunj", "Pokhariya", "Bahudarmai",
              "Parsagadhi", "Paterwasugauli", "Sakhuwa Prasauni",
              "Jagarnathpur", "Kalikamai", "Bindabasini",
              "Pakaha Mainpur", "Thori", "Dhobini",
              "Chhipaharmai", "Bindabasini"],

    # Bagmati Province
    "Dolakha": ["Bhimeshwar", "Jiri", "Kalinchok",
                "Melung", "Bigu", "Gaurishankar",
                "Tamakoshi", "Baiteshwar", "Sailung"],
    "Sindhupalchok": ["Chautara Sangachokgadhi", "Melamchi",
                      "Barhabise", "Bahrabise", "Panchpokhari Thangpal",
                      "Helambu", "Balefi", "Sunkoshi",
                      "Indrawati", "Jugal", "Lisankhu Pakhar",
                      "Tripurasundari"],
    "Rasuwa": ["Naukunda", "Kalika", "Uttargaya",
               "Gosaikunda", "Aamachhodingmo"],
    "Nuwakot": ["Bidur", "Belkotgadhi", "Kakani",
                "Dupcheshwar", "Shivapuri", "Tadi",
                "Kispang", "Suryagadhi", "Likhu",
                "Panchakanya", "Tarkeshwar", "Myagang"],
    "Dhading": ["Dhunibesi", "Nilkantha", "Gajuri",
                "Galchi", "Benighat Rorang", "Jwalamukhi",
                "Gangajamuna", "Khaniyabas", "Netrawati Dabjong",
                "Rubi Valley", "Siddhalek", "Thakre",
                "Tripurasundari"],
    "Kathmandu": ["Kathmandu Metropolitan", "Kirtipur",
                  "Chandragiri", "Tokha", "Tarakeshwar",
                  "Nagarjun", "Kageshwari Manohara",
                  "Gokarneshwar", "Budhanilkantha",
                  "Dakshinkali", "Shankharapur"],
    "Bhaktapur": ["Bhaktapur", "Madhyapur Thimi",
                  "Suryabinayak", "Changunarayan"],
    "Lalitpur": ["Lalitpur Metropolitan", "Godawari",
                 "Mahalaxmi", "Konjyosom", "Bagmati",
                 "Khokana"],
    "Kavrepalanchok": ["Dhulikhel", "Banepa", "Panauti",
                       "Namobuddha", "Panchkhal",
                       "Mandandeupur", "Khanikhola",
                       "Chaunri Deurali", "Temal",
                       "Bhumlu", "Mahabharat", "Bethanchok",
                       "Roshi"],
    "Ramechhap": ["Manthali", "Ramechhap", "Umakunda",
                  "Khandadevi", "Doramba", "Gokulganga",
                  "Likhu Tamakoshi", "Sunapati"],
    "Sindhuli": ["Sindhulimadhi", "Kamalamai", "Dudhauli",
                 "Sunkoshi", "Hariharpurgadhi", "Tinpatan",
                 "Marin", "Phikkal", "Golanjor"],
    "Makwanpur": ["Hetauda", "Thaha", "Makwanpurgadhi",
                  "Manahari", "Bakaiya", "Bagmati",
                  "Bhimphedi", "Indrasarowar", "Kailash",
                  "Raksirang"],
    "Chitwan": ["Bharatpur", "Ratnanagar", "Rapti",
                "Khairhani", "Madi", "Kalika",
                "Ichchhakamana"],

    # Gandaki Province
    "Gorkha": ["Gorkha", "Palungtar", "Sulikot",
               "Siranchok", "Ajirkot", "Aarughat",
               "Shahid Lakhan", "Barpak Sulikot",
               "Bhimsen Thapa", "Dharche", "Gandaki"],
    "Manang": ["Chame", "Nason", "Narpabhumi",
               "Manang Ngisyang"],
    "Mustang": ["Jomsom", "Gharapjhong", "Thasang",
                "Baragung Muktichhetra", "Lo Ghekar Damodarkunda"],
    "Myagdi": ["Beni", "Annapurna", "Dhaulagiri",
               "Mangala", "Malika", "Raghuganga"],
    "Kaski": ["Pokhara", "Machhapuchchhre",
              "Madi", "Rupa", "Annapurna"],
    "Lamjung": ["Besisahar", "Sundarbazar", "Rainas",
                "Dordi", "Dudhpokhari", "Kwholasothar",
                "Marsyangdi", "Madhya Nepal"],
    "Tanahu": ["Damauli", "Bhanu", "Shuklagandaki",
               "Byas", "Bandipur", "Rishing",
               "Ghiring", "Devghat", "Myagde",
               "Aanbukhaireni"],
    "Nawalparasi East": ["Kawasoti", "Devchuli", "Gaidakot",
                         "Madhyabindu", "Binayi Tribeni",
                         "Bulingtar", "Hupsekot", "Baudikatham"],
    "Syangja": ["Putalibazar", "Waling", "Galyang",
                "Chapakot", "Bhirkot", "Arjun Chaupari",
                "Biruwa", "Kaligandaki", "Harinas",
                "Phedikhola", "Aandhikhola"],
    "Parbat": ["Kushma", "Phalebas", "Jaljala",
               "Modi", "Mahashila", "Bihadi", "Paiyun"],
    "Baglung": ["Baglung", "Galkot", "Jaimini",
                "Dhorpatan", "Bareng", "Kanthekhola",
                "Taman Khola", "Tara Khola", "Nisikhola",
                "Badigad"],

    # Lumbini Province
    "Gulmi": ["Tamghas", "Musikot", "Resunga",
              "Isma", "Kaligandaki", "Satyawati",
              "Chandrakot", "Ruru", "Malika",
              "Chatrakot", "Dhurkot", "Madane"],
    "Palpa": ["Tansen", "Rampur", "Rainadevi Chhahara",
              "Ripdhi", "Bagnaskali", "Rambha",
              "Nisdi", "Mathagadhi", "Purbakhola",
              "Tinau"],
    "Nawalparasi West": ["Ramgram", "Sunwal", "Bardaghat",
                         "Pratappur", "Susta", "Palhinandan",
                         "Sarawal"],
    "Rupandehi": ["Butwal", "Siddharthanagar", "Devdaha",
                  "Lumbini Sanskritik", "Sainamaina",
                  "Rohini", "Tillotama", "Sammarimai",
                  "Marchawari", "Gaidahawa", "Omsatiya",
                  "Kanchan", "Siyari", "Sudhdhodhan",
                  "Kotahimai", "Mayadevi"],
    "Kapilvastu": ["Kapilvastu", "Banganga", "Buddhabhumi",
                   "Shivaraj", "Krishnanagar", "Maharajgunj",
                   "Mayadevi", "Yashodhaara", "Bijayanagar",
                   "Suddhodhan"],
    "Arghakhanchi": ["Sandhikharka", "Sitganga", "Bhumikasthan",
                     "Chhatradev", "Panini", "Malarani"],
    "Pyuthan": ["Pyuthan", "Swargadwari", "Gaumukhi",
                "Mandavi", "Sarumarani", "Mallarani",
                "Jhimruk", "Naubahini", "Airawati"],
    "Rolpa": ["Liwang", "Rolpa", "Triveni",
              "Runtigadhi", "Lungri", "Sunchhahari",
              "Sukidaha", "Thabang", "Madi",
              "Gangadev"],
    "Dang": ["Ghorahi", "Tulsipur", "Lamahi",
             "Gadhawa", "Rajpur", "Shantinagar",
             "Bangalachuli", "Dangisharan", "Rapti",
             "Babai"],
    "Banke": ["Nepalgunj", "Kohalpur", "Narainapur",
              "Raptisonari", "Baijanath", "Khajura",
              "Duduwa", "Janaki"],
    "Bardiya": ["Gulariya", "Rajapur", "Madhuwan",
                "Thakurbaba", "Bansgadhi", "Barbardiya",
                "Badhaiyatal", "Geruwa"],

    # Karnali Province
    "Dolpa": ["Dunai", "Thulibheri", "Dolpo Buddha",
              "Shey Phoksundo", "Jagadulla", "Mudkechula",
              "Kaike", "Chharka Tangsong", "Tribeni"],
    "Mugu": ["Gamgadhi", "Chhayanath Rara", "Mugum Karmarong",
             "Soru", "Khamale"],
    "Humla": ["Simikot", "Namkha", "Chankheli",
              "Adanchuli", "Kharpunath", "Sarkegad",
              "Tanjakot"],
    "Jumla": ["Khalanga", "Chandannath", "Kanaka Sundari",
              "Patarasi", "Tila", "Guthichaur",
              "Tatopani", "Hima"],
    "Kalikot": ["Manma", "Khandachakra", "Raskot",
                "Tilagufa", "Pachal Jharna", "Sanni Triveni",
                "Mahawai", "Naraharinath", "Palata"],
    "Dailekh": ["Narayan", "Dullu", "Chamunda Bindrasaini",
                "Aathabis", "Bhagwatimai", "Gurans",
                "Mahabu", "Naumule", "Bhairabi",
                "Dungeshwar", "Thantikandh"],
    "Jajarkot": ["Khalanga", "Bheri", "Nalgad",
                 "Chhedagad", "Junichande", "Kushe",
                 "Barekot"],
    "Rukum West": ["Musikot", "Chaurjahari", "Sanibheri",
                   "Triveni", "Aathbiskot", "Banfikot"],
    "Salyan": ["Salyan", "Bangad Kupinde", "Sharada",
               "Bagchaur", "Kalimati", "Tribeni",
               "Kumakh", "Chatreshwori", "Kapurkot",
               "Darma", "Siddha Kumakh"],
    "Surkhet": ["Birendranagar", "Bheriganga", "Gurbhakot",
                "Panchapuri", "Lekbeshi", "Chaukune",
                "Barahatal", "Chingad", "Simta"],

    # Sudurpashchim Province
    "Bajura": ["Martadi", "Badimalika", "Triveni",
               "Budhiganga", "Budhinanda", "Gaumul",
               "Jagannath", "Swamikartik Khapar",
               "Himali"],
    "Bajhang": ["Jayaprithvi", "Bungal", "Thalara",
                "Masta", "Durgathali", "Kedarsyu",
                "Khaptad Chhanna", "Talkot", "Bitthadchir",
                "Surma", "Chabispathivera", "Saipal"],
    "Darchula": ["Mahakali", "Shailyashikhar",
                 "Malikarjun", "Marma", "Apihimal",
                 "Duhun", "Naugad", "Byas",
                 "Lekam"],
    "Baitadi": ["Dashrathchand", "Patan", "Melauli",
                "Purchaudi", "Sigas", "Shivanath",
                "Dogadakedar", "Dilasaini",
                "Surnaya", "Pancheshwar"],
    "Dadeldhura": ["Amargadhi", "Parashuram",
                   "Aalitaal", "Bhageshwar",
                   "Navadurga", "Ajaymeru",
                   "Ganyapadhura"],
    "Doti": ["Dipayal Silgadhi", "Shikhar",
             "Purbichauki", "Badikedar", "Jorayal",
             "Sayal", "Aadarsha", "Bogatan Phudsil",
             "K I Singh"],
    "Achham": ["Mangalsen", "Sanfebagar", "Kamalbazar",
               "Panchadewal Binayak", "Chaurpati",
               "Mellekh", "Ramaroshan", "Jayaprithvi",
               "Turmakhad", "Bannigadhi Jayagadh"],
    "Kailali": ["Dhangadhi", "Tikapur", "Ghodaghodi",
                "Lamkichuha", "Bhajani", "Godawari",
                "Gauriganga", "Janaki", "Bardagoriya",
                "Mohanyal", "Kailari", "Joshipur",
                "Chure"],
    "Kanchanpur": ["Bhimdatta", "Mahakali", "Shuklaphanta",
                   "Bedkot", "Belauri", "Punarbas",
                   "Krishnapur", "Laljhadi", "Beldandi"],
}


# ---------------------------------------------------------- lookups ---

# Normalised district names for fast lookup
_DISTRICT_LOWER = {d.lower(): d for d in NEPAL_GEOGRAPHY}

# Normalised municipality → district mapping
_MUNI_LOWER: Dict[str, Dict[str, str]] = {}
for _dist, _munis in NEPAL_GEOGRAPHY.items():
    for _m in _munis:
        _MUNI_LOWER.setdefault(_m.lower(), {})[_dist.lower()] = _dist


# -------------------------------------------------------- public API ---

def validate_district(name: str) -> bool:
    """Return True if *name* exactly matches a known district (case-insensitive)."""
    return name.strip().lower() in _DISTRICT_LOWER


def validate_municipality(name: str, district: str) -> bool:
    """Return True if *name* is a municipality in *district* (case-insensitive)."""
    dist_lower = district.strip().lower()
    if dist_lower not in _DISTRICT_LOWER:
        return False
    canon_dist = _DISTRICT_LOWER[dist_lower]
    munis_lower = [m.lower() for m in NEPAL_GEOGRAPHY[canon_dist]]
    return name.strip().lower() in munis_lower


def fuzzy_match_district(name: str, threshold: float = 70.0) -> Optional[str]:
    """Return the best fuzzy-matching district name, or None."""
    if not name or fuzz is None:
        return None
    name_l = name.strip().lower()
    if name_l in _DISTRICT_LOWER:
        return _DISTRICT_LOWER[name_l]
    best, best_score = None, 0.0
    for d_lower, d_canon in _DISTRICT_LOWER.items():
        score = fuzz.ratio(name_l, d_lower)
        if score > best_score:
            best_score, best = score, d_canon
    return best if best_score >= threshold else None


def fuzzy_match_municipality(name: str, district: str,
                             threshold: float = 65.0) -> Optional[str]:
    """Return the best fuzzy-matching municipality in *district*, or None.

    Uses both full ratio and partial_ratio to handle OCR truncation
    (e.g. "Jana" → "Janakpurdham").
    """
    if not name or fuzz is None:
        return None
    dist_lower = district.strip().lower()
    if dist_lower not in _DISTRICT_LOWER:
        # Try fuzzy district first
        matched_dist = fuzzy_match_district(district)
        if not matched_dist:
            return None
        dist_lower = matched_dist.lower()
    canon_dist = _DISTRICT_LOWER[dist_lower]
    munis = NEPAL_GEOGRAPHY[canon_dist]

    name_l = name.strip().lower()
    best, best_score = None, 0.0
    for m in munis:
        m_l = m.lower()
        # Full match score
        full = fuzz.ratio(name_l, m_l)
        # Partial match score (handles OCR truncation) — require the
        # partial match to cover at least 3 characters to avoid noise.
        partial = fuzz.partial_ratio(name_l, m_l) if len(name_l) >= 3 else 0.0
        # Prefer full match; use partial only if it's very strong (≥85)
        score = max(full, partial * 0.85)
        if score > best_score:
            best_score, best = score, m
    return best if best_score >= threshold else None
