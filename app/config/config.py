import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    return {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    }

def set_env(config):
    os.environ["GOOGLE_API_KEY"] = config["GOOGLE_API_KEY"]