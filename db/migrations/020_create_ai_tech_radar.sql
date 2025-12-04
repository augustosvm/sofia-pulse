-- Migration: AI Technology Radar Tables
-- Created: 2025-12-04
-- Purpose: Track AI technology trends across GitHub, PyPI, NPM, HuggingFace, and ArXiv

-- ============================================================================
-- 1. GitHub AI Tech Trends
-- ============================================================================
CREATE TABLE IF NOT EXISTS sofia.ai_github_trends (
    id SERIAL PRIMARY KEY,

    -- Technology identification
    tech_key VARCHAR(100) NOT NULL,           -- e.g., 'llama-3', 'deepseek-r1'
    category VARCHAR(50) NOT NULL,            -- 'llm', 'agents', 'rag', 'inference', etc.
    search_query VARCHAR(255) NOT NULL,       -- Original search query used

    -- Metrics
    total_repos INTEGER DEFAULT 0,
    total_stars BIGINT DEFAULT 0,
    total_forks BIGINT DEFAULT 0,
    stars_7d INTEGER DEFAULT 0,
    stars_30d INTEGER DEFAULT 0,
    forks_7d INTEGER DEFAULT 0,
    forks_30d INTEGER DEFAULT 0,

    -- Top repository (for reference)
    top_repo_name VARCHAR(255),
    top_repo_url TEXT,
    top_repo_stars INTEGER,
    top_repo_description TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(tech_key, date)
);

CREATE INDEX IF NOT EXISTS idx_ai_github_tech_key ON sofia.ai_github_trends(tech_key);
CREATE INDEX IF NOT EXISTS idx_ai_github_category ON sofia.ai_github_trends(category);
CREATE INDEX IF NOT EXISTS idx_ai_github_date ON sofia.ai_github_trends(date DESC);
CREATE INDEX IF NOT EXISTS idx_ai_github_metadata ON sofia.ai_github_trends USING GIN(metadata);

-- ============================================================================
-- 2. PyPI AI Packages
-- ============================================================================
CREATE TABLE IF NOT EXISTS sofia.ai_pypi_packages (
    id SERIAL PRIMARY KEY,

    -- Package identification
    package_name VARCHAR(255) NOT NULL,
    tech_key VARCHAR(100) NOT NULL,           -- Normalized key (e.g., 'transformers')
    category VARCHAR(50) NOT NULL,

    -- Download metrics
    downloads_7d BIGINT DEFAULT 0,
    downloads_30d BIGINT DEFAULT 0,
    downloads_90d BIGINT DEFAULT 0,
    downloads_total BIGINT DEFAULT 0,

    -- Package metadata
    version VARCHAR(50),
    description TEXT,
    homepage_url TEXT,
    repository_url TEXT,

    -- Additional metrics
    stars INTEGER DEFAULT 0,                  -- From linked GitHub repo
    dependents INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(package_name, date)
);

CREATE INDEX IF NOT EXISTS idx_ai_pypi_package ON sofia.ai_pypi_packages(package_name);
CREATE INDEX IF NOT EXISTS idx_ai_pypi_tech_key ON sofia.ai_pypi_packages(tech_key);
CREATE INDEX IF NOT EXISTS idx_ai_pypi_category ON sofia.ai_pypi_packages(category);
CREATE INDEX IF NOT EXISTS idx_ai_pypi_date ON sofia.ai_pypi_packages(date DESC);

-- ============================================================================
-- 3. NPM AI Packages
-- ============================================================================
CREATE TABLE IF NOT EXISTS sofia.ai_npm_packages (
    id SERIAL PRIMARY KEY,

    -- Package identification
    package_name VARCHAR(255) NOT NULL,
    tech_key VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,

    -- Download metrics
    downloads_7d BIGINT DEFAULT 0,
    downloads_30d BIGINT DEFAULT 0,
    downloads_90d BIGINT DEFAULT 0,
    downloads_total BIGINT DEFAULT 0,

    -- Package metadata
    version VARCHAR(50),
    description TEXT,
    homepage_url TEXT,
    repository_url TEXT,

    -- Additional metrics
    stars INTEGER DEFAULT 0,
    dependents INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(package_name, date)
);

