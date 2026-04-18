from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "Mind Island API"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    # Example: mysql+pymysql://root:123456@127.0.0.1:3306/mind_island?charset=utf8mb4
    database_url: str = "mysql+pymysql://root:123456@127.0.0.1:3306/mind_island?charset=utf8mb4"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    siliconflow_api_key: str = ""
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_model: str = "THUDM/GLM-4-9B-0414"
    siliconflow_system_prompt: str = "你是一个温暖、专业、谨慎的校园心理陪伴助手，优先提供支持性建议，不做医疗诊断。"

    analysis_use_hf_encoders: bool = False
    analysis_hf_local_files_only: bool = True
    analysis_text_model_name: str = "bert-base-chinese"
    analysis_image_model_name: str = "google/vit-base-patch16-224-in21k"
    analysis_text_model_dir: str = ""
    analysis_image_model_dir: str = ""

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")


settings = Settings()
