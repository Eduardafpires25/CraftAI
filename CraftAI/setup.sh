#!/bin/bash

echo "🚀 Iniciando setup do CraftAI..."

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

# Verificar arquivo .env
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env a partir do exemplo..."
    cp .env.example .env
    echo "⚠️  Por favor, configure sua OPENAI_API_KEY no arquivo .env antes de continuar!"
    echo "   Você pode obter sua chave em: https://platform.openai.com/api-keys"
    read -p "Pressione Enter após configurar sua chave..."
fi

# Construir e iniciar containers
echo "🔨 Construindo containers..."
docker-compose build

echo "🚀 Iniciando serviços..."
docker-compose up -d

echo "⏳ Aguardando serviços iniciarem..."
sleep 10

echo "✅ Setup completo!"
echo ""
echo "🌐 Acesse:"
echo "   Frontend: http://localhost:3001"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔍 Para verificar os logs: docker-compose logs -f"
echo "🛑 Para parar: docker-compose down"
