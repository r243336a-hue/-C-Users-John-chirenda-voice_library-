"""
Configuration settings for the Voice Library application.

Manages environment-specific settings and feature flags.
"""

import os
from pathlib import Path


class BaseConfig:
    """Base configuration with common settings."""
    
    # Application
    APP_NAME = 'Voice Library'
    APP_VERSION = '2.0.0'
    
    # Database
    DB_PATH = Path(__file__).parent / "data" / "database" / "library.db"
    DB_TIMEOUT = 5
    
    # Search
    MAX_SEARCH_RESULTS = 5
    MAX_QUERY_LENGTH = 100
    SEARCH_TIMEOUT = 10
    
    # Speech Recognition
    SPEECH_TIMEOUT = 5
    PHRASE_TIME_LIMIT = 5
    SPEECH_RECOGNITION_TIMEOUT = 30
    SUPPORTED_ENCODINGS = ['utf-8', 'latin-1', 'ascii']
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JSON_SORT_KEYS = False
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'voice_library.log'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
    # Caching
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    
    DEBUG = True
    TESTING = True
    DB_PATH = ':memory:'  # Use in-memory database for tests
    LOG_LEVEL = 'WARNING'


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'
    
    # Override with environment variables in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    DB_PATH = Path(os.getenv('DB_PATH', BaseConfig.DB_PATH))


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration for specified environment."""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
