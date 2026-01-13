"""
Geographic Normalization Helpers for Python
Funções para obter países, estados e cidades normalizados

UPDATED 2025-12-23: Now uses normalized lookup functions instead of get_or_create
This prevents duplicates and ensures referential integrity with normalized tables.

UPDATED 2025-12-26: Added intelligent fallbacks for common mismatches
"""

import re
from typing import Optional

# Support both relative and absolute imports
# Try different import methods to work in various contexts
try:
    # Method 1: Relative import (when used as package)
    from .geo_id_helpers import get_city_id, get_country_id, get_state_id
except (ImportError, ValueError):
    try:
        # Method 2: Absolute import from shared package
        from shared.geo_id_helpers import get_city_id, get_country_id, get_state_id
    except ImportError:
        # Method 3: Direct import (when script in same directory)
        from geo_id_helpers import get_city_id, get_country_id, get_state_id


# ============================================================================
# INTELLIGENT FALLBACKS - Maps common mistakes to correct countries
# ============================================================================

CITY_TO_COUNTRY = {
    # Germany
    "berlin": "Germany",
    "munich": "Germany",
    "hamburg": "Germany",
    "cologne": "Germany",
    "frankfurt": "Germany",
    "stuttgart": "Germany",
    "dortmund": "Germany",
    "düsseldorf": "Germany",
    "mannheim": "Germany",
    "nuremberg": "Germany",
    "bremen": "Germany",
    "leipzig": "Germany",
    "dresden": "Germany",
    "hannover": "Germany",
    "duisburg": "Germany",
    "essen": "Germany",
    "köln": "Germany",
    "nürnberg": "Germany",
    "frankfurt am main": "Germany",
    # UK & Ireland
    "dublin": "Ireland",
    "london": "United Kingdom",
    "manchester": "United Kingdom",
    "birmingham": "United Kingdom",
    # France
    "paris": "France",
    "lyon": "France",
    "marseille": "France",
    "toulouse": "France",
    "bordeaux": "France",
    "lille": "France",
    "nantes": "France",
    "nice": "France",
    "strasbourg": "France",
    "grenoble": "France",
    "montpellier": "France",
    # Netherlands
    "amsterdam": "Netherlands",
    "rotterdam": "Netherlands",
    "utrecht": "Netherlands",
    "eindhoven": "Netherlands",
    "groningen": "Netherlands",
    "delft": "Netherlands",
    "arnhem": "Netherlands",
    "maastricht": "Netherlands",
    # Spain
    "barcelona": "Spain",
    "madrid": "Spain",
    "valencia": "Spain",
    "sevilla": "Spain",
    "seville": "Spain",
    "bilbao": "Spain",
    "málaga": "Spain",
    "zaragoza": "Spain",
    # Switzerland
    "zürich": "Switzerland",
    "zurich": "Switzerland",
    "geneva": "Switzerland",
    "basel": "Switzerland",
    "bern": "Switzerland",
    "lausanne": "Switzerland",
    "lucerne": "Switzerland",
    "zug": "Switzerland",
    # Austria
    "vienna": "Austria",
    "wien": "Austria",
    "salzburg": "Austria",
    "graz": "Austria",
    "linz": "Austria",
    # Italy
    "rome": "Italy",
    "milan": "Italy",
    "naples": "Italy",
    "turin": "Italy",
    "florence": "Italy",
    # Poland
    "warsaw": "Poland",
    "kraków": "Poland",
    "krakow": "Poland",
    "gdańsk": "Poland",
    "wrocław": "Poland",
    # India
    "bangalore": "India",
    "bengaluru": "India",
    "mumbai": "India",
    "delhi": "India",
    "pune": "India",
    "hyderabad": "India",
    "chennai": "India",
    "kolkata": "India",
    "noida": "India",
    "gurgaon": "India",
    "ahmedabad": "India",
    "jaipur": "India",
    "kochi": "India",
    "trivandrum": "India",
    "thiruvananthapuram": "India",
    "madurai": "India",
    "coimbatore": "India",
    "navi mumbai": "India",
    # Asia-Pacific
    "singapore": "Singapore",
    "tokyo": "Japan",
    "seoul": "South Korea",
    "beijing": "China",
    "shanghai": "China",
    "hong kong": "Hong Kong",
    "bangkok": "Thailand",
    "ho chi minh": "Vietnam",
    "manila": "Philippines",
    "jakarta": "Indonesia",
    "kuala lumpur": "Malaysia",
    # Australia
    "sydney": "Australia",
    "melbourne": "Australia",
    "brisbane": "Australia",
    "perth": "Australia",
    "adelaide": "Australia",
    "canberra": "Australia",
    "melbourne cbd": "Australia",
    "perth cbd": "Australia",
    "adelaide cbd": "Australia",
    # New Zealand
    "auckland": "New Zealand",
    "wellington": "New Zealand",
    "christchurch": "New Zealand",
    # Brazil
    "são paulo": "Brazil",
    "sao paulo": "Brazil",
    "rio de janeiro": "Brazil",
    "brasilia": "Brazil",
    "brasília": "Brazil",
    "porto alegre": "Brazil",
    "curitiba": "Brazil",
    "recife": "Brazil",
    "fortaleza": "Brazil",
    "belo horizonte": "Brazil",
    "salvador": "Brazil",
    "manaus": "Brazil",
    "campinas": "Brazil",
    "florianópolis": "Brazil",
    "goiânia": "Brazil",
    # Latin America
    "buenos aires": "Argentina",
    "santiago": "Chile",
    "mexico city": "Mexico",
    "bogotá": "Colombia",
    "lima": "Peru",
    "caracas": "Venezuela",
    "montevideo": "Uruguay",
    # Canada
    "toronto": "Canada",
    "vancouver": "Canada",
    "montreal": "Canada",
    "montréal": "Canada",
    "calgary": "Canada",
    "edmonton": "Canada",
    "ottawa": "Canada",
    "halifax": "Canada",
    "winnipeg": "Canada",
    "québec city": "Canada",
    "quebec city": "Canada",
    # United States
    "new york": "United States",
    "los angeles": "United States",
    "san francisco": "United States",
    "chicago": "United States",
    "boston": "United States",
    "seattle": "United States",
    "austin": "United States",
    "atlanta": "United States",
    "denver": "United States",
    "miami": "United States",
    "philadelphia": "United States",
    "phoenix": "United States",
    "dallas": "United States",
    "houston": "United States",
    "san diego": "United States",
    "portland": "United States",
    "las vegas": "United States",
    "detroit": "United States",
    "washington": "United States",
    "minneapolis": "United States",
    "pittsburgh": "United States",
    # City abbreviations
    "nyc": "United States",
    "sf": "United States",
    "la": "United States",
    "sea": "United States",
    "atl": "United States",
    "chi": "United States",
    "phx": "United States",
    "pdx": "United States",
    # South Africa
    "johannesburg": "South Africa",
    "cape town": "South Africa",
    "durban": "South Africa",
    "pretoria": "South Africa",
}

