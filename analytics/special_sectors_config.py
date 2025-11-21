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
            'quantum', 'qubit', 'qbit', 'quantum-computing', 'quantum algorithm',
            'quantum supremacy', 'quantum advantage', 'ibm quantum',
            'google quantum', 'quantum annealing', 'quantum cryptography',
            'post-quantum', 'quantum resistant', 'superposition', 'entanglement',
            'quantum gate', 'quantum circuit', 'quantum error', 'error correction',
            'topological quantum', 'majorana', 'superconducting qubit',
            'trapped ion', 'photonic quantum', 'quantum simulation',
            'variational quantum', 'vqe', 'qaoa', 'quantum machine learning'
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
    },

    # NOVOS SETORES GLOBAIS - 2025-11-19

    'Electric Vehicles & Batteries': {
        'keywords': [
            'electric vehicle', 'ev', 'battery', 'tesla', 'byd', 'rivian',
            'lucid', 'nio', 'xpeng', 'catl', 'lg energy', 'panasonic',
            'lithium', 'solid state battery', 'charging', 'range',
            'battery pack', 'battery cell', 'gigafactory', 'supercharger',
            'fast charging', 'battery chemistry', 'cobalt', 'nickel',
            'lithium iron phosphate', 'lfp', 'ncm', 'nmc'
        ],
        'priority': 'critical',
        'description': 'EVs, battery technology, charging infrastructure'
    },

    'Autonomous Driving': {
        'keywords': [
            'autonomous', 'self-driving', 'waymo', 'cruise', 'fsd',
            'autopilot', 'lidar', 'adas', 'level 4', 'level 5',
            'robotaxi', 'mobileye', 'comma ai', 'openpilot',
            'autonomous vehicle', 'av', 'perception', 'path planning',
            'sensor fusion', 'camera', 'radar', 'ultrasonic'
        ],
        'priority': 'high',
        'description': 'Self-driving cars, ADAS, autonomous systems'
    },

    'Smartphones & Mobile': {
        'keywords': [
            'smartphone', 'iphone', 'android', 'samsung', 'xiaomi',
            'oppo', 'vivo', 'huawei', 'mobile', '5g', 'foldable',
            'qualcomm', 'snapdragon', 'mediatek', 'exynos', 'tensor',
            'apple silicon', 'a17', 'mobile chip', 'arm', 'tsmc'
        ],
        'priority': 'high',
        'description': 'Smartphones, mobile processors, 5G, foldables'
    },

    'Edge AI & Embedded': {
        'keywords': [
            'edge ai', 'edge computing', 'embedded ai', 'nvidia jetson',
            'qualcomm ai', 'tpu', 'neural engine', 'on-device ai',
            'tinyml', 'edge inference', 'iot ai', 'embedded ml',
            'coral', 'hailo', 'kneron', 'onnx', 'quantization'
        ],
        'priority': 'high',
        'description': 'AI on edge devices, embedded systems, on-device ML'
    },

    'Renewable Energy': {
        'keywords': [
            'solar', 'wind', 'renewable', 'clean energy', 'solar panel',
            'wind turbine', 'photovoltaic', 'offshore wind', 'pv',
            'solar farm', 'wind farm', 'perovskite', 'bifacial',
            'energy transition', 'decarbonization', 'net zero',
            'green energy', 'renewable capacity', 'utility scale'
        ],
        'priority': 'critical',
        'description': 'Solar, wind, hydro, renewable energy projects'
    },

    'Nuclear Energy': {
        'keywords': [
            'nuclear', 'nuclear power', 'reactor', 'smr', 'fusion',
            'fission', 'uranium', 'thorium', 'nuscale', 'terrapower',
            'iter', 'tokamak', 'nuclear plant', 'gen 4', 'gen iv',
            'molten salt', 'breeder reactor', 'fast reactor',
            'commonwealth fusion', 'tae technologies'
        ],
        'priority': 'high',
        'description': 'Nuclear power plants, SMRs, fusion reactors'
    },

    'Energy Storage & Grid': {
        'keywords': [
            'energy storage', 'grid', 'battery storage', 'pumped hydro',
            'hydrogen', 'green hydrogen', 'fuel cell', 'microgrid',
            'transmission', 'smart grid', 'grid scale', 'bess',
            'flow battery', 'compressed air', 'thermal storage',
            'virtual power plant', 'demand response', 'grid balancing'
        ],
        'priority': 'high',
        'description': 'Grid modernization, energy storage, hydrogen economy'
    },

    'Databases & Data Infrastructure': {
        'keywords': [
            'database', 'db', 'sql', 'nosql', 'postgresql', 'postgres', 'mongodb',
            'mysql', 'mariadb', 'redis', 'elasticsearch', 'cassandra', 'neo4j',
            'clickhouse', 'snowflake', 'databricks', 'data warehouse', 'datalake',
            'olap', 'oltp', 'vector database', 'graph database', 'embedding database',
            'time series', 'influxdb', 'timescale', 'cockroachdb', 'yugabyte',
            'distributed database', 'acid', 'transaction', 'index', 'indexing',
            'query optimization', 'b-tree', 'lsm tree', 'raft', 'paxos',
            'replication', 'sharding', 'partitioning', 'consistency',
            'data modeling', 'etl', 'data pipeline', 'streaming database',
            'real-time analytics', 'bi', 'business intelligence'
        ],
        'priority': 'medium',
        'description': 'Databases, data warehouses, data infrastructure'
    },

    # NOVOS SETORES 2025-11-21 (para chegar a 20+)

    'Fintech & Payments': {
        'keywords': [
            'fintech', 'payment', 'stripe', 'paypal', 'square', 'adyen',
            'digital wallet', 'mobile payment', 'neobank', 'challenger bank',
            'open banking', 'pix', 'venmo', 'zelle', 'cashapp',
            'buy now pay later', 'bnpl', 'lending', 'credit',
            'remittance', 'cross-border payment', 'cryptocurrency exchange',
            'defi', 'stablecoin', 'cbdc', 'digital currency',
            'banking-as-a-service', 'baas', 'embedded finance'
        ],
        'priority': 'high',
        'description': 'Digital payments, neobanks, embedded finance, BNPL'
    },

    'Biotech & Genomics': {
        'keywords': [
            'biotech', 'biotechnology', 'genomics', 'crispr', 'gene therapy',
            'mrna', 'monoclonal antibody', 'car-t', 'cell therapy',
            'precision medicine', 'personalized medicine', 'sequencing',
            'dna', 'rna', 'proteomics', 'bioinformatics',
            'synthetic biology', 'protein engineering', 'antibody',
            'immunotherapy', 'oncology', 'rare disease',
            'regenerative medicine', 'stem cell', 'organoid'
        ],
        'priority': 'high',
        'description': 'Gene editing, CRISPR, mRNA, precision medicine'
    },

    'Climate Tech & Carbon Capture': {
        'keywords': [
            'climate tech', 'carbon capture', 'ccs', 'dac', 'direct air capture',
            'carbon removal', 'carbon credit', 'carbon offset',
            'climeworks', 'carbon engineering', 'decarbonization',
            'ghg', 'greenhouse gas', 'methane', 'co2',
            'carbon neutral', 'net zero', 'climate change',
            'carbon sequestration', 'afforestation', 'reforestation',
            'biochar', 'enhanced weathering', 'ocean alkalinity'
        ],
        'priority': 'critical',
        'description': 'Carbon capture, climate solutions, decarbonization'
    },

    'Cloud & DevOps': {
        'keywords': [
            'cloud', 'aws', 'azure', 'gcp', 'google cloud', 'kubernetes',
            'docker', 'container', 'serverless', 'lambda', 'fargate',
            'devops', 'ci/cd', 'jenkins', 'gitlab', 'github actions',
            'terraform', 'infrastructure as code', 'iac', 'ansible',
            'microservices', 'service mesh', 'istio', 'envoy',
            'observability', 'monitoring', 'prometheus', 'grafana',
            'datadog', 'newrelic', 'cloudflare', 'cdn'
        ],
        'priority': 'medium',
        'description': 'Cloud platforms, containers, Kubernetes, DevOps tools'
    },

    'Semiconductors & Chips': {
        'keywords': [
            'semiconductor', 'chip', 'tsmc', 'samsung foundry', 'intel foundry',
            'asml', 'euv', 'lithography', 'fab', 'foundry',
            'chip manufacturing', '3nm', '2nm', '1nm', 'gaafet',
            'chiplet', 'packaging', '3d ic', 'chiplet',
            'nvidia', 'amd', 'intel', 'qualcomm', 'mediatek',
            'gpu', 'ai chip', 'tpu', 'npu', 'accelerator',
            'risc-v', 'arm', 'x86', 'instruction set'
        ],
        'priority': 'critical',
        'description': 'Chip manufacturing, fabs, AI accelerators, process nodes'
    },

    'AR/VR & Spatial Computing': {
        'keywords': [
            'ar', 'vr', 'xr', 'augmented reality', 'virtual reality',
            'mixed reality', 'spatial computing', 'meta quest',
            'apple vision pro', 'hololens', 'magic leap', 'snap spectacles',
            'passthrough', 'hand tracking', 'eye tracking', 'haptic',
            'metaverse', 'virtual world', 'avatar', 'digital twin',
            '3d modeling', 'photogrammetry', 'gaussian splatting', 'nerf',
            'webxr', 'openxr', 'unity', 'unreal engine'
        ],
        'priority': 'medium',
        'description': 'AR/VR headsets, spatial computing, metaverse platforms'
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
