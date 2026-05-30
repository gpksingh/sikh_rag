import ollama
import sys

# Try Railway first, fall back to local
RAILWAY_HOST = 'https://ollama-production-1333.up.railway.app'
LOCAL_HOST = 'http://localhost:11434'

host = RAILWAY_HOST if '--railway' in sys.argv else LOCAL_HOST
print(f"Connecting to: {host}")

client = ollama.Client(host=host)

response = client.chat(model='llama3.1', messages=[
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
])
print(response['message']['content'])