STATE_TO_COUNTRY = {
    # United States
    "california": "United States",
    "texas": "United States",
    "florida": "United States",
    "new york": "United States",
    "washington": "United States",
    "massachusetts": "United States",
    "illinois": "United States",
    "pennsylvania": "United States",
    "ohio": "United States",
    "georgia": "United States",
    "colorado": "United States",
    "oregon": "United States",
    # Brazil
    "minas gerais": "Brazil",
    "rio grande do sul": "Brazil",
    "pernambuco": "Brazil",
    "ceará": "Brazil",
    "ceara": "Brazil",
    "distrito federal": "Brazil",
    "amazonas": "Brazil",
    "santa catarina": "Brazil",
    "paraná": "Brazil",
    "parana": "Brazil",
    "bahia": "Brazil",
    "rio de janeiro": "Brazil",
    "são paulo": "Brazil",
    "sao paulo": "Brazil",
    "goiás": "Brazil",
    # India
    "maharashtra": "India",
    "telangana": "India",
    "tamil nadu": "India",
    "karnataka": "India",
    "kerala": "India",
    "gujarat": "India",
    "uttar pradesh": "India",
    "rajasthan": "India",
    "west bengal": "India",
    "madhya pradesh": "India",
    "haryana": "India",
    "punjab": "India",
    # Canada
    "british columbia": "Canada",
    "ontario": "Canada",
    "quebec": "Canada",
    "québec": "Canada",
    "alberta": "Canada",
    "manitoba": "Canada",
    "saskatchewan": "Canada",
    "nova scotia": "Canada",
    "new brunswick": "Canada",
    "newfoundland": "Canada",
    # Australia
    "new south wales": "Australia",
    "victoria": "Australia",
    "queensland": "Australia",
    "south australia": "Australia",
    "western australia": "Australia",
    "australian capital territory": "Australia",
    "tasmania": "Australia",
    "northern territory": "Australia",
    # Germany
    "baden-württemberg": "Germany",
    "baden-wurttemberg": "Germany",
    "bayern": "Germany",
    "bavaria": "Germany",
    "berlin": "Germany",
    "brandenburg": "Germany",
    "bremen": "Germany",
    "hamburg": "Germany",
    "hessen": "Germany",
    "hesse": "Germany",
    "niedersachsen": "Germany",
    "lower saxony": "Germany",
    "nordrhein-westfalen": "Germany",
    "north rhine-westphalia": "Germany",
    "rheinland-pfalz": "Germany",
    "saarland": "Germany",
    "sachsen": "Germany",
    "saxony": "Germany",
    "schleswig-holstein": "Germany",
    "thüringen": "Germany",
    "thuringia": "Germany",
    # France
    "île-de-france": "France",
    "ile-de-france": "France",
    "provence-alpes-côte d'azur": "France",
    "auvergne-rhône-alpes": "France",
    "nouvelle-aquitaine": "France",
    "occitanie": "France",
    "hauts-de-france": "France",
    "bretagne": "France",
    "brittany": "France",
    "normandie": "France",
    # Italy
    "lombardia": "Italy",
    "lombardy": "Italy",
    "lazio": "Italy",
    "latium": "Italy",
    "toscana": "Italy",
    "tuscany": "Italy",
    "emilia-romagna": "Italy",
    "veneto": "Italy",
    "piemonte": "Italy",
    "piedmont": "Italy",
    "campania": "Italy",
    "sicilia": "Italy",
    "sicily": "Italy",
    # Netherlands
    "noord-holland": "Netherlands",
    "zuid-holland": "Netherlands",
    "noord-brabant": "Netherlands",
    "gelderland": "Netherlands",
    "overijssel": "Netherlands",
    "friesland": "Netherlands",
    "provincie utrecht": "Netherlands",
    # Poland
    "mazowieckie": "Poland",
    "śląskie": "Poland",
    "dolnośląskie": "Poland",
    "małopolskie": "Poland",
    "wielkopolskie": "Poland",
    "pomorskie": "Poland",
    # Mexico
    "nuevo león": "Mexico",
    "nuevo leon": "Mexico",
    "jalisco": "Mexico",
    "estado de méxico": "Mexico",
    "mexico city": "Mexico",
    "ciudad de méxico": "Mexico",
}

