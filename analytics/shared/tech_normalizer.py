"""
Tech Name Normalizer - Sofia Pulse
Shared module to normalize technology names across all analytics reports.

Usage:
    from shared.tech_normalizer import normalize_tech_name, normalize_tech_dict
"""

from typing import Dict, Any

# Comprehensive mapping of tech name aliases (lowercase → canonical name)
TECH_ALIASES = {
    # Programming Languages
    'javascript': 'JavaScript',
    'js': 'JavaScript',
    'typescript': 'TypeScript',
    'ts': 'TypeScript',
    'python': 'Python',
    'py': 'Python',
    'rust': 'Rust',
    'go': 'Go',
    'golang': 'Go',
    'java': 'Java',
    'c++': 'C++',
    'cpp': 'C++',
    'csharp': 'C#',
    'c#': 'C#',
    'ruby': 'Ruby',
    'rb': 'Ruby',
    'php': 'PHP',
    'swift': 'Swift',
    'kotlin': 'Kotlin',
    'kt': 'Kotlin',
    'elixir': 'Elixir',
    'scala': 'Scala',
    'zig': 'Zig',
    'julia': 'Julia',
    'r': 'R',
    'haskell': 'Haskell',
    'lua': 'Lua',
    'perl': 'Perl',
    'dart': 'Dart',
    'objective-c': 'Objective-C',
    'objectivec': 'Objective-C',
    'objc': 'Objective-C',
    'clojure': 'Clojure',
    'erlang': 'Erlang',
    'f#': 'F#',
    'fsharp': 'F#',
    'ocaml': 'OCaml',
    'nim': 'Nim',
    'v': 'V',
    'vlang': 'V',
    'crystal': 'Crystal',
    'groovy': 'Groovy',
    'shell': 'Shell',
    'bash': 'Shell',
    'powershell': 'PowerShell',

    # Frontend Frameworks
    'react': 'React',
    'reactjs': 'React',
    'react.js': 'React',
    'vue': 'Vue',
    'vuejs': 'Vue',
    'vue.js': 'Vue',
    'angular': 'Angular',
    'angularjs': 'Angular',
    'svelte': 'Svelte',
    'nextjs': 'Next.js',
    'next.js': 'Next.js',
    'next': 'Next.js',
    'nuxt': 'Nuxt',
    'nuxtjs': 'Nuxt',
    'nuxt.js': 'Nuxt',
    'remix': 'Remix',
    'astro': 'Astro',
    'solid': 'SolidJS',
    'solidjs': 'SolidJS',
    'qwik': 'Qwik',
    'preact': 'Preact',
    'ember': 'Ember',
    'emberjs': 'Ember',
    'backbone': 'Backbone',
    'htmx': 'HTMX',
    'alpine': 'Alpine.js',
    'alpinejs': 'Alpine.js',

    # CSS/UI Frameworks
    'tailwind': 'Tailwind CSS',
    'tailwindcss': 'Tailwind CSS',
    'bootstrap': 'Bootstrap',
    'material-ui': 'Material UI',
    'mui': 'Material UI',
    'chakra': 'Chakra UI',
    'chakra-ui': 'Chakra UI',
    'antd': 'Ant Design',
    'ant design': 'Ant Design',
    'styled-components': 'styled-components',
    'emotion': 'Emotion',
    'sass': 'Sass',
    'scss': 'Sass',
    'less': 'Less',

    # Backend Frameworks
    'django': 'Django',
    'flask': 'Flask',
    'fastapi': 'FastAPI',
    'fast-api': 'FastAPI',
    'rails': 'Rails',
    'ruby on rails': 'Rails',
    'ror': 'Rails',
    'laravel': 'Laravel',
    'spring': 'Spring',
    'springboot': 'Spring Boot',
    'spring boot': 'Spring Boot',
    'spring-boot': 'Spring Boot',
    'express': 'Express',
    'expressjs': 'Express',
    'express.js': 'Express',
    'nestjs': 'NestJS',
    'nest.js': 'NestJS',
    'nest': 'NestJS',
    'fastify': 'Fastify',
    'koa': 'Koa',
    'koajs': 'Koa',
    'hapi': 'Hapi',
    'hapijs': 'Hapi',
    'gin': 'Gin',
    'echo': 'Echo',
    'fiber': 'Fiber',
    'actix': 'Actix',
    'rocket': 'Rocket',
    'phoenix': 'Phoenix',
    'asp.net': 'ASP.NET',
    'aspnet': 'ASP.NET',
    '.net': '.NET',
    'dotnet': '.NET',
    'blazor': 'Blazor',

    # AI/ML Frameworks
    'tensorflow': 'TensorFlow',
    'tf': 'TensorFlow',
    'pytorch': 'PyTorch',
    'torch': 'PyTorch',
    'keras': 'Keras',
    'scikit-learn': 'scikit-learn',
    'sklearn': 'scikit-learn',
    'scikitlearn': 'scikit-learn',
    'jax': 'JAX',
    'huggingface': 'Hugging Face',
    'hugging face': 'Hugging Face',
    'hf': 'Hugging Face',
    'langchain': 'LangChain',
    'llamaindex': 'LlamaIndex',
    'llama-index': 'LlamaIndex',
    'openai': 'OpenAI',
    'gpt': 'GPT',
    'chatgpt': 'ChatGPT',
    'llama': 'LLaMA',
    'ollama': 'Ollama',
    'mistral': 'Mistral',
    'claude': 'Claude',
    'anthropic': 'Anthropic',
    'stable diffusion': 'Stable Diffusion',
    'stablediffusion': 'Stable Diffusion',
    'midjourney': 'Midjourney',

    # DevOps/Infrastructure
    'kubernetes': 'Kubernetes',
    'k8s': 'Kubernetes',
    'docker': 'Docker',
    'terraform': 'Terraform',
    'tf': 'Terraform',  # Note: conflicts with TensorFlow - context dependent
    'ansible': 'Ansible',
    'jenkins': 'Jenkins',
    'github actions': 'GitHub Actions',
    'gitlab ci': 'GitLab CI',
    'circleci': 'CircleCI',
    'travis': 'Travis CI',
    'travisci': 'Travis CI',
    'argocd': 'ArgoCD',
    'argo': 'ArgoCD',
    'helm': 'Helm',
    'prometheus': 'Prometheus',
    'grafana': 'Grafana',
    'datadog': 'Datadog',
    'newrelic': 'New Relic',
    'pulumi': 'Pulumi',

    # Cloud Providers
    'aws': 'AWS',
    'amazon web services': 'AWS',
    'gcp': 'GCP',
    'google cloud': 'GCP',
    'google cloud platform': 'GCP',
    'azure': 'Azure',
    'microsoft azure': 'Azure',
    'digitalocean': 'DigitalOcean',
    'do': 'DigitalOcean',
    'linode': 'Linode',
    'vercel': 'Vercel',
    'netlify': 'Netlify',
    'cloudflare': 'Cloudflare',
    'fly.io': 'Fly.io',
    'flyio': 'Fly.io',
    'railway': 'Railway',
    'render': 'Render',
    'heroku': 'Heroku',

    # Databases
    'postgres': 'PostgreSQL',
    'postgresql': 'PostgreSQL',
    'pg': 'PostgreSQL',
    'mysql': 'MySQL',
    'mariadb': 'MariaDB',
    'mongodb': 'MongoDB',
    'mongo': 'MongoDB',
    'redis': 'Redis',
    'elasticsearch': 'Elasticsearch',
    'es': 'Elasticsearch',
    'opensearch': 'OpenSearch',
    'sqlite': 'SQLite',
    'cassandra': 'Cassandra',
    'dynamodb': 'DynamoDB',
    'firestore': 'Firestore',
    'cockroachdb': 'CockroachDB',
    'cockroach': 'CockroachDB',
    'planetscale': 'PlanetScale',
    'supabase': 'Supabase',
    'neon': 'Neon',
    'tidb': 'TiDB',
    'singlestore': 'SingleStore',
    'clickhouse': 'ClickHouse',
    'timescaledb': 'TimescaleDB',
    'timescale': 'TimescaleDB',
    'influxdb': 'InfluxDB',
    'neo4j': 'Neo4j',
    'dgraph': 'Dgraph',
    'arangodb': 'ArangoDB',

    # Message Queues
    'kafka': 'Kafka',
    'apache kafka': 'Kafka',
    'rabbitmq': 'RabbitMQ',
    'rabbit mq': 'RabbitMQ',
    'pulsar': 'Apache Pulsar',
    'nats': 'NATS',
    'sqs': 'AWS SQS',
    'aws sqs': 'AWS SQS',

    # Web Technologies
    'wasm': 'WebAssembly',
    'webassembly': 'WebAssembly',
    'graphql': 'GraphQL',
    'gql': 'GraphQL',
    'grpc': 'gRPC',
    'rest': 'REST',
    'restful': 'REST',
    'websocket': 'WebSocket',
    'websockets': 'WebSocket',
    'sse': 'Server-Sent Events',
    'webrtc': 'WebRTC',
    'trpc': 'tRPC',

    # Build Tools
    'webpack': 'Webpack',
    'vite': 'Vite',
    'vitejs': 'Vite',
    'rollup': 'Rollup',
    'esbuild': 'esbuild',
    'parcel': 'Parcel',
    'turbopack': 'Turbopack',
    'bun': 'Bun',
    'deno': 'Deno',
    'swc': 'SWC',
    'babel': 'Babel',

    # Testing
    'jest': 'Jest',
    'mocha': 'Mocha',
    'pytest': 'pytest',
    'cypress': 'Cypress',
    'playwright': 'Playwright',
    'selenium': 'Selenium',
    'vitest': 'Vitest',
    'junit': 'JUnit',
    'testng': 'TestNG',
    'rspec': 'RSpec',

    # Mobile
    'flutter': 'Flutter',
    'react native': 'React Native',
    'react-native': 'React Native',
    'reactnative': 'React Native',
    'rn': 'React Native',
    'ionic': 'Ionic',
    'xamarin': 'Xamarin',
    'swiftui': 'SwiftUI',
    'jetpack compose': 'Jetpack Compose',
    'compose': 'Jetpack Compose',
    'expo': 'Expo',

    # Other
    'nginx': 'NGINX',
    'apache': 'Apache',
    'caddy': 'Caddy',
    'git': 'Git',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'bitbucket': 'Bitbucket',
    'linux': 'Linux',
    'ubuntu': 'Ubuntu',
    'debian': 'Debian',
    'centos': 'CentOS',
    'fedora': 'Fedora',
    'macos': 'macOS',
    'windows': 'Windows',
    'blockchain': 'Blockchain',
    'web3': 'Web3',
    'solidity': 'Solidity',
    'ethereum': 'Ethereum',
    'eth': 'Ethereum',
    'bitcoin': 'Bitcoin',
    'btc': 'Bitcoin',
    'nft': 'NFT',
    'ipfs': 'IPFS',

    # ORMs
    'prisma': 'Prisma',
    'drizzle': 'Drizzle',
    'typeorm': 'TypeORM',
    'sequelize': 'Sequelize',
    'sqlalchemy': 'SQLAlchemy',
    'peewee': 'Peewee',
    'hibernate': 'Hibernate',
    'eloquent': 'Eloquent',
    'activerecord': 'ActiveRecord',
    'active record': 'ActiveRecord',
}


