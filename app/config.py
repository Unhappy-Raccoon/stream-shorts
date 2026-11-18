from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Stream Shorts"
    admin_token: str = "change-me"
    data_dir: Path = Path("/data")
    whisper_model: str = "small"
    max_source_seconds: int = 21600
    clip_min_seconds: int = 45
    clip_max_seconds: int = 75
    clips_per_day: int = 3
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