COUNTRY_ALIASES = {
    # ========== PORTUGUESE COUNTRY NAMES (ALL ~195 COUNTRIES) ==========
    # Americas
    "estados unidos": "United States",
    "canadá": "Canada",
    "canada": "Canada",
    "méxico": "Mexico",
    "mexico": "Mexico",
    "argentina": "Argentina",
    "chile": "Chile",
    "colômbia": "Colombia",
    "colombia": "Colombia",
    "peru": "Peru",
    "venezuela": "Venezuela",
    "equador": "Ecuador",
    "bolívia": "Bolivia",
    "bolivia": "Bolivia",
    "paraguai": "Paraguay",
    "uruguai": "Uruguay",
    "guiana": "Guyana",
    "suriname": "Suriname",
    "guiana francesa": "French Guiana",
    "costa rica": "Costa Rica",
    "panamá": "Panama",
    "panama": "Panama",
    "guatemala": "Guatemala",
    "belize": "Belize",
    "honduras": "Honduras",
    "el salvador": "El Salvador",
    "nicarágua": "Nicaragua",
    "nicaragua": "Nicaragua",
    "cuba": "Cuba",
    "jamaica": "Jamaica",
    "haiti": "Haiti",
    "república dominicana": "Dominican Republic",
    "republica dominicana": "Dominican Republic",
    "porto rico": "Puerto Rico",
    "bahamas": "Bahamas",
    "barbados": "Barbados",
    "trinidad e tobago": "Trinidad and Tobago",
    "granada": "Grenada",
    "santa lúcia": "Saint Lucia",
    "santa lucia": "Saint Lucia",
    "são vicente e granadinas": "Saint Vincent and the Grenadines",
    "antígua e barbuda": "Antigua and Barbuda",
    "dominica": "Dominica",
    "são cristóvão e nevis": "Saint Kitts and Nevis",
    # Europe
    "alemanha": "Germany",
    "frança": "France",
    "franca": "France",
    "reino unido": "United Kingdom",
    "itália": "Italy",
    "italia": "Italy",
    "espanha": "Spain",
    "portugal": "Portugal",
    "países baixos": "Netherlands",
    "paises baixos": "Netherlands",
    "holanda": "Netherlands",
    "países baixos (holanda)": "Netherlands",
    "bélgica": "Belgium",
    "belgica": "Belgium",
    "suíça": "Switzerland",
    "suica": "Switzerland",
    "áustria": "Austria",
    "austria": "Austria",
    "suécia": "Sweden",
    "suecia": "Sweden",
    "noruega": "Norway",
    "dinamarca": "Denmark",
    "finlândia": "Finland",
    "finlandia": "Finland",
    "islândia": "Iceland",
    "islandia": "Iceland",
    "irlanda": "Ireland",
    "polônia": "Poland",
    "polonia": "Poland",
    "república tcheca": "Czech Republic",
    "republica tcheca": "Czech Republic",
    "tchéquia": "Czechia",
    "tchequia": "Czechia",
    "eslováquia": "Slovakia",
    "eslovaquia": "Slovakia",
    "hungria": "Hungary",
    "romênia": "Romania",
    "romenia": "Romania",
    "bulgária": "Bulgaria",
    "bulgaria": "Bulgaria",
    "grécia": "Greece",
    "grecia": "Greece",
    "croácia": "Croatia",
    "croacia": "Croatia",
    "sérvia": "Serbia",
    "serbia": "Serbia",
    "bósnia e herzegovina": "Bosnia and Herzegovina",
    "bosnia e herzegovina": "Bosnia and Herzegovina",
    "montenegro": "Montenegro",
    "macedônia do norte": "North Macedonia",
    "macedonia do norte": "North Macedonia",
    "albânia": "Albania",
    "albania": "Albania",
    "eslovênia": "Slovenia",
    "eslovenia": "Slovenia",
    "estônia": "Estonia",
    "estonia": "Estonia",
    "letônia": "Latvia",
    "letonia": "Latvia",
    "lituânia": "Lithuania",
    "lituania": "Lithuania",
    "ucrânia": "Ukraine",
    "ucrania": "Ukraine",
    "bielorrússia": "Belarus",
    "bielorrussia": "Belarus",
    "rússia": "Russia",
    "russia": "Russia",
    "moldávia": "Moldova",
    "moldavia": "Moldova",
    "luxemburgo": "Luxembourg",
    "mônaco": "Monaco",
    "monaco": "Monaco",
    "liechtenstein": "Liechtenstein",
    "andorra": "Andorra",
    "san marino": "San Marino",
    "vaticano": "Vatican City",
    "malta": "Malta",
    "chipre": "Cyprus",
    # Africa
    "áfrica do sul": "South Africa",
    "africa do sul": "South Africa",
    "egito": "Egypt",
    "líbia": "Libya",
    "libia": "Libya",
    "tunísia": "Tunisia",
    "tunisia": "Tunisia",
    "argélia": "Algeria",
    "argelia": "Algeria",
    "marrocos": "Morocco",
    "sudão": "Sudan",
    "sudao": "Sudan",
    "sudão do sul": "South Sudan",
    "sudao do sul": "South Sudan",
    "etiópia": "Ethiopia",
    "etiopia": "Ethiopia",
    "eritreia": "Eritrea",
    "somália": "Somalia",
    "somalia": "Somalia",
    "djibuti": "Djibouti",
    "quênia": "Kenya",
    "quenia": "Kenya",
    "tanzânia": "Tanzania",
    "tanzania": "Tanzania",
    "uganda": "Uganda",
    "ruanda": "Rwanda",
    "burundi": "Burundi",
    "nigéria": "Nigeria",
    "nigeria": "Nigeria",
    "níger": "Niger",
    "niger": "Niger",
    "chade": "Chad",
    "mali": "Mali",
    "mauritânia": "Mauritania",
    "mauritania": "Mauritania",
    "senegal": "Senegal",
    "gâmbia": "Gambia",
    "gambia": "Gambia",
    "guiné": "Guinea",
    "guine": "Guinea",
    "guiné-bissau": "Guinea-Bissau",
    "guine-bissau": "Guinea-Bissau",
    "serra leoa": "Sierra Leone",
    "libéria": "Liberia",
    "liberia": "Liberia",
    "costa do marfim": "Ivory Coast",
    "gana": "Ghana",
    "togo": "Togo",
    "benin": "Benin",
    "burkina faso": "Burkina Faso",
    "camarões": "Cameroon",
    "camaroes": "Cameroon",
    "república centro-africana": "Central African Republic",
    "republica centro-africana": "Central African Republic",
    "gabão": "Gabon",
    "gabao": "Gabon",
    "república do congo": "Republic of the Congo",
    "republica do congo": "Republic of the Congo",
    "congo": "Republic of the Congo",
    "república democrática do congo": "Democratic Republic of the Congo",
    "republica democratica do congo": "Democratic Republic of the Congo",
    "angola": "Angola",
    "zâmbia": "Zambia",
    "zambia": "Zambia",
    "zimbábue": "Zimbabwe",
    "zimbabue": "Zimbabwe",
    "moçambique": "Mozambique",
    "mocambique": "Mozambique",
    "malawi": "Malawi",
    "madagáscar": "Madagascar",
    "madagascar": "Madagascar",
    "maurício": "Mauritius",
    "mauricio": "Mauritius",
    "seicheles": "Seychelles",
    "comores": "Comoros",
    "namíbia": "Namibia",
    "namibia": "Namibia",
    "botsuana": "Botswana",
    "lesoto": "Lesotho",
    "suazilândia": "Eswatini",
    "suazilandia": "Eswatini",
    "eswatini": "Eswatini",
    "cabo verde": "Cape Verde",
    "são tomé e príncipe": "Sao Tome and Principe",
    "sao tome e principe": "Sao Tome and Principe",
    "guiné equatorial": "Equatorial Guinea",
    "guine equatorial": "Equatorial Guinea",
    # Asia
    "china": "China",
    "japão": "Japan",
    "japao": "Japan",
    "coreia do sul": "South Korea",
    "coreia do norte": "North Korea",
    "mongólia": "Mongolia",
    "mongolia": "Mongolia",
    "índia": "India",
    "india": "India",
    "paquistão": "Pakistan",
    "paquistao": "Pakistan",
    "bangladesh": "Bangladesh",
    "sri lanka": "Sri Lanka",
    "nepal": "Nepal",
    "butão": "Bhutan",
    "butao": "Bhutan",
    "maldivas": "Maldives",
    "afeganistão": "Afghanistan",
    "afeganistao": "Afghanistan",
    "irã": "Iran",
    "ira": "Iran",
    "iraque": "Iraq",
    "síria": "Syria",
    "siria": "Syria",
    "líbano": "Lebanon",
    "libano": "Lebanon",
    "jordânia": "Jordan",
    "jordania": "Jordan",
    "israel": "Israel",
    "palestina": "Palestine",
    "arábia saudita": "Saudi Arabia",
    "arabia saudita": "Saudi Arabia",
    "iêmen": "Yemen",
    "iemen": "Yemen",
    "omã": "Oman",
    "oma": "Oman",
    "emirados árabes unidos": "United Arab Emirates",
    "emirados arabes unidos": "United Arab Emirates",
    "catar": "Qatar",
    "bahrein": "Bahrain",
    "kuwait": "Kuwait",
    "turquia": "Turkey",
    "armênia": "Armenia",
    "armenia": "Armenia",
    "azerbaijão": "Azerbaijan",
    "azerbaijao": "Azerbaijan",
    "geórgia": "Georgia",
    "georgia": "Georgia",
    "cazaquistão": "Kazakhstan",
    "cazaquistao": "Kazakhstan",
    "uzbequistão": "Uzbekistan",
    "uzbequistao": "Uzbekistan",
    "turcomenistão": "Turkmenistan",
    "turcomenistao": "Turkmenistan",
    "quirguistão": "Kyrgyzstan",
    "quirguistao": "Kyrgyzstan",
    "tadjiquistão": "Tajikistan",
    "tadjiquistao": "Tajikistan",
    "tailândia": "Thailand",
    "tailandia": "Thailand",
    "vietnã": "Vietnam",
    "vietna": "Vietnam",
    "mianmar": "Myanmar",
    "laos": "Laos",
    "camboja": "Cambodia",
    "malásia": "Malaysia",
    "malasia": "Malaysia",
    "singapura": "Singapore",
    "indonésia": "Indonesia",
    "indonesia": "Indonesia",
    "filipinas": "Philippines",
    "brunei": "Brunei",
    "timor-leste": "Timor-Leste",
    "hong kong": "Hong Kong",
    "macau": "Macau",
    "taiwan": "Taiwan",
    "taiwan (formosa)": "Taiwan",
    # Oceania
    "austrália": "Australia",
    "australia": "Australia",
    "nova zelândia": "New Zealand",
    "nova zelandia": "New Zealand",
    "papua nova guiné": "Papua New Guinea",
    "papua nova guine": "Papua New Guinea",
    "fiji": "Fiji",
    "ilhas salomão": "Solomon Islands",
    "ilhas salomao": "Solomon Islands",
    "vanuatu": "Vanuatu",
    "samoa": "Samoa",
    "tonga": "Tonga",
    "micronésia": "Micronesia",
    "micronesia": "Micronesia",
    "palau": "Palau",
    "kiribati": "Kiribati",
    "tuvalu": "Tuvalu",
    "nauru": "Nauru",
    "ilhas marshall": "Marshall Islands",
    # Language variations (other languages)
    "brasil": "Brazil",
    "deutschland": "Germany",
    "nederland": "Netherlands",
    "schweiz": "Switzerland",
    "suisse": "Switzerland",
    "svizzera": "Switzerland",
    "österreich": "Austria",
    "oesterreich": "Austria",
    "españa": "Spain",
    "espana": "Spain",
    "polska": "Poland",
    "france": "France",
    # Common abbreviations
    "usa": "United States",
    "us": "United States",
    "uk": "United Kingdom",
    "uae": "United Arab Emirates",
    "uae": "United Arab Emirates",
    # ISO codes that might be misused
    "il": "Israel",
    "nz": "New Zealand",
    "au": "Australia",
    "ca": "Canada",
    "de": "Germany",
    "fr": "France",
    "nl": "Netherlands",
    "ch": "Switzerland",
    "at": "Austria",
    "es": "Spain",
    "mx": "Mexico",
    "pl": "Poland",
    "it": "Italy",
    "in": "India",
    "br": "Brazil",
    "ar": "Argentina",
    "cl": "Chile",
    "co": "Colombia",
    "pe": "Peru",
    "za": "South Africa",
    "jp": "Japan",
    "cn": "China",
    "kr": "South Korea",
    "sg": "Singapore",
    "my": "Malaysia",
    "th": "Thailand",
    "vn": "Vietnam",
    "id": "Indonesia",
    "ph": "Philippines",
    "tr": "Turkey",
    "eg": "Egypt",
    "ng": "Nigeria",
    "ke": "Kenya",
    "tz": "Tanzania",
    "ma": "Morocco",
    "dz": "Algeria",
    "ru": "Russia",
    "ua": "Ukraine",
    "no": "Norway",
    "se": "Sweden",
    "dk": "Denmark",
    "fi": "Finland",
    "gr": "Greece",
    "pt": "Portugal",
}