CREATE INDEX IF NOT EXISTS idx_ai_npm_package ON sofia.ai_npm_packages(package_name);
CREATE INDEX IF NOT EXISTS idx_ai_npm_tech_key ON sofia.ai_npm_packages(tech_key);
CREATE INDEX IF NOT EXISTS idx_ai_npm_category ON sofia.ai_npm_packages(category);
CREATE INDEX IF NOT EXISTS idx_ai_npm_date ON sofia.ai_npm_packages(date DESC);

-- ============================================================================
-- 4. HuggingFace AI Models
-- ============================================================================
CREATE TABLE IF NOT EXISTS sofia.ai_huggingface_models (
    id SERIAL PRIMARY KEY,

    -- Model identification
    model_id VARCHAR(255) NOT NULL,           -- e.g., 'meta-llama/Llama-3.3-70B-Instruct'
    tech_key VARCHAR(100) NOT NULL,           -- e.g., 'llama-3'
    category VARCHAR(50) NOT NULL,

    -- Metrics
    downloads_30d BIGINT DEFAULT 0,
    downloads_total BIGINT DEFAULT 0,
    likes INTEGER DEFAULT 0,

    -- Model metadata
    model_type VARCHAR(100),                  -- 'text-generation', 'text2text', etc.
    pipeline_tag VARCHAR(100),
    library_name VARCHAR(50),                 -- 'transformers', 'diffusers', etc.

    -- Model details
    description TEXT,
    author VARCHAR(255),
    created_at_source TIMESTAMP,
    last_modified TIMESTAMP,

    -- Technical specs
    parameters VARCHAR(50),                   -- e.g., '70B', '7B'
    model_size_gb DECIMAL(10,2),

    -- Metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(model_id, date)
);

CREATE INDEX IF NOT EXISTS idx_ai_hf_model_id ON sofia.ai_huggingface_models(model_id);
CREATE INDEX IF NOT EXISTS idx_ai_hf_tech_key ON sofia.ai_huggingface_models(tech_key);
CREATE INDEX IF NOT EXISTS idx_ai_hf_category ON sofia.ai_huggingface_models(category);
CREATE INDEX IF NOT EXISTS idx_ai_hf_date ON sofia.ai_huggingface_models(date DESC);
CREATE INDEX IF NOT EXISTS idx_ai_hf_tags ON sofia.ai_huggingface_models USING GIN(tags);

-- ============================================================================
-- 5. ArXiv AI Papers
-- ============================================================================
CREATE TABLE IF NOT EXISTS sofia.ai_arxiv_keywords (
    id SERIAL PRIMARY KEY,

    -- Keyword identification
    keyword VARCHAR(100) NOT NULL,
    tech_key VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,

    -- Metrics
    paper_count INTEGER DEFAULT 0,

    -- Monthly breakdown
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,

    -- Top papers (for reference)
    top_paper_ids TEXT[],
    top_paper_titles TEXT[],

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(keyword, year, month)
);

CREATE INDEX IF NOT EXISTS idx_ai_arxiv_keyword ON sofia.ai_arxiv_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_ai_arxiv_tech_key ON sofia.ai_arxiv_keywords(tech_key);
CREATE INDEX IF NOT EXISTS idx_ai_arxiv_category ON sofia.ai_arxiv_keywords(category);
CREATE INDEX IF NOT EXISTS idx_ai_arxiv_year_month ON sofia.ai_arxiv_keywords(year DESC, month DESC);

