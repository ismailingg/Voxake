from app.config import get_settings
from supabase import create_client

settings = get_settings()

supabase = create_client(settings.supabase_url, settings.supabase_service_key)