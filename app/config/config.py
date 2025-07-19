import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    return {
        "LLAMA_CLOUD_API_KEY": os.getenv("LLAMA_CLOUD_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    }

def set_env(config):
    os.environ["LLAMA_CLOUD_API_KEY"] = config["LLAMA_CLOUD_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = config["GOOGLE_API_KEY"]