# backend/app/services/gdd_error_handler.py
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class GDDErrorHandler:
    def __init__(self, max_retries: int = 3, fallback_value: float = 0.0):
        self.max_retries = max_retries
        self.fallback_value = fallback_value

    def handle_errors(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                    if attempt + 1 == self.max_retries:
                        logger.error(f"All retries failed for {func.__name__}. Falling back.")
                        return self.fallback_value
        return wrapper

gdd_error_handler = GDDErrorHandler()
