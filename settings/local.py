import os

BACKEND_HOST = os.getenv("BACKEND_HOST") or "localhost"
BACKEND_PORT = os.getenv("BACKEND_PORT") or 80

HASH_SECRET_KEY = os.getenv("HASH_SECRET_KEY") or "0d7cf6923e5b7d20b4913e5a485895f400b5ec2c8ea3370e1f924f95ebd09c57"
LOGIN_SECRET = os.getenv("LOGIN_SECRET") or "b437e46982b70e30334ab85d43064d21c0f3956a2c43ab91"
