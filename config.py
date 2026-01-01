import os

class Config:
    SECRET_KEY = 'your_secret_key'
    MONGO_URI = 'mongodb+srv://sirana53:sirana007@sirajulorg.lioqrwk.mongodb.net/ecommercedb'
    CACHE_TYPE = "redis"
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = 6379
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
