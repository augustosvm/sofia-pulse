FROM node:18-alpine

LABEL maintainer="Sofia Intelligence Hub"
LABEL description="Sofia Finance Intelligence - Investment Signal Generator"

# Instalar dependências do sistema
RUN apk add --no-cache \
    bash \
    curl \
    git \
    postgresql-client

# Criar diretório de trabalho
WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependências Node.js
RUN npm ci --only=production && npm cache clean --force

# Copiar código
COPY . .

# Criar diretório de output
RUN mkdir -p output

# Expor porta (se criar API REST no futuro)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "console.log('healthy')" || exit 1

# Comando padrão: rodar demo
CMD ["npm", "run", "demo"]
