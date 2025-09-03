# Security Implementation Guide

This document outlines the comprehensive security measures implemented in the Trajectory.AI backend.

## Overview

The security implementation includes:
- Row Level Security (RLS) policies in Supabase
- Input validation and sanitization
- Rate limiting and DDoS protection
- Secure file upload with virus scanning
- Authentication and authorization
- Security headers and CORS configuration

## Security Features

### 1. Row Level Security (RLS)

**Location**: `backend/security/rls_policies.sql`

RLS policies ensure users can only access their own data:
- Users can only view/modify their own profiles, resumes, roadmaps, etc.
- Storage bucket policies restrict file access to file owners
- All database tables have appropriate RLS policies enabled

**Setup**:
```bash
# Apply RLS policies in Supabase SQL Editor
cat backend/security/rls_policies.sql
```

### 2. Input Validation and Sanitization

**Location**: `backend/security/input_validation.py`

Features:
- HTML sanitization using bleach
- String length validation
- Email format validation
- UUID format validation
- Filename validation (prevents path traversal)
- URL validation with allowed schemes
- Recursive dictionary/list sanitization
- Custom validation errors

**Usage**:
```python
from security.input_validation import InputSanitizer, validate_user_id

# Sanitize user input
clean_text = InputSanitizer.sanitize_string(user_input)
user_id = validate_user_id(raw_user_id)
```

### 3. Rate Limiting

**Location**: `backend/security/rate_limiting.py`

Features:
- Sliding window rate limiting
- Redis-backed with local fallback
- Different limits for different endpoints
- Burst protection
- Rate limit headers in responses

**Configuration**:
- Global: 1000 requests/hour, 100 requests/minute
- Auth: 10 requests/5min, 5 requests/minute
- Upload: 5 requests/5min, 2 requests/minute
- AI Chat: 50 requests/hour, 10 requests/minute
- Roadmap: 10 requests/hour, 3 requests/minute

### 4. Secure File Upload

**Location**: `backend/security/file_security.py`

Features:
- File type validation using python-magic
- Virus scanning with ClamAV and YARA rules
- Content analysis for malicious patterns
- File size limits
- Temporary file handling
- Hash-based deduplication

**Supported Scanners**:
- ClamAV (if installed)
- YARA rules for malware detection
- Content pattern analysis
- File type validation

### 5. Authentication and Authorization

**Location**: `backend/security/auth.py`

Features:
- Supabase JWT token validation
- Role-based access control
- Resource ownership verification
- Permission decorators
- User context management

**Usage**:
```python
from security.auth import get_current_user_id, require_permission

@require_permission("resume", "write")
async def update_resume(user_id: str = Depends(get_current_user_id)):
    # Function implementation
```

### 6. Security Headers and CORS

**Location**: `backend/main.py`

Security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` with strict rules
- `Strict-Transport-Security` (production only)

CORS configuration:
- Restricted origins based on environment
- Limited allowed headers
- Credentials support for authenticated requests

## Environment Variables

### Required Variables

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Security Configuration
ENVIRONMENT=development|production
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
ALLOWED_HOSTS=localhost,127.0.0.1,*.vercel.app
```

### Optional Variables

```bash
# Rate Limiting
REDIS_URL=redis://localhost:6379
RATE_LIMIT_ENABLED=true

# File Upload
MAX_FILE_SIZE=10485760  # 10MB in bytes
VIRUS_SCANNING_ENABLED=true

# Security
DEBUG=false
LOG_SECURITY_EVENTS=true
LOG_LEVEL=INFO
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Security Setup

```bash
python backend/setup_security.py
```

This script will:
- Check environment variables
- Verify security dependencies
- Test Supabase connection
- Display RLS policies to apply
- Show security configuration summary

### 3. Apply RLS Policies

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy the SQL from `backend/security/rls_policies.sql`
4. Execute the queries

### 4. Optional: Install ClamAV

For enhanced virus scanning:

```bash
# Ubuntu/Debian
sudo apt-get install clamav clamav-daemon