def normalize_tech_name(tech: str) -> str:
    """
    Normalize a technology name to its canonical form.

    Args:
        tech: Technology name to normalize

    Returns:
        Canonical technology name

    Examples:
        normalize_tech_name('typescript') → 'TypeScript'
        normalize_tech_name('k8s') → 'Kubernetes'
        normalize_tech_name('reactjs') → 'React'
    """
    if not tech:
        return tech
    tech_lower = tech.lower().strip()
    return TECH_ALIASES.get(tech_lower, tech)


def normalize_tech_dict(data: Dict[str, Any], merge_strategy: str = 'sum') -> Dict[str, Any]:
    """
    Normalize all keys in a dictionary using tech name normalization.
    Merges duplicate keys after normalization.

    Args:
        data: Dictionary with tech names as keys
        merge_strategy: How to merge duplicate values ('sum', 'max', 'first', 'last')

    Returns:
        New dictionary with normalized keys

    Example:
        data = {'typescript': 100, 'TypeScript': 50, 'ts': 25}
        normalize_tech_dict(data) → {'TypeScript': 175}
    """
    normalized = {}

    for tech, value in data.items():
        norm_key = normalize_tech_name(tech)

        if norm_key in normalized:
            existing = normalized[norm_key]

            if isinstance(value, dict) and isinstance(existing, dict):
                # Merge dictionaries
                for k, v in value.items():
                    if k in existing and isinstance(v, (int, float)):
                        if merge_strategy == 'sum':
                            existing[k] = existing.get(k, 0) + v
                        elif merge_strategy == 'max':
                            existing[k] = max(existing.get(k, 0), v)
                        elif merge_strategy == 'last':
                            existing[k] = v
                        # 'first' keeps existing value
                    else:
                        existing[k] = v
            elif isinstance(value, (int, float)) and isinstance(existing, (int, float)):
                if merge_strategy == 'sum':
                    normalized[norm_key] = existing + value
                elif merge_strategy == 'max':
                    normalized[norm_key] = max(existing, value)
                elif merge_strategy == 'last':
                    normalized[norm_key] = value
                # 'first' keeps existing value
        else:
            # Copy value to avoid mutation
            if isinstance(value, dict):
                normalized[norm_key] = value.copy()
            else:
                normalized[norm_key] = value

    return normalized


