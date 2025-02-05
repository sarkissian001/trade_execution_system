import os
from dotenv import load_dotenv

load_dotenv()

# TODO: Use those for authentication
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
