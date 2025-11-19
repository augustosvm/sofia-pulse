"""
Configuração de Setores Especiais para Sofia Pulse

Temas críticos que precisam de tracking especial:
- Cybersecurity / Data Breaches
- AI Regulation
- Space Race
- Robotics (Humanoid + Automation)
"""

# Setores especiais com keywords para matching
SPECIAL_SECTORS = {
    'Space Industry': {
        'keywords': [
            'space', 'spacex', 'blue origin', 'virgin galactic', 'rocket lab',
            'satellite', 'launch', 'orbital', 'spacecraft', 'rocket',
            'nasa', 'esa', 'jaxa', 'isro', 'cnsa',
            'starlink', 'starship', 'falcon', 'dragon',
            'space tourism', 'moon', 'mars', 'asteroid',
            'space station', 'iss', 'lunar', 'planetary'
        ],
        'priority': 'high',
        'description': 'Space exploration, launches, satellites, space tourism'
    },

    'Robotics & Automation': {
        'keywords': [
            'robot', 'robotics', 'humanoid', 'automation', 'autonomous',
            'boston dynamics', 'tesla bot', 'optimus', 'figure ai',
            'spot', 'atlas', 'industrial robot', 'cobot',
            'warehouse automation', 'agricultural robot', 'drone',
            'automated warehouse', 'robotic arm', 'mobile robot',
            'service robot', 'delivery robot', 'surgical robot'
        ],
        'priority': 'high',
        'description': 'Humanoid robots, industrial automation, autonomous systems'
    },

    'Cybersecurity': {
        'keywords': [
            'cybersecurity', 'cyber security', 'infosec', 'appsec',
            'data breach', 'breach', 'hack', 'hacker', 'ransomware',
            'malware', 'phishing', 'zero-day', 'vulnerability',
            'cve', 'exploit', 'penetration testing', 'pentesting',
            'threat intelligence', 'siem', 'soc', 'incident response',
            'firewall', 'ids', 'ips', 'encryption', 'cryptography',
            'ddos', 'botnet', 'apt', 'supply chain attack'
        ],
        'priority': 'critical',
        'description': 'Cyber attacks, vulnerabilities, data breaches, security tools'
    },

    'AI Regulation': {
        'keywords': [
            'ai act', 'ai regulation', 'ai governance', 'ai policy',
            'eu ai act', 'gdpr', 'lgpd', 'anpd', 'ccpa',
            'privacy law', 'data protection', 'ai ethics',
            'ai compliance', 'responsible ai', 'ai safety',
            'algorithmic bias', 'fairness', 'transparency',
            'explainable ai', 'xai', 'ai audit',
            'regulatory framework', 'tech regulation'
        ],
        'priority': 'high',
        'description': 'AI laws, privacy regulations, compliance, ethics'
    },

    'Quantum Computing': {
        'keywords': [
            'quantum', 'quantum computing', 'qubit', 'quantum algorithm',
            'quantum supremacy', 'quantum advantage', 'ibm quantum',
            'google quantum', 'quantum annealing', 'quantum cryptography',
            'post-quantum', 'quantum resistant'
        ],
        'priority': 'medium',
        'description': 'Quantum computers, algorithms, cryptography'
    },

    'Defense Tech': {
        'keywords': [
            'defense', 'military', 'defense tech', 'dual use',
            'palantir', 'anduril', 'shield ai', 'defense ai',
            'autonomous weapons', 'military drone', 'counter-drone',
            'electronic warfare', 'radar', 'sonar'
        ],
        'priority': 'medium',
        'description': 'Military technology, defense contractors, dual-use AI'
    }
}

# ArXiv categories mapping para setores especiais
ARXIV_SPECIAL_CATEGORIES = {
    'cs.RO': 'Robotics & Automation',
    'physics.space-ph': 'Space Industry',
    'astro-ph': 'Space Industry',
    'cs.CR': 'Cybersecurity',
    'cs.CY': 'AI Regulation',  # Computers and Society
    'quant-ph': 'Quantum Computing'
}

def match_special_sector(text):
    """
    Retorna lista de setores especiais que fazem match com o texto

    Args:
        text: string para fazer matching (título, descrição, keywords, etc)

    Returns:
        list: Lista de setores que fazem match
    """
    if not text:
        return []

    text_lower = text.lower()
    matched_sectors = []

    for sector, config in SPECIAL_SECTORS.items():
        for keyword in config['keywords']:
            if keyword in text_lower:
                if sector not in matched_sectors:
                    matched_sectors.append(sector)
                break

    return matched_sectors

def get_sector_priority(sector):
    """Retorna prioridade de um setor"""
    if sector in SPECIAL_SECTORS:
        return SPECIAL_SECTORS[sector]['priority']
    return 'low'

def is_critical_sector(sector):
    """Retorna True se setor é crítico"""
    return get_sector_priority(sector) == 'critical'

def get_all_sectors():
    """Retorna lista de todos os setores especiais"""
    return list(SPECIAL_SECTORS.keys())

def get_sector_description(sector):
    """Retorna descrição de um setor"""
    if sector in SPECIAL_SECTORS:
        return SPECIAL_SECTORS[sector]['description']
    return ''
