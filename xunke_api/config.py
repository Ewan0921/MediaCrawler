import os


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


API_PORT = _get_int_env("API_PORT", 8090)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_CONCURRENT_PER_ACCOUNT = _get_int_env("MAX_CONCURRENT_PER_ACCOUNT", 3)

