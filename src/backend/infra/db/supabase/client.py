from supabase import create_client

from src.shared.config import settings
from src.shared.logger import logger

supabase = None


def create_supabase(url=None, key=None):
    url: str = url if url else settings.database_settings.supabase_url
    key: str = key if key else settings.database_settings.supabase_key

    return create_client(url, key)


def init_supabase(url=None, key=None) -> None:
    global supabase
    if not supabase:
        try:
            supabase = create_supabase(url=url, key=key)
            logger.info('Created supabase client successfully.')
        except Exception as e:
            logger.exception(f'Exception while creating supabase: {e}')
            raise Exception()
