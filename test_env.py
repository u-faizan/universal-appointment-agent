import os
from dotenv import load_dotenv
   
print("Before load_dotenv:")
print(f"MISTRAL_API_KEY: {os.getenv('MISTRAL_API_KEY')}")
load_dotenv()
   
print("After load_dotenv:")
print(f"MISTRAL_API_KEY: {os.getenv('MISTRAL_API_KEY')}")
   
   # Check if .env file exists
import pathlib
env_file = pathlib.Path('.env')
print(f".env file exists: {env_file.exists()}")
if env_file.exists():
    print(f".env file contents:")
    print(env_file.read_text())