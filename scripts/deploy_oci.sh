#!/bin/bash
# OCI Deployment Script for RAG Lex
# Run this on your OCI ARM instance after SSH

set -e

echo "=== RAG Lex OCI Deployment Script ==="
echo ""

# Check if running on ARM
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
    echo "⚠️  Warning: This script is optimized for ARM64 (aarch64)"
    echo "   Current architecture: $ARCH"
fi

# Step 1: Update system
echo ">>> Step 1: Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Step 2: Install Docker
echo ">>> Step 2: Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed. Please log out and back in, then re-run this script."
    exit 0
else
    echo "Docker already installed: $(docker --version)"
fi

# Step 3: Install Docker Compose
echo ">>> Step 3: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt-get install -y docker-compose-plugin
fi
echo "Docker Compose: $(docker compose version)"

# Step 4: Clone repository (if not exists)
echo ">>> Step 4: Setting up project..."
PROJECT_DIR="$HOME/rag_lex_project"
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "Please clone your repository to $PROJECT_DIR first."
    echo "Example: git clone https://github.com/YOUR_USERNAME/rag_lex_project.git"
    exit 1
fi
cd "$PROJECT_DIR"

# Step 5: Create .env.production from template
echo ">>> Step 5: Checking environment configuration..."
if [[ ! -f ".env.production" ]]; then
    echo "ERROR: .env.production not found!"
    echo "Please copy .env.production.example and configure it:"
    echo "  cp .env.production.example .env.production"
    echo "  nano .env.production"
    exit 1
fi

# Step 6: Create necessary directories
echo ">>> Step 6: Creating directories..."
mkdir -p data/raw_data models vectordb nginx/ssl

# Step 7: Check if model exists
echo ">>> Step 7: Checking model file..."
MODEL_FILE=$(grep LLAMA_MODEL_FILENAME .env.production | cut -d= -f2)
if [[ ! -f "models/$MODEL_FILE" ]]; then
    echo "⚠️  Model file not found: models/$MODEL_FILE"
    echo "Please upload your model file to the models/ directory."
    echo ""
    echo "Option 1: SCP from local machine:"
    echo "  scp /path/to/model.gguf ubuntu@YOUR_OCI_IP:~/rag_lex_project/models/"
    echo ""
    echo "Option 2: Download directly (if hosted):"
    echo "  wget -O models/$MODEL_FILE https://example.com/model.gguf"
    echo ""
    read -p "Continue without model? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 8: Check vectordb
echo ">>> Step 8: Checking vector database..."
if [[ ! -d "vectordb/chroma_db" ]] || [[ -z "$(ls -A vectordb/chroma_db 2>/dev/null)" ]]; then
    echo "⚠️  Vector database not found or empty."
    echo "You will need to run indexing after deployment:"
    echo "  docker exec rag_lex_app python main.py prepare"
    echo "  docker exec rag_lex_app python main.py index"
fi

# Step 9: Build and start containers
echo ">>> Step 9: Building Docker images..."
docker compose -f docker-compose.prod.yml build

echo ">>> Step 10: Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Step 11: Show status
echo ""
echo "=== Deployment Complete ==="
echo ""
docker compose -f docker-compose.prod.yml ps
echo ""
echo "API endpoint: http://$(curl -s ifconfig.me):8000"
echo "Health check: http://$(curl -s ifconfig.me):8000/api/v1/health"
echo ""
echo "Next steps:"
echo "1. Configure SSL with Let's Encrypt (see docs/OCI_DEPLOYMENT.md)"
echo "2. Update CORS_ORIGINS in .env.production with your GitHub Pages URL"
echo "3. If needed, run: docker exec rag_lex_app python main.py index"
echo ""
