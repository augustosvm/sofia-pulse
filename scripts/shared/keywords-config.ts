/**
 * Configuração centralizada de keywords para coletores de vagas
 * Pode ser reutilizada por diferentes coletores e expandida para outras finalidades
 */

export interface KeywordConfig {
    category: string;
    keywords: {
        pt: string[];  // Português (Brasil)
        en: string[];  // Inglês
        es?: string[]; // Espanhol (opcional)
    };
}

export const JOB_KEYWORDS: KeywordConfig[] = [
    {
        category: 'desenvolvimento-geral',
        keywords: {
            pt: ['desenvolvedor', 'programador', 'engenheiro-de-software', 'analista-de-sistemas'],
            en: ['developer', 'programmer', 'software-engineer', 'systems-analyst'],
            es: ['desarrollador', 'programador', 'ingeniero-de-software']
        }
    },
    {
        category: 'frontend',
        keywords: {
            pt: ['frontend', 'front-end', 'desenvolvedor-frontend'],
            en: ['frontend', 'front-end', 'frontend-developer', 'react', 'vue', 'angular', 'nextjs']
        }
    },
    {
        category: 'backend',
        keywords: {
            pt: ['backend', 'back-end', 'desenvolvedor-backend'],
            en: ['backend', 'back-end', 'backend-developer', 'nodejs', 'java', 'python', 'dotnet', 'golang']
        }
    },
    {
        category: 'fullstack',
        keywords: {
            pt: ['full-stack', 'fullstack'],
            en: ['full-stack', 'fullstack', 'full-stack-developer']
        }
    },
    {
        category: 'ia-ml',
        keywords: {
            pt: ['inteligencia-artificial', 'machine-learning', 'cientista-de-dados', 'aprendizado-de-maquina'],
            en: ['artificial-intelligence', 'machine-learning', 'data-scientist', 'ai-engineer', 'ml-engineer', 'llm', 'deep-learning', 'nlp', 'computer-vision']
        }
    },
    {
        category: 'devops-cloud',
        keywords: {
            pt: ['devops', 'engenheiro-de-nuvem', 'infraestrutura'],
            en: ['devops', 'sre', 'cloud-engineer', 'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform', 'ansible']
        }
    },
    {
        category: 'dados',
        keywords: {
            pt: ['engenheiro-de-dados', 'dba', 'administrador-de-banco-de-dados', 'arquiteto-de-dados', 'analista-de-dados'],
            en: ['data-engineer', 'database-administrator', 'dba', 'data-architect', 'big-data', 'analytics', 'data-analyst', 'bi-developer']
        }
    },
    {
        category: 'qa-testes',
        keywords: {
            pt: ['qa', 'analista-de-testes', 'testador', 'qualidade-de-software'],
            en: ['qa', 'quality-assurance', 'tester', 'test-automation', 'qa-engineer', 'sdet']
        }
    },
    {
        category: 'seguranca',
        keywords: {
            pt: ['seguranca-da-informacao', 'seguranca-cibernetica', 'analista-de-seguranca'],
            en: ['cybersecurity', 'security-engineer', 'infosec', 'pentest', 'penetration-tester', 'security-analyst', 'ethical-hacker']
        }
    },
    {
        category: 'redes',
        keywords: {
            pt: ['engenheiro-de-redes', 'administrador-de-redes', 'infraestrutura-de-ti'],
            en: ['network-engineer', 'network-administrator', 'it-infrastructure']
        }
    },
    {
        category: 'gestao-lideranca',
        keywords: {
            pt: ['tech-lead', 'gerente-de-engenharia', 'scrum-master', 'product-owner', 'cto', 'diretor-de-tecnologia'],
            en: ['tech-lead', 'engineering-manager', 'scrum-master', 'product-owner', 'agile-coach', 'cto', 'vp-engineering']
        }
    },
    {
        category: 'plataformas-especificas',
        keywords: {
            pt: ['salesforce', 'sap', 'oracle', 'totvs'],
            en: ['salesforce', 'sap', 'oracle', 'ibm', 'servicenow', 'workday']
        }
    },
    {
        category: 'mobile',
        keywords: {
            pt: ['desenvolvedor-mobile', 'desenvolvedor-android', 'desenvolvedor-ios'],
            en: ['mobile', 'mobile-developer', 'android', 'ios', 'react-native', 'flutter', 'kotlin', 'swift']
        }
    },
    {
        category: 'certificacoes',
        keywords: {
            pt: ['mcp', 'pmp', 'itil', 'cobit', 'cissp', 'ceh', 'aws-certified', 'azure-certified', 'scrum-master-certified', 'safe', 'prince2', 'togaf', 'comptia', 'ccna', 'ccnp'],
            en: ['mcp', 'pmp', 'itil', 'cobit', 'cissp', 'ceh', 'certified-ethical-hacker', 'aws-certified', 'azure-certified', 'gcp-certified', 'certified-scrum-master', 'safe', 'prince2', 'togaf', 'comptia', 'security+', 'network+', 'ccna', 'ccnp', 'cka', 'ckad']
        }
    },
    {
        category: 'web3-blockchain',
        keywords: {
            pt: ['blockchain', 'web3', 'desenvolvedor-blockchain'],
            en: ['blockchain', 'web3', 'blockchain-developer', 'solidity', 'smart-contracts', 'defi', 'nft']
        }
    },
    {
        category: 'game-dev',
        keywords: {
            pt: ['desenvolvedor-de-jogos', 'game-developer'],
            en: ['game-developer', 'unity', 'unreal-engine', 'game-designer']
        }
    }
];

/**
 * Retorna keywords para um idioma específico
 */
export function getKeywordsByLanguage(language: 'pt' | 'en' | 'es' = 'pt'): string[] {
    const keywords: string[] = [];

    JOB_KEYWORDS.forEach(config => {
        const langKeywords = config.keywords[language];
        if (langKeywords) {
            keywords.push(...langKeywords);
        }
    });

    return keywords;
}

/**
 * Retorna keywords por categoria
 */
export function getKeywordsByCategory(category: string, language: 'pt' | 'en' | 'es' = 'pt'): string[] {
    const config = JOB_KEYWORDS.find(k => k.category === category);
    return config?.keywords[language] || [];
}

/**
 * Retorna todas as categorias disponíveis
 */
export function getCategories(): string[] {
    return JOB_KEYWORDS.map(k => k.category);
}

/**
 * Configuração para uso futuro em outras áreas (papers, trends, etc.)
 * Pode ser expandido conforme necessário
 */
export const RESEARCH_KEYWORDS = {
    // Exemplo para papers acadêmicos
    'ai-research': ['artificial intelligence', 'machine learning', 'deep learning', 'neural networks'],
    'quantum-computing': ['quantum computing', 'quantum algorithms', 'quantum cryptography'],
    'biotech': ['biotechnology', 'genomics', 'crispr', 'gene editing'],
    // ... expandir conforme necessário
};

export const TREND_KEYWORDS = {
    // Exemplo para análise de tendências
    'emerging-tech': ['generative ai', 'llm', 'chatgpt', 'stable diffusion', 'midjourney'],
    'sustainability': ['green tech', 'renewable energy', 'carbon neutral', 'esg'],
    // ... expandir conforme necessário
};
