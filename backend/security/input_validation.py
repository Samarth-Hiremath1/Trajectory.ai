"""
Input validation and sanitization utilities for security
"""
import re
import html
import uuid
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator
import bleach
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputSanitizer:
    """Utility class for input sanitization"""
    
    # Allowed HTML tags for rich text content (very restrictive)
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    # Common patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")
        
        # Trim whitespace
        value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Input too long. Maximum {max_length} characters allowed")
        
        if allow_html:
            # Clean HTML with bleach
            value = bleach.clean(
                value,
                tags=InputSanitizer.ALLOWED_TAGS,
                attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
                strip=True
            )
        else:
            # Escape HTML entities
            value = html.escape(value)
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address"""
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")
        
        email = email.strip().lower()
        
        if not InputSanitizer.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address too long")
        
        return email
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> str:
        """Validate UUID format"""
        if not isinstance(uuid_str, str):
            raise ValidationError("UUID must be a string")
        
        uuid_str = uuid_str.strip()
        
        if not InputSanitizer.UUID_PATTERN.match(uuid_str):
            raise ValidationError("Invalid UUID format")
        
        return uuid_str
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize filename"""
        if not isinstance(filename, str):
            raise ValidationError("Filename must be a string")
        
        filename = filename.strip()
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError("Invalid filename: path traversal detected")
        
        # Check for null bytes
        if '\x00' in filename:
            raise ValidationError("Invalid filename: null byte detected")
        
        # Check length
        if len(filename) > 255:
            raise ValidationError("Filename too long")
        
        # Check for empty filename
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        return filename
    
    @staticmethod
    def validate_url(url: str, allowed_schemes: List[str] = ['http', 'https']) -> str:
        """Validate URL format and scheme"""
        if not isinstance(url, str):
            raise ValidationError("URL must be a string")
        
        url = url.strip()
        
        try:
            parsed = urlparse(url)
            if parsed.scheme not in allowed_schemes:
                raise ValidationError(f"URL scheme must be one of: {allowed_schemes}")
            
            if not parsed.netloc:
                raise ValidationError("Invalid URL: missing domain")
            
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {str(e)}")
        
        return url
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_depth: int = 5, current_depth: int = 0) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            
        Returns:
            Sanitized dictionary
        """
        if current_depth > max_depth:
            raise ValidationError("Dictionary nesting too deep")
        
        if not isinstance(data, dict):
            raise ValidationError("Input must be a dictionary")
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            if not isinstance(key, str):
                raise ValidationError("Dictionary keys must be strings")
            
            key = InputSanitizer.sanitize_string(key, max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = InputSanitizer.sanitize_dict(value, max_depth, current_depth + 1)
            elif isinstance(value, list):
                sanitized[key] = InputSanitizer.sanitize_list(value, max_depth, current_depth + 1)
            elif isinstance(value, (int, float, bool)) or value is None:
                sanitized[key] = value
            else:
                # Convert other types to string and sanitize
                sanitized[key] = InputSanitizer.sanitize_string(str(value))
        
        return sanitized
    
    @staticmethod
    def sanitize_list(data: List[Any], max_depth: int = 5, current_depth: int = 0) -> List[Any]:
        """
        Recursively sanitize list values
        
        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            
        Returns:
            Sanitized list
        """
        if current_depth > max_depth:
            raise ValidationError("List nesting too deep")
        
        if not isinstance(data, list):
            raise ValidationError("Input must be a list")
        
        if len(data) > 1000:  # Prevent DoS attacks
            raise ValidationError("List too long")
        
        sanitized = []
        
        for value in data:
            if isinstance(value, str):
                sanitized.append(InputSanitizer.sanitize_string(value))
            elif isinstance(value, dict):
                sanitized.append(InputSanitizer.sanitize_dict(value, max_depth, current_depth + 1))
            elif isinstance(value, list):
                sanitized.append(InputSanitizer.sanitize_list(value, max_depth, current_depth + 1))
            elif isinstance(value, (int, float, bool)) or value is None:
                sanitized.append(value)
            else:
                # Convert other types to string and sanitize
                sanitized.append(InputSanitizer.sanitize_string(str(value)))
        
        return sanitized

class SecureBaseModel(BaseModel):
    """Base model with built-in input validation and sanitization"""
    
    class Config:
        # Validate assignment to prevent injection after creation
        validate_assignment = True
        # Use enum values instead of names
        use_enum_values = True
        # Forbid extra fields to prevent injection
        extra = "forbid"
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Automatically sanitize string fields"""
        if isinstance(v, str):
            return InputSanitizer.sanitize_string(v)
        return v

class FileUploadValidator:
    """Validator for file uploads"""
    
    # Allowed file types and their magic numbers
    ALLOWED_MIME_TYPES = {
        'application/pdf': [b'%PDF'],
        'text/plain': [b''],  # Text files don't have consistent magic numbers
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_content(content: bytes, filename: str, content_type: str) -> None:
        """
        Validate file content for security
        
        Args:
            content: File content as bytes
            filename: Original filename
            content_type: MIME type
            
        Raises:
            ValidationError: If validation fails
        """
        # Check file size
        if len(content) > FileUploadValidator.MAX_FILE_SIZE:
            raise ValidationError(f"File too large. Maximum size: {FileUploadValidator.MAX_FILE_SIZE} bytes")
        
        # Check if content type is allowed
        if content_type not in FileUploadValidator.ALLOWED_MIME_TYPES:
            raise ValidationError(f"File type not allowed: {content_type}")
        
        # Validate filename
        InputSanitizer.validate_filename(filename)
        
        # Check file extension matches content type
        if content_type == 'application/pdf' and not filename.lower().endswith('.pdf'):
            raise ValidationError("File extension doesn't match content type")
        
        # Check magic numbers for PDF files
        if content_type == 'application/pdf':
            magic_numbers = FileUploadValidator.ALLOWED_MIME_TYPES[content_type]
            if not any(content.startswith(magic) for magic in magic_numbers):
                raise ValidationError("File content doesn't match declared type")
        
        # Check for embedded scripts or malicious content
        FileUploadValidator._scan_for_malicious_content(content, content_type)
    
    @staticmethod
    def _scan_for_malicious_content(content: bytes, content_type: str) -> None:
        """
        Scan file content for potentially malicious patterns
        
        Args:
            content: File content as bytes
            content_type: MIME type
            
        Raises:
            ValidationError: If malicious content is detected
        """
        # Convert to string for pattern matching (ignore decode errors)
        try:
            content_str = content.decode('utf-8', errors='ignore').lower()
        except:
            content_str = str(content).lower()
        
        # Suspicious patterns that might indicate malicious content
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'eval(',
            b'document.cookie',
            b'window.location',
            b'/launch',
            b'/action',
            b'cmd.exe',
            b'powershell',
            b'bash',
            b'/bin/sh',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in content:
                logger.warning(f"Suspicious pattern detected in uploaded file: {pattern}")
                raise ValidationError("File contains potentially malicious content")

def validate_user_id(user_id: str) -> str:
    """Validate user ID format"""
    if not user_id:
        raise ValidationError("User ID is required")
    
    # Try to validate as UUID first
    try:
        return InputSanitizer.validate_uuid(user_id)
    except ValidationError:
        # If not UUID, sanitize as string
        return InputSanitizer.sanitize_string(user_id, max_length=100)

def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize request data"""
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a dictionary")
    
    return InputSanitizer.sanitize_dict(data)