import os

HASH_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class DBConfig:
    DB_USER = os.getenv("POSTGRES_USER") or "postgres"
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD") or "postgres"
    DB_HOST = os.getenv("POSTGRES_HOST") or "localhost"
    DB_PORT = os.getenv("POSTGRES_PORT") or 5432
    DB_DATABASE = os.getenv("POSTGRES_DB") or "ecogram"
    DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
    #DB_URL = 'postgresql+psycopg2://postgres:postgres@localhost:5432/ecogram'


LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(funcName)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': LOG_LEVEL
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': LOG_LEVEL
        },
    }
}
