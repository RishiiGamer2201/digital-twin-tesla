#!/bin/bash
set -e

echo "=== Digital Twin of Nikola Tesla - Starting ==="

# Collect data if not already done
if [ ! -f "data/processed/documents.json" ]; then
    echo "Collecting Tesla's writings (first-time setup)..."
    python scripts/collect_data.py || echo "Warning: Some data sources may have failed, continuing..."
else
    echo "Data already collected, skipping."
fi

# Build vectorstore if not already done
if [ ! -d ".chroma" ]; then
    echo "Building vector store (first-time setup)..."
    python scripts/build_vectorstore.py
else
    echo "Vector store already built, skipping."
fi

echo "Starting Flask server on port 7860..."
python server.py