# City name normalization map - Fixes common malformed city names
# Empty string = filter out (invalid location)
CITY_NAME_FIXES = {
    # ========== BRAZIL - Partial/malformed names ==========
    "paulo": "São Paulo",
    "sao paulo": "São Paulo",
    "rio": "Rio de Janeiro",
    "janeiro": "Rio de Janeiro",  # "Janeiro" alone → Rio de Janeiro
    "belo": "Belo Horizonte",
    "horizonte": "Belo Horizonte",  # "Horizonte" alone → Belo Horizonte
    "bh": "Belo Horizonte",
    "poa": "Porto Alegre",
    "alegre": "Porto Alegre",  # "Alegre" alone → Porto Alegre
    "floripa": "Florianópolis",
    "bsb": "Brasília",
    "brasilia": "Brasília",
    "sampa": "São Paulo",
    "sp": "São Paulo",
    "rj": "Rio de Janeiro",
    # New partial names
    "andre": "Santo André",
    "preto": "Ribeirão Preto",
    "campo": "Campo Grande",
    "sul": "Porto Alegre",  # Could be "Rio Grande do Sul" but likely Porto Alegre
    "leopoldo": "São Leopoldo",
    "camboriu": "Balneário Camboriú",
    # ========== USA - Common variations ==========
    "san francisco bay area": "San Francisco",
    "sf bay area": "San Francisco",
    "bay area": "San Francisco",
    "nyc": "New York",
    "new york city": "New York",
    "la": "Los Angeles",
    "sf": "San Francisco",
    "philly": "Philadelphia",
    "dc": "Washington",
    "washington dc": "Washington",
    # ========== INDIA - Alternative spellings ==========
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    # ========== EUROPE - Alternative names ==========
    "wien": "Vienna",
    "münchen": "Munich",
    "muenchen": "Munich",
    "köln": "Cologne",
    "koeln": "Cologne",
    "warszawa": "Warsaw",
    "frankfurt am main": "Frankfurt",
    # ========== COUNTRIES MISTAKEN AS CITIES - Filter out ==========
    "united states": "",
    "usa": "",
    "canada": "",
    "brasil": "",
    "brazil": "",
    "mexico": "",
    "méxico": "",
    "india": "",
    "china": "",
    "singapore": "",
    "portugal": "",
    "españa": "",
    "spain": "",
    "france": "",
    "germany": "",
    "deutschland": "",
    "uk": "",
    "united kingdom": "",
    "ireland": "",
    "australia": "",
    "new zealand": "",
    "philippines": "",
    "italy": "",
    "italia": "",
    "nederland": "",
    "netherlands": "",
    "schweiz": "",
    "switzerland": "",
    "österreich": "",
    "poland": "",
    "serbia": "",
    "south africa": "",
    "japan": "",
    "korea": "",
    # ========== REMOTE/HYBRID PATTERNS - Filter out ==========
    "remote": "",
    "hybrid": "",
    "in-office": "",
    "on-site": "",
    "distributed": "",
    "flexible / remote": "",
    "us-remote": "",
    "remote usa": "",
    "remote, us": "",
    "remote, emea": "",
    "remote, americas": "",
    "remote, canada; remote, us": "",
    # Regional patterns
    "northeast - united states": "",
    "us": "",  # "US" alone is not a city
    # ========== INVALID/PLACEHOLDER VALUES - Filter out ==========
    "n/a": "",
    "na": "",
    "location": "",
    "tbd": "",
    "tba": "",
    "various": "",
    "multiple": "",
    "qualquer lugar": "",  # Portuguese for "anywhere"
    "latam": "",
    "emea": "",
    "apac": "",
}


