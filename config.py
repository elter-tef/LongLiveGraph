import os
from dotenv import load_dotenv  

load_dotenv()
OAI_COMPATIBLE_API_KEY = os.getenv("OAI_COMPATIBLE_API_KEY")
OAI_COMPATIBLE_BASE_URL = os.getenv("OAI_COMPATIBLE_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")