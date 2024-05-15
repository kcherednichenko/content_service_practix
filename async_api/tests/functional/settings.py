from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    elastic_host: str = '127.0.0.1'
    elastic_port: int = 9200
    redis_host: str = '127.0.0.1'
    redis_port: int = 6379
    service_host: str = '127.0.0.1'
    service_port: ints = 8000


test_settings = TestSettings()
