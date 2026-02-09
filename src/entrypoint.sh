#!/bin/bash
set -e

# Define paths (relative to WORKDIR /app)
DB_DIR="vectordb/chroma_db"

echo "Checking database status..."

# Simple check: if directory doesn't exist or is empty
if [ ! -d "$DB_DIR" ] || [ -z "$(ls -A "$DB_DIR" 2>/dev/null)" ]; then
    echo "⚠️  Vector database not found or empty."
    echo "🚀 Starting initial bootstrap (downloading & indexing recent acts)..."
    
    # Run the update command, but don't exit if it fails (API might be down)
    if python main.py update --limit 10; then
        echo "✅ Bootstrap complete."
    else
        echo "❌ Bootstrap failed (API error or network issue). You may need to run 'python main.py index' manually later."
    fi
else
    echo "✅ Vector database exists. Skipping bootstrap."
fi

echo "🚀 Starting API Server..."
# Execute the passed command (CMD from Dockerfile)
exec "$@"
