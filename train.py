"""
here we train models, if need be
"""
from dotenv import load_dotenv
import os

load_dotenv('ENV')  # Load environment variables from .env file

api_key = os.getenv("FI")

print(api_key)

