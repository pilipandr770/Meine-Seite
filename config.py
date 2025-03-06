import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://user:password@db/mydb")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Використання класу Config
config = Config()
