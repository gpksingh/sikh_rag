#!/bin/bash
# Test Railway Ollama Connection

# Replace with your actual Railway public URL
RAILWAY_URL="https://YOUR_RAILWAY_PUBLIC_URL"

echo "🔍 Testing Railway Ollama Connection..."
echo "URL: $RAILWAY_URL"
echo ""

# Test 1: Check if endpoint is reachable
echo "Test 1: Checking connectivity..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$RAILWAY_URL/api/tags"
echo ""

# Test 2: Get models list
echo "Test 2: Getting models list..."
curl -s "$RAILWAY_URL/api/tags" | head -20
echo ""

# Test 3: Test embedding
echo "Test 3: Testing embedding..."
curl -X POST "$RAILWAY_URL/api/embed" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "input": "test query"
  }' | head -20
