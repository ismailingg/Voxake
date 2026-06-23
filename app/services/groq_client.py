from groq import Groq
from app.config import get_settings

settings = get_settings()

groq_client = Groq(api_key=settings.groq_api_key)