-- ============================================================================
-- 6. AI Tech Category Mapping (Reference Table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sofia.ai_tech_categories (
    tech_key VARCHAR(100) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    aliases TEXT[],                           -- Alternative names/search terms
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert initial category mappings (EXPANDED - 100+ technologies!)
INSERT INTO sofia.ai_tech_categories (tech_key, category, display_name, description, aliases)
VALUES
    -- ========== LLMs (Open Source) ==========
    ('llama-3', 'llm', 'Llama 3', 'Meta''s Llama 3 language model', ARRAY['llama', 'meta-llama', 'llama3', 'llama 3']),
    ('llama-4', 'llm', 'Llama 4', 'Meta''s Llama 4 (upcoming)', ARRAY['llama4', 'llama 4']),
    ('deepseek', 'llm', 'DeepSeek', 'DeepSeek AI models (R1, V3)', ARRAY['deepseek-r1', 'deepseek-v3', 'deepseek r1']),
    ('mistral', 'llm', 'Mistral', 'Mistral AI models', ARRAY['mixtral', 'codestral', 'mistral-7b']),
    ('phi-4', 'llm', 'Phi-4', 'Microsoft Phi small language models', ARRAY['microsoft/phi', 'phi', 'phi-3']),
    ('gemma', 'llm', 'Gemma', 'Google Gemma models', ARRAY['google/gemma', 'gemma-2', 'gemma-3']),
    ('qwen', 'llm', 'Qwen', 'Alibaba Qwen models', ARRAY['qwen2.5', 'qwen2.5-coder', 'qwen2.5-vl']),
    ('falcon', 'llm', 'Falcon', 'TII Falcon models', ARRAY['falcon-40b', 'falcon-180b']),
    ('vicuna', 'llm', 'Vicuna', 'LMSYS Vicuna chatbot', ARRAY['vicuna-13b', 'vicuna-33b']),
    ('alpaca', 'llm', 'Alpaca', 'Stanford Alpaca instruction-following', ARRAY['stanford-alpaca']),
    ('yi', 'llm', 'Yi', 'Yi series models (01-AI)', ARRAY['yi-34b', 'yi-6b']),
    ('orca', 'llm', 'Orca', 'Microsoft Orca reasoning model', ARRAY['orca-2']),
    ('openchat', 'llm', 'OpenChat', 'OpenChat models', ARRAY['openchat-3.5']),
    ('zephyr', 'llm', 'Zephyr', 'HuggingFace Zephyr', ARRAY['zephyr-7b']),
    ('solar', 'llm', 'SOLAR', 'Upstage SOLAR models', ARRAY['solar-10.7b']),

    -- ========== LLMs (Proprietary/API) ==========
    ('gpt-4', 'llm', 'GPT-4', 'OpenAI GPT-4 series', ARRAY['gpt-4-turbo', 'gpt-4o', 'chatgpt']),
    ('claude', 'llm', 'Claude', 'Anthropic Claude (Opus, Sonnet, Haiku)', ARRAY['claude-3', 'claude-opus', 'claude-sonnet', 'claude-haiku', 'claude-3.5']),
    ('gemini', 'llm', 'Gemini', 'Google Gemini Pro/Ultra', ARRAY['gemini-pro', 'gemini-ultra', 'bard']),
    ('palm', 'llm', 'PaLM', 'Google PaLM 2', ARRAY['palm-2', 'palm2']),
    ('command-r', 'llm', 'Command R', 'Cohere Command R models', ARRAY['command-r-plus']),
    ('ernie', 'llm', 'ERNIE', 'Baidu ERNIE models', ARRAY['ernie-bot']),
    ('grok', 'llm', 'Grok', 'xAI Grok model', ARRAY['grok-1']),

    -- ========== Image Generation ==========
    ('stable-diffusion', 'image-gen', 'Stable Diffusion', 'Image generation models', ARRAY['stablediffusion', 'sd-xl', 'sdxl']),
    ('dalle', 'image-gen', 'DALL-E', 'OpenAI DALL-E 2/3', ARRAY['dalle-2', 'dalle-3']),
    ('midjourney', 'image-gen', 'Midjourney', 'Midjourney image generation', ARRAY['midjourney']),
    ('flux', 'image-gen', 'FLUX', 'Black Forest Labs FLUX', ARRAY['flux-dev', 'flux-schnell']),
    ('firefly', 'image-gen', 'Firefly', 'Adobe Firefly', ARRAY['adobe-firefly']),
    ('imagen', 'image-gen', 'Imagen', 'Google Imagen', ARRAY['imagen-2']),

    -- ========== Video Generation ==========
    ('sora', 'video-gen', 'Sora', 'OpenAI Sora video generation', ARRAY['sora']),
    ('runway', 'video-gen', 'Runway', 'Runway Gen-2/Gen-3', ARRAY['runway-gen2', 'runway-gen3']),
    ('pika', 'video-gen', 'Pika', 'Pika Labs video generation', ARRAY['pika-labs']),
    ('synthesia', 'video-gen', 'Synthesia', 'AI video avatars', ARRAY['synthesia']),

    -- ========== Agent Frameworks ==========
    ('langgraph', 'agents', 'LangGraph', 'LangChain graph-based agents', ARRAY['lang-graph']),
    ('langchain', 'agents', 'LangChain', 'LangChain framework', ARRAY['langchain']),
    ('autogen', 'agents', 'AutoGen', 'Microsoft AutoGen framework', ARRAY['autogen-2', 'pyautogen']),
    ('crewai', 'agents', 'CrewAI', 'Multi-agent orchestration', ARRAY['crew-ai']),
    ('taskweaver', 'agents', 'TaskWeaver', 'Microsoft TaskWeaver', ARRAY['task-weaver']),
    ('pydantic-ai', 'agents', 'Pydantic AI', 'Type-safe AI agents', ARRAY['pydantic_ai']),
    ('smolagents', 'agents', 'SmolAgents', 'HuggingFace lightweight agents', ARRAY['smol-agents']),
    ('agents', 'agents', 'LlamaIndex Agents', 'LlamaIndex agent framework', ARRAY['llama-index-agents']),
    ('haystack', 'agents', 'Haystack', 'deepset Haystack NLP framework', ARRAY['haystack-ai']),
    ('semantic-kernel', 'agents', 'Semantic Kernel', 'Microsoft Semantic Kernel', ARRAY['semantic-kernel']),

    -- ========== Inference & Optimization ==========
    ('vllm', 'inference', 'vLLM', 'Fast LLM inference engine', ARRAY['vllm']),
    ('tensorrt-llm', 'inference', 'TensorRT-LLM', 'NVIDIA TensorRT for LLMs', ARRAY['tensorrt']),
    ('onnxruntime', 'inference', 'ONNX Runtime', 'Cross-platform inference', ARRAY['onnxruntime-gpu', 'onnxruntime-web']),
    ('mlc-llm', 'inference', 'MLC-LLM', 'Machine Learning Compilation for LLMs', ARRAY['web-llm']),
    ('transformers-js', 'inference', 'Transformers.js', 'Run transformers in browser', ARRAY['transformersjs']),
    ('gguf', 'inference', 'GGUF', 'Quantized model format', ARRAY['ggml', 'llama.cpp']),
    ('llama-cpp', 'inference', 'llama.cpp', 'C++ LLM inference', ARRAY['llamacpp']),
    ('ctransformers', 'inference', 'CTransformers', 'Python bindings for GGML', ARRAY['ctransformers']),
    ('exllama', 'inference', 'ExLlama', 'Fast GPTQ inference', ARRAY['exllamav2']),
    ('gptq', 'inference', 'GPTQ', 'GPU quantization', ARRAY['auto-gptq', 'autogptq']),
    ('awq', 'inference', 'AWQ', 'Activation-aware quantization', ARRAY['autoawq']),
    ('bitsandbytes', 'inference', 'BitsAndBytes', '8-bit/4-bit quantization', ARRAY['bitsandbytes']),
    ('deepspeed', 'inference', 'DeepSpeed', 'Microsoft DeepSpeed training/inference', ARRAY['deepspeed']),
    ('triton', 'inference', 'Triton', 'NVIDIA Triton Inference Server', ARRAY['triton-inference']),

    -- ========== RAG & Embeddings ==========
    ('graphrag', 'rag', 'GraphRAG', 'Microsoft GraphRAG', ARRAY['graph-rag']),
    ('rag-island', 'rag', 'RAG Island', 'Advanced RAG architecture', ARRAY['ragisland']),
    ('colbert', 'rag', 'ColBERT', 'Late interaction retrieval', ARRAY['colbertv2', 'colbertv3']),
    ('llamaindex', 'rag', 'LlamaIndex', 'Data framework for LLMs', ARRAY['llama-index', 'gpt-index']),
    ('sentence-transformers', 'rag', 'Sentence Transformers', 'Embedding models', ARRAY['sbert']),
    ('e5', 'rag', 'E5 Embeddings', 'Microsoft E5 embeddings', ARRAY['e5-base', 'e5-large']),
    ('gte', 'rag', 'GTE Embeddings', 'Alibaba GTE embeddings', ARRAY['gte-large']),
    ('bge', 'rag', 'BGE Embeddings', 'BAAI BGE embeddings', ARRAY['bge-large']),

    -- ========== Vector Databases ==========
    ('chromadb', 'rag', 'ChromaDB', 'Vector database', ARRAY['chroma']),
    ('milvus', 'rag', 'Milvus', 'Vector database', ARRAY['zilliz']),
    ('pgvector', 'rag', 'pgvector', 'PostgreSQL vector extension', ARRAY['pg-vector']),
    ('lancedb', 'rag', 'LanceDB', 'Vector database', ARRAY['lance-db']),
    ('qdrant', 'rag', 'Qdrant', 'Vector search engine', ARRAY['qdrant']),
    ('weaviate', 'rag', 'Weaviate', 'Vector database', ARRAY['weaviate']),
    ('pinecone', 'rag', 'Pinecone', 'Managed vector database', ARRAY['pinecone']),
    ('faiss', 'rag', 'FAISS', 'Facebook AI Similarity Search', ARRAY['faiss-gpu']),
    ('voyage-ai', 'rag', 'Voyage AI', 'Embedding models', ARRAY['voyage']),

    -- ========== Data & Lakehouse ==========
    ('duckdb', 'data', 'DuckDB', 'In-process SQL OLAP database', ARRAY['duckdb-ai']),
    ('polars', 'data', 'Polars', 'Fast DataFrame library', ARRAY['polars']),
    ('pg-lake', 'data', 'pg_lake', 'PostgreSQL lakehouse extension', ARRAY['pglake']),
    ('delta-lake', 'data', 'Delta Lake', 'Open table format', ARRAY['deltalake']),
    ('motherduck', 'data', 'MotherDuck', 'Serverless DuckDB', ARRAY['mother-duck']),
    ('apache-iceberg', 'data', 'Apache Iceberg', 'Table format for huge analytic datasets', ARRAY['iceberg']),

    -- ========== Multimodal ==========
    ('llava', 'multimodal', 'LLaVA', 'Visual language model', ARRAY['llava-next', 'llava-1.5']),
    ('qwen-vl', 'multimodal', 'Qwen-VL', 'Qwen vision-language', ARRAY['qwen2.5-vl', 'qwen2-vl']),
    ('janus', 'multimodal', 'Janus', 'Multimodal understanding', ARRAY['janus-flow']),
    ('deepseek-vl', 'multimodal', 'DeepSeek-VL', 'DeepSeek vision-language', ARRAY['deepseekvl']),
    ('siglip', 'multimodal', 'SigLIP', 'Vision encoder', ARRAY['sig-lip']),
    ('clip', 'multimodal', 'CLIP', 'OpenAI CLIP vision-language', ARRAY['openai-clip']),
    ('blip', 'multimodal', 'BLIP', 'Salesforce BLIP models', ARRAY['blip-2']),
    ('fuyu', 'multimodal', 'Fuyu', 'Adept Fuyu multimodal', ARRAY['fuyu-8b']),
    ('cogvlm', 'multimodal', 'CogVLM', 'CogVLM visual language model', ARRAY['cogvlm']),

    -- ========== Audio/Voice ==========
    ('openvoice', 'audio', 'OpenVoice', 'Voice cloning', ARRAY['open-voice']),
    ('cosyvoice', 'audio', 'CosyVoice', 'TTS system', ARRAY['cosy-voice']),
    ('bark', 'audio', 'Bark', 'Text-to-audio model', ARRAY['bark-2', 'suno-bark']),
    ('styletts', 'audio', 'StyleTTS', 'Expressive TTS', ARRAY['style-tts', 'styletts2']),
    ('whisper', 'audio', 'Whisper', 'OpenAI speech recognition', ARRAY['openai-whisper', 'whisper-large']),
    ('xtts', 'audio', 'XTTS', 'Coqui XTTS voice cloning', ARRAY['xtts-v2']),
    ('elevenlabs', 'audio', 'ElevenLabs', 'ElevenLabs TTS API', ARRAY['elevenlabs']),
    ('musicgen', 'audio', 'MusicGen', 'Meta music generation', ARRAY['musicgen']),
    ('audiogen', 'audio', 'AudioGen', 'Meta audio generation', ARRAY['audiogen']),

    -- ========== Coding Assistants ==========
    ('cursor-ai', 'devtools', 'Cursor', 'AI-native code editor', ARRAY['cursor']),
    ('aider', 'devtools', 'Aider', 'AI pair programming', ARRAY['aider-chat']),
    ('continue-dev', 'devtools', 'Continue', 'VS Code AI extension', ARRAY['continue']),
    ('open-interpreter', 'devtools', 'Open Interpreter', 'Natural language coding', ARRAY['openinterpreter']),
    ('copilot', 'devtools', 'GitHub Copilot', 'GitHub Copilot', ARRAY['github-copilot', 'copilot-agents']),
    ('codeium', 'devtools', 'Codeium', 'Codeium AI coding', ARRAY['codeium']),
    ('tabnine', 'devtools', 'Tabnine', 'Tabnine AI autocomplete', ARRAY['tabnine']),
    ('windsurf', 'devtools', 'WindSurf', 'AI coding assistant', ARRAY['wind-surf']),
    ('replit-ghostwriter', 'devtools', 'Replit Ghostwriter', 'Replit AI', ARRAY['ghostwriter']),
    ('sourcegraph-cody', 'devtools', 'Cody', 'Sourcegraph Cody', ARRAY['cody']),

    -- ========== Edge/On-Device ==========
    ('mlx', 'edge', 'Apple MLX', 'Apple Silicon ML framework', ARRAY['apple-mlx']),
    ('qualcomm-ai', 'edge', 'Qualcomm AI Hub', 'Qualcomm on-device AI', ARRAY['qualcomm']),
    ('gemma-edge', 'edge', 'Gemma Edge', 'Gemma for edge devices', ARRAY['gemma-on-device']),
    ('llama-edge', 'edge', 'LLaMA Edge', 'LLaMA for edge devices', ARRAY['llama-on-device']),
    ('mediapipe', 'edge', 'MediaPipe', 'Google MediaPipe on-device ML', ARRAY['mediapipe']),
    ('tensorflow-lite', 'edge', 'TensorFlow Lite', 'TensorFlow for mobile/edge', ARRAY['tflite']),
    ('core-ml', 'edge', 'Core ML', 'Apple Core ML', ARRAY['coreml']),
    ('pytorch-mobile', 'edge', 'PyTorch Mobile', 'PyTorch on mobile', ARRAY['pytorch-mobile']),

    -- ========== AI Frameworks (General) ==========
    ('pytorch', 'framework', 'PyTorch', 'Meta PyTorch', ARRAY['torch']),
    ('tensorflow', 'framework', 'TensorFlow', 'Google TensorFlow', ARRAY['tf']),
    ('jax', 'framework', 'JAX', 'Google JAX', ARRAY['jax']),
    ('transformers', 'framework', 'Transformers', 'HuggingFace Transformers', ARRAY['huggingface-transformers']),
    ('diffusers', 'framework', 'Diffusers', 'HuggingFace Diffusers', ARRAY['huggingface-diffusers']),
    ('accelerate', 'framework', 'Accelerate', 'HuggingFace Accelerate', ARRAY['huggingface-accelerate']),
    ('peft', 'framework', 'PEFT', 'Parameter-Efficient Fine-Tuning', ARRAY['lora', 'qlora']),
    ('axolotl', 'framework', 'Axolotl', 'LLM fine-tuning framework', ARRAY['axolotl']),
    ('unsloth', 'framework', 'Unsloth', 'Fast LLM fine-tuning', ARRAY['unsloth']),

    -- ========== AI Safety & Alignment ==========
    ('guardrails', 'safety', 'Guardrails', 'Guardrails AI validation', ARRAY['guardrails-ai']),
    ('nemo-guardrails', 'safety', 'NeMo Guardrails', 'NVIDIA NeMo Guardrails', ARRAY['nemo-guardrails']),
    ('llm-guard', 'safety', 'LLM Guard', 'LLM security toolkit', ARRAY['llmguard']),
    ('constitutional-ai', 'safety', 'Constitutional AI', 'AI alignment technique', ARRAY['constitutional-ai']),
    ('rlhf', 'safety', 'RLHF', 'Reinforcement Learning from Human Feedback', ARRAY['rlhf']),

    -- ========== Observability & Monitoring ==========
    ('langfuse', 'observability', 'Langfuse', 'LLM tracing and monitoring', ARRAY['langfuse']),
    ('langsmith', 'observability', 'LangSmith', 'LangChain debugging platform', ARRAY['langsmith']),
    ('phoenix', 'observability', 'Phoenix', 'Arize Phoenix LLM observability', ARRAY['arize-phoenix']),
    ('weave', 'observability', 'Weave', 'Weights & Biases Weave', ARRAY['wandb-weave']),
    ('promptlayer', 'observability', 'PromptLayer', 'Prompt engineering platform', ARRAY['promptlayer']),

    -- ========== Testing & Evaluation ==========
    ('promptfoo', 'testing', 'promptfoo', 'LLM testing framework', ARRAY['promptfoo']),
    ('evalplus', 'testing', 'EvalPlus', 'Code generation evaluation', ARRAY['evalplus']),
    ('ragas', 'testing', 'RAGAS', 'RAG evaluation framework', ARRAY['ragas'])
ON CONFLICT (tech_key) DO NOTHING;

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE sofia.ai_github_trends IS 'GitHub trends for AI technologies';
COMMENT ON TABLE sofia.ai_pypi_packages IS 'PyPI download stats for AI packages';
COMMENT ON TABLE sofia.ai_npm_packages IS 'NPM download stats for AI packages';
COMMENT ON TABLE sofia.ai_huggingface_models IS 'HuggingFace model downloads and popularity';
COMMENT ON TABLE sofia.ai_arxiv_keywords IS 'ArXiv paper counts by AI keyword/technology';
COMMENT ON TABLE sofia.ai_tech_categories IS 'Mapping of AI technologies to categories';
