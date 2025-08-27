from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    # List available models
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error fetching models: {str(e)}")