# macOS
brew install clamav

# Update virus definitions
sudo freshclam
```

### 5. Optional: Set up Redis

For distributed rate limiting:

```bash
# Install Redis
# Ubuntu/Debian: sudo apt-get install redis-server
# macOS: brew install redis

# Set REDIS_URL environment variable
export REDIS_URL=redis://localhost:6379
```

## Security Testing

### 1. Input Validation Tests

```python
# Test malicious input
malicious_inputs = [
    "<script>alert('xss')</script>",
    "'; DROP TABLE users; --",
    "../../../etc/passwd",
    "\x00malicious"
]

for input_data in malicious_inputs:
    try:
        clean_data = InputSanitizer.sanitize_string(input_data)
        print(f"Sanitized: {clean_data}")
    except ValidationError as e:
        print(f"Blocked: {e}")
```

### 2. Rate Limiting Tests

```bash
# Test rate limiting with curl
for i in {1..20}; do
    curl -H "Authorization: Bearer $TOKEN" \
         http://localhost:8000/api/profile/test-user
done
```

### 3. File Upload Tests

```python
# Test malicious file upload
malicious_files = [
    ("virus.exe", b"MZ\x90\x00..."),  # Executable
    ("script.pdf", b"%PDF<script>"),   # PDF with script
    ("large.pdf", b"A" * (50 * 1024 * 1024))  # Too large
]

for filename, content in malicious_files:
    result = await secure_file_handler.process_upload(
        content, filename, "application/pdf", "test-user"
    )
    print(f"{filename}: {'BLOCKED' if not result['success'] else 'ALLOWED'}")
```

## Monitoring and Alerting

### Security Events to Monitor

1. **Authentication Failures**
   - Failed login attempts
   - Invalid JWT tokens
   - Suspicious user behavior

2. **Rate Limiting Triggers**
   - Clients hitting rate limits
   - Unusual traffic patterns
   - Potential DDoS attacks

3. **File Upload Security**
   - Virus detection events
   - Malicious file attempts
   - Large file uploads

4. **Input Validation Failures**
   - XSS attempts
   - SQL injection attempts
   - Path traversal attempts

### Log Analysis

Security events are logged with structured data:

```python
logger.warning(f"Security event: {event_type}", extra={
    "client_ip": client_ip,
    "user_id": user_id,
    "event_type": event_type,
    "details": event_details
})
```

## Security Best Practices

### 1. Regular Updates
- Keep dependencies updated
- Monitor security advisories
- Update virus definitions

### 2. Environment Security
- Use strong, unique passwords
- Rotate API keys regularly
- Secure environment variables

### 3. Network Security
- Use HTTPS in production
- Configure firewalls properly
- Monitor network traffic

### 4. Data Protection
- Encrypt sensitive data
- Implement data retention policies
- Regular security audits

### 5. Incident Response
- Have incident response plan
- Monitor security logs
- Regular security testing

## Troubleshooting

### Common Issues

1. **RLS Policies Not Working**
   - Verify policies are applied in Supabase
   - Check user authentication
   - Ensure correct user_id format

2. **Rate Limiting Too Strict**
   - Adjust limits in `rate_limiting.py`
   - Check Redis connection
   - Verify client identification

3. **File Upload Blocked**
   - Check file type and size
   - Verify virus scanner setup
   - Review security logs

4. **CORS Issues**
   - Verify CORS_ORIGINS setting
   - Check request headers
   - Ensure proper authentication

### Debug Mode

For debugging security issues:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python backend/main.py
```

## Security Compliance

This implementation addresses:
- **OWASP Top 10** security risks
- **Data protection** requirements
- **Input validation** best practices
- **Authentication** security standards
- **File upload** security guidelines

## Contact

For security issues or questions:
- Review this documentation
- Check security logs
- Run security setup script
- Test security measures thoroughly