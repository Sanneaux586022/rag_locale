import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
MODELLO_EMBEDDING_ITA = os.environ["MODELLO_EMBEDDING_ITA"]
MODELLO_EMBEDDING_ENG = os.environ["MODELLO_EMBEDDING_ENG"]
MODELLO_GENERAZIONE = os.environ.get("MODELLO_GENERAZIONE", "llama3.2:3b")
URL_LLM_LOCAL_API = os.environ["URL_LLM_LOCAL_API"]
