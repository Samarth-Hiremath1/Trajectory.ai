"""
Security configuration settings
"""
import os
from typing import List, Dict, Any

class SecurityConfig:
    """Security configuration settings"""
    
    # Environment settings
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = [
        "Authorization",
        "Content-Type", 
        "X-User-ID",
        "X-Request-ID",
        "Accept",
        "Origin",
        "User-Agent"
    ]
    
    # Trusted hosts
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*.vercel.app").split(",")
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    REDIS_URL = os.getenv("REDIS_URL")
    
    # File upload security
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB default
    ALLOWED_FILE_TYPES = ["application/pdf", "text/plain"]
    VIRUS_SCANNING_ENABLED = os.getenv("VIRUS_SCANNING_ENABLED", "true").lower() == "true"
    
    # Authentication settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Supabase settings
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    # Content Security Policy
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.huggingface.co https://*.supabase.co; "
        "frame-ancestors 'none';"
    )
    
    # Input validation settings
    MAX_STRING_LENGTH = int(os.getenv("MAX_STRING_LENGTH", "10000"))
    MAX_DICT_DEPTH = int(os.getenv("MAX_DICT_DEPTH", "5"))
    MAX_LIST_LENGTH = int(os.getenv("MAX_LIST_LENGTH", "1000"))
    
    # Logging settings
    LOG_SECURITY_EVENTS = os.getenv("LOG_SECURITY_EVENTS", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """
        Validate security configuration
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required environment variables
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY"
        ]
        
        for var in required_vars:
            if not getattr(cls, var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Check production-specific requirements
        if cls.ENVIRONMENT == "production":
            if cls.DEBUG:
                errors.append("DEBUG should be disabled in production")
            
            if not cls.SUPABASE_SERVICE_ROLE_KEY:
                errors.append("SUPABASE_SERVICE_ROLE_KEY required in production")
            
            if "localhost" in cls.CORS_ORIGINS:
                errors.append("localhost should not be in CORS_ORIGINS in production")
        
        # Validate file size limits
        if cls.MAX_FILE_SIZE > 100 * 1024 * 1024:  # 100MB
            errors.append("MAX_FILE_SIZE should not exceed 100MB")
        
        return errors
    
    @classmethod
    def get_security_summary(cls) -> Dict[str, Any]:
        """
        Get security configuration summary
        
        Returns:
            Dictionary with security settings summary
        """
        return {
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "rate_limiting": cls.RATE_LIMIT_ENABLED,
            "virus_scanning": cls.VIRUS_SCANNING_ENABLED,
            "max_file_size_mb": cls.MAX_FILE_SIZE / (1024 * 1024),
            "allowed_file_types": cls.ALLOWED_FILE_TYPES,
            "cors_origins_count": len(cls.CORS_ORIGINS),
            "allowed_hosts_count": len(cls.ALLOWED_HOSTS),
            "security_headers_count": len(cls.SECURITY_HEADERS),
            "validation_errors": cls.validate_config()
        }

# Validate configuration on import
config_errors = SecurityConfig.validate_config()
if config_errors:
    import logging
    logger = logging.getLogger(__name__)
    for error in config_errors:
        logger.error(f"Security configuration error: {error}")
    
    # In production, fail fast on configuration errors
    if SecurityConfig.ENVIRONMENT == "production":
        raise ValueError(f"Security configuration errors: {config_errors}")