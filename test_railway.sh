#!/bin/bash
# Test Railway Ollama Connection

# Railway Ollama URL
RAILWAY_URL="https://ollama-production-016d.up.railway.app:8050"

echo "🔍 Testing Railway Ollama Connection..."
echo "URL: $RAILWAY_URL"
echo ""

# Test 1: Check if endpoint is reachable with timeout
echo "Test 1: Checking connectivity (30 second timeout)..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" --max-time 30 "$RAILWAY_URL/api/tags"
echo ""

# Test 2: Get models list
echo "Test 2: Getting models list..."
curl -s --max-time 30 "$RAILWAY_URL/api/tags" 2>&1 | head -30
echo ""

# Test 3: Test embedding
echo "Test 3: Testing embedding..."
curl -s -X POST --max-time 30 "$RAILWAY_URL/api/embed" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "input": "test query"
  }' 2>&1 | head -30

echo ""
echo "✅ Connection test complete"
