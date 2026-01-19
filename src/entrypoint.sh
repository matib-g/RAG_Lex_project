#!/bin/bash
set -e

# Define paths (relative to WORKDIR /app)
DB_DIR="vectordb/chroma_db"

echo "Checking database status..."

# Simple check: if directory doesn't exist or is empty
if [ ! -d "$DB_DIR" ] || [ -z "$(ls -A "$DB_DIR" 2>/dev/null)" ]; then
    echo "⚠️  Vector database not found or empty."
    echo "🚀 Starting initial bootstrap (downloading & indexing 20 recent acts)..."
    
    # Run the update command with a limit to avoid long wait times
    # This downloads, processes, and indexes 20 items.
    python main.py update --limit 20
    
    echo "✅ Bootstrap complete."
else
    echo "✅ Vector database exists. Skipping bootstrap."
fi

echo "🚀 Starting API Server..."
# Execute the passed command (CMD from Dockerfile)
exec "$@"
