# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# Database settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "euda_remediation")

# AWS settings
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Amazon Titan model settings
TITAN_TEXT_MODEL = os.getenv("TITAN_TEXT_MODEL", "amazon-titan-v2")
TITAN_IMAGE_MODEL = os.getenv("TITAN_IMAGE_MODEL", "amazon-titan-image-v1") 

# Anthropic API settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")

# Vector embedding dimensions
EMBEDDING_DIMENSION = 1536  # Amazon Titan embeddings dimension