def normalize_city_name(city_name: str) -> str:
    """
    Normaliza nomes de cidades malformados
    Retorna string vazia se deve ser filtrado (Remote, Hybrid, etc)
    """
    normalized = city_name.lower().strip()

    # Filter out empty/null
    if not normalized:
        return ""

    # ========== PATTERN 1: Remote work patterns ==========
    # "Remote", "Remote - USA", "Remote - Canada: Select locations", etc.
    if re.match(r"^remote[\s\-]", normalized) or re.search(r"[\s\-]remote$", normalized, re.IGNORECASE):
        return ""

    # "Hybrid", "Hybrid - Luxembourg", "San Francisco; Hybrid", etc.
    if "hybrid" in normalized:
        return ""

    # "Distributed", "Flexible", "In-Office", "On-Site", "Virtual"
    if re.match(
        r"^(distributed|flexible|in-office|on-site|virtual|anywhere|worldwide|global)", normalized, re.IGNORECASE
    ):
        return ""

    # ========== PATTERN 2: Multi-city lists ==========
    # "Denver, CO;San Francisco, CA;New York, NY;..."
    # "San Francisco, CA; New York City, NY; Austin, TX"
    if ";" in normalized or normalized.count(",") >= 3:
        return ""  # Too many cities, can't pick one

    # ========== PATTERN 3: Invalid placeholders ==========
    # "LOCATION", "N/A", "TBD", "NA", etc.
    if re.match(r"^(location|n/a|na|tbd|tba|various|multiple)$", normalized, re.IGNORECASE):
        return ""

    # Regional aggregations: "LATAM", "EMEA", "APAC"
    if re.match(r"^(latam|emea|apac|americas|europe|asia)$", normalized, re.IGNORECASE):
        return ""

    # ========== PATTERN 4: Check exact match in fixes map ==========
    if normalized in CITY_NAME_FIXES:
        fixed = CITY_NAME_FIXES[normalized]
        return fixed  # Could be empty string if it's a filter pattern

    # ========== PATTERN 5: Extract city from "City, State" format ==========
    # "Charlotte, NC" → "Charlotte"
    # But NOT "San Francisco, CA; New York" (already filtered above)
    if "," in normalized:
        parts = normalized.split(",")
        if len(parts) == 2:
            city_part = parts[0].strip()
            # Recursively check if the extracted city part is valid
            clean_city = normalize_city_name(city_part)
            if clean_city:
                return clean_city

    # ========== PATTERN 6: Extract city from "City; Hybrid" format ==========
    # "San Francisco; Hybrid" → "San Francisco"
    # "Berlin; Hybrid" → "Berlin"
    if ";" in normalized:
        parts = normalized.split(";")
        first_part = parts[0].strip()
        # Recursively check if the first part is a valid city
        clean_city = normalize_city_name(first_part)
        if clean_city:
            return clean_city

    # Return original if no fix/filter found
    return city_name.strip()


def apply_intelligent_fallbacks(country_name: str) -> str:
    """Aplica fallbacks inteligentes para corrigir erros comuns"""
    normalized = country_name.lower().strip()

    # Ignore "Remote" and similar patterns
    if re.match(r"^(remote|anywhere|worldwide|global|flexible|hybrid)", normalized, re.IGNORECASE):
        return ""

    # Ignore remote work prefixes/suffixes
    if re.match(
        r"^(us|uk|ca|au|eu|apac|emea|latam|americas|europe|asia)[\s\-](remote|nationwide|national)",
        normalized,
        re.IGNORECASE,
    ):
        return ""
    if re.match(r"^remote[\s\-](us|uk|ca|au|in|de|fr|nl|it|es)", normalized, re.IGNORECASE):
        return ""

    # Ignore regional aggregations
    if re.match(
        r"^(emea|apac|latam|americas|europe|asia|oceania|north america|south america|central america)$",
        normalized,
        re.IGNORECASE,
    ):
        return ""

    # Ignore non-specific location markers
    if re.match(r"^(n/a|tbd|tba|various|multiple|na)$", normalized, re.IGNORECASE):
        return ""

    # Try alias first
    if normalized in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[normalized]

    # Try city to country
    if normalized in CITY_TO_COUNTRY:
        return CITY_TO_COUNTRY[normalized]

    # Try state to country
    if normalized in STATE_TO_COUNTRY:
        return STATE_TO_COUNTRY[normalized]

    # Return original if no fallback found
    return country_name


