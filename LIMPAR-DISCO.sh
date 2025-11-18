#!/bin/bash
# Script para limpar disco cheio - Docker e outros

echo "🧹 Limpando disco..."
echo ""

# 1. Ver uso atual
echo "📊 Uso atual do disco:"
df -h /
echo ""

# 2. Limpar Docker (maior culpado)
echo "🐳 Limpando Docker..."
echo ""

# Remover containers parados
echo "  ⏹️  Removendo containers parados..."
docker container prune -f

# Remover imagens não utilizadas
echo "  🖼️  Removendo imagens não utilizadas..."
docker image prune -a -f

# Remover volumes não utilizados
echo "  💾 Removendo volumes não utilizados..."
docker volume prune -f

# Remover networks não utilizados
echo "  🌐 Removendo networks não utilizadas..."
docker network prune -f

# Remover build cache
echo "  🏗️  Removendo build cache..."
docker builder prune -a -f

# Limpeza completa de tudo que não está em uso
echo "  🔥 Limpeza profunda (system prune)..."
docker system prune -a -f --volumes

echo ""
echo "✅ Docker limpo!"
echo ""

# 3. Limpar APT cache
echo "📦 Limpando cache do APT..."
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y
echo ""

# 4. Limpar logs antigos
echo "📝 Limpando logs antigos..."
sudo journalctl --vacuum-time=7d
echo ""

# 5. Limpar npm cache (se tiver)
if command -v npm &> /dev/null; then
    echo "📦 Limpando npm cache..."
    npm cache clean --force
    echo ""
fi

# 6. Limpar pip cache (se tiver)
if command -v pip3 &> /dev/null; then
    echo "🐍 Limpando pip cache..."
    pip3 cache purge 2>/dev/null || echo "  (pip cache não suportado nesta versão)"
    echo ""
fi

# 7. Ver uso final
echo "📊 Uso final do disco:"
df -h /
echo ""

# 8. Mostrar o que está ocupando mais espaço
echo "📊 Top 10 diretórios que ocupam mais espaço:"
sudo du -h --max-depth=1 / 2>/dev/null | sort -hr | head -10
echo ""

echo "✅ Limpeza concluída!"
