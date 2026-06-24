import os
from openai import OpenAI
from dotenv import load_dotenv # this pushes values into os.environ

load_dotenv(override=True)
gemini_api_key = os.getenv("GEMINI_API_KEY")
print(gemini_api_key)