def get_or_create_country(conn, country_name: Optional[str]) -> Optional[int]:
    """
    Obtém um país normalizado da tabela sofia.countries
    Tenta múltiplas estratégias: ISO codes, nome comum, fallbacks inteligentes
    NÃO cria novos registros - apenas faz lookup
    """
    if not country_name or not country_name.strip():
        return None

    # Apply intelligent fallbacks first
    corrected_name = apply_intelligent_fallbacks(country_name.strip())
    if not corrected_name:
        return None  # "Remote" etc

    try:
        with conn.cursor() as cursor:
            return get_country_id(cursor, corrected_name)
    except Exception as e:
        print(f'Erro ao normalizar país "{country_name}": {e}')
        return None


def get_or_create_state(conn, state_name: Optional[str], country_id: Optional[int]) -> Optional[int]:
    """
    Obtém um estado normalizado da tabela sofia.states
    Busca por código (2 letras) ou nome dentro do país especificado
    NÃO cria novos registros - apenas faz lookup
    """
    if not state_name or not state_name.strip() or not country_id:
        return None

    try:
        with conn.cursor() as cursor:
            return get_state_id(cursor, state_name.strip(), country_id)
    except Exception as e:
        print(f'Erro ao normalizar estado "{state_name}": {e}')
        return None


