from logging import config as logging_config

from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING


logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    project_name: str = 'movies'
    redis_host: str = '127.0.0.1'
    redis_port: int = 6379
    elastic_host: str = '127.0.0.1'
    elastic_port: int = 9200


settings = Settings()