def get_tech_category(tech: str) -> str:
    """
    Get the category of a technology.

    Returns:
        Category string: 'Language', 'Frontend', 'Backend', 'Database',
                        'DevOps', 'AI/ML', 'Mobile', 'Cloud', 'Other'
    """
    norm = normalize_tech_name(tech)

    languages = {
        'JavaScript', 'TypeScript', 'Python', 'Rust', 'Go', 'Java', 'C++', 'C#',
        'Ruby', 'PHP', 'Swift', 'Kotlin', 'Elixir', 'Scala', 'Zig', 'Julia', 'R',
        'Haskell', 'Lua', 'Perl', 'Dart', 'Objective-C', 'Clojure', 'Erlang',
        'F#', 'OCaml', 'Nim', 'V', 'Crystal', 'Groovy', 'Shell', 'PowerShell'
    }

    frontend = {
        'React', 'Vue', 'Angular', 'Svelte', 'Next.js', 'Nuxt', 'Remix', 'Astro',
        'SolidJS', 'Qwik', 'Preact', 'Ember', 'HTMX', 'Alpine.js', 'Tailwind CSS',
        'Bootstrap', 'Material UI', 'Chakra UI', 'styled-components', 'WebAssembly'
    }

    backend = {
        'Django', 'Flask', 'FastAPI', 'Rails', 'Laravel', 'Spring', 'Spring Boot',
        'Express', 'NestJS', 'Fastify', 'Koa', 'Gin', 'Echo', 'Fiber', 'Actix',
        'Phoenix', 'ASP.NET', '.NET', 'Blazor', 'GraphQL', 'gRPC', 'REST'
    }

    databases = {
        'PostgreSQL', 'MySQL', 'MariaDB', 'MongoDB', 'Redis', 'Elasticsearch',
        'SQLite', 'Cassandra', 'DynamoDB', 'CockroachDB', 'PlanetScale',
        'Supabase', 'Neon', 'ClickHouse', 'TimescaleDB', 'Neo4j', 'InfluxDB'
    }

    devops = {
        'Kubernetes', 'Docker', 'Terraform', 'Ansible', 'Jenkins', 'Helm',
        'Prometheus', 'Grafana', 'ArgoCD', 'GitHub Actions', 'GitLab CI',
        'NGINX', 'Apache', 'Caddy', 'Linux', 'Git'
    }

    ai_ml = {
        'TensorFlow', 'PyTorch', 'Keras', 'scikit-learn', 'JAX', 'Hugging Face',
        'LangChain', 'LlamaIndex', 'OpenAI', 'GPT', 'ChatGPT', 'LLaMA', 'Ollama',
        'Mistral', 'Claude', 'Stable Diffusion'
    }

    mobile = {
        'Flutter', 'React Native', 'Ionic', 'Xamarin', 'SwiftUI', 'Jetpack Compose', 'Expo'
    }

    cloud = {
        'AWS', 'GCP', 'Azure', 'DigitalOcean', 'Vercel', 'Netlify', 'Cloudflare',
        'Fly.io', 'Railway', 'Render', 'Heroku'
    }

    if norm in languages:
        return 'Language'
    elif norm in frontend:
        return 'Frontend'
    elif norm in backend:
        return 'Backend'
    elif norm in databases:
        return 'Database'
    elif norm in devops:
        return 'DevOps'
    elif norm in ai_ml:
        return 'AI/ML'
    elif norm in mobile:
        return 'Mobile'
    elif norm in cloud:
        return 'Cloud'
    else:
        return 'Other'
