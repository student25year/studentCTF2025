from os import getenv
from os.path import abspath, dirname
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Lucky Duck Casino"

    class Config:
        BASE_DIR = abspath(dirname(__file__))
        SECRET_KEY = getenv('KEY', 'secret_key')
        FLAG = getenv('FLAG', 'stctf{ты забыл положить флаг?!}')

        SQLALCHEMY_DATABASE_URI = getenv('DB_URI', 'sqlite:///users.db')
        SQLALCHEMY_TRACK_MODIFICATIONS = False


settings = Settings()