def get_or_create_city(
    conn, city_name: Optional[str], state_id: Optional[int], country_id: Optional[int]
) -> Optional[int]:
    """
    Obtém uma cidade normalizada da tabela sofia.cities
    Busca por nome dentro do estado/país especificado
    CRIA AUTOMATICAMENTE se não existir (UPDATED 2026-01-13)
    """
    if not city_name or not city_name.strip() or not country_id:
        return None

    # Apply city name normalization first (fixes "Paulo" → "São Paulo", filters "Remote", etc)
    normalized_name = normalize_city_name(city_name)
    if not normalized_name:
        return None  # Filtered out (Remote, Hybrid, etc)

    try:
        with conn.cursor() as cursor:
            # Try to find existing city
            city_id = get_city_id(cursor, normalized_name, state_id, country_id)

            # If not found and we have a state_id, create it automatically
            if not city_id and state_id:
                try:
                    cursor.execute(
                        """INSERT INTO sofia.cities (name, state_id, country_id, created_at)
                           VALUES (%s, %s, %s, NOW())
                           RETURNING id""",
                        (normalized_name, state_id, country_id)
                    )
                    result = cursor.fetchone()
                    if result:
                        city_id = result[0]
                        conn.commit()
                        print(f"✅ Auto-created city: {normalized_name} (state_id: {state_id})")
                except Exception as create_error:
                    # If duplicate (race condition), try to get it again
                    if '23505' in str(create_error):  # unique_violation
                        conn.rollback()
                        city_id = get_city_id(cursor, normalized_name, state_id, country_id)
                    else:
                        conn.rollback()
                        print(f'⚠️  Failed to auto-create city "{normalized_name}": {create_error}')

            return city_id
    except Exception as e:
        print(f'Erro ao normalizar cidade "{city_name}": {e}')
        return None


def normalize_location(conn, location: dict) -> dict:
    """
    Normaliza uma localização completa (país, estado, cidade)
    Retorna os IDs normalizados

    Args:
        location: dict com keys 'country', 'state', 'city'

    Returns:
        dict com keys 'country_id', 'state_id', 'city_id'
    """
    country_id = get_or_create_country(conn, location.get("country"))
    state_id = get_or_create_state(conn, location.get("state"), country_id)
    city_id = get_or_create_city(conn, location.get("city"), state_id, country_id)

    return {"country_id": country_id, "state_id": state_id, "city_id": city_id}
