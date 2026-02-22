# Security Rules: Frontend & Backend

## Security Principles

### 1. Security-First Mindset
- **Never Trust Input**: Validate and sanitize all user input
- **Least Privilege**: Grant minimum necessary permissions
- **Defense in Depth**: Multiple layers of security
- **Security by Design**: Build security into architecture, not as afterthought

### 2. OWASP Top 10 Awareness
- **Injection**: Prevent SQL injection, command injection
- **Broken Authentication**: Secure authentication mechanisms
- **Sensitive Data Exposure**: Protect sensitive data
- **XML External Entities (XXE)**: Prevent XXE attacks
- **Broken Access Control**: Implement proper authorization
- **Security Misconfiguration**: Secure configurations
- **XSS**: Prevent Cross-Site Scripting
- **Insecure Deserialization**: Secure data deserialization
- **Using Components with Known Vulnerabilities**: Keep dependencies updated
- **Insufficient Logging & Monitoring**: Log security events

## Authentication & Authorization

### 3. Authentication Rules
- **JWT Tokens**: Use JWT for stateless authentication
- **Token Expiration**: Set short expiration times (15-60 minutes)
- **Refresh Tokens**: Use refresh tokens for long-lived sessions
- **Password Hashing**: Use bcrypt/argon2, never store plain passwords
- **Rate Limiting**: Implement rate limiting on auth endpoints

```python
# Backend: JWT Authentication
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### 4. Authorization Rules
- **Role-Based Access Control (RBAC)**: Implement RBAC
- **Resource-Level Authorization**: Check permissions at resource level
- **Principle of Least Privilege**: Grant minimum necessary access
- **Explicit Deny**: Default to deny, explicitly allow

```python
# Backend: Authorization
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user

async def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.delete("/stocks/{symbol}")
async def delete_stock(
    symbol: str,
    current_user: User = Depends(require_admin)
):
    # Only admins can delete stocks
    pass
```

### 5. Frontend Authentication
```typescript
// Frontend: Token Storage
// ✅ Good: Use httpOnly cookies (server-side)
// ❌ Bad: localStorage (vulnerable to XSS)

// If using localStorage (less secure):
const token = localStorage.getItem('auth_token');

// Better: Use httpOnly cookies set by backend
// Or use secure session storage for temporary tokens
```

## Input Validation & Sanitization

### 6. Backend Validation
- **Pydantic Validation**: Validate all inputs with Pydantic
- **Type Checking**: Strict type checking
- **Length Limits**: Set appropriate length limits
- **Sanitization**: Sanitize inputs to prevent injection

```python
# Backend: Input Validation
from pydantic import BaseModel, Field, validator
import re

class StockCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, regex="^[A-Z]+$")
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0, le=1000000)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        # Additional validation
        if not re.match(r'^[A-Z]{1,5}$', v):
            raise ValueError('Invalid symbol format')
        return v.upper()
    
    @validator('name')
    def sanitize_name(cls, v):
        # Remove potentially dangerous characters
        return re.sub(r'[<>"\']', '', v)
```

### 7. Frontend Validation
```typescript
// Frontend: Input Validation
import { z } from 'zod';

const stockSchema = z.object({
  symbol: z.string()
    .min(1)
    .max(10)
    .regex(/^[A-Z]+$/, 'Symbol must be uppercase letters'),
  price: z.number()
    .positive('Price must be positive')
    .max(1000000, 'Price too high'),
});

// Validate before sending to API
const result = stockSchema.safeParse(formData);
if (!result.success) {
  // Show validation errors
  return;
}
```

### 8. SQL Injection Prevention
```python
# ✅ Good: Use parameterized queries (SQLAlchemy does this)
from sqlalchemy import select

result = await db.execute(
    select(Stock).where(Stock.symbol == symbol)  # Safe
)

# ❌ Bad: String concatenation (never do this)
query = f"SELECT * FROM stocks WHERE symbol = '{symbol}'"  # Vulnerable!
```

## Data Protection

### 9. Sensitive Data Handling
- **Never Log**: Never log passwords, tokens, or sensitive data
- **Encryption**: Encrypt sensitive data at rest
- **HTTPS Only**: Always use HTTPS in production
- **Data Masking**: Mask sensitive data in logs/responses

```python
# Backend: Data Masking
def mask_email(email: str) -> str:
    local, domain = email.split('@')
    return f"{local[0]}***@{domain}"

def mask_credit_card(card: str) -> str:
    return f"****-****-****-{card[-4:]}"
```

### 10. Environment Variables
- **Never Commit**: Never commit secrets to repository
- **Use .env**: Use environment variables for secrets
- **Separate Files**: Separate .env files for different environments
- **Validate**: Validate required environment variables at startup

```python
# Backend: Environment Variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    api_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## API Security

### 11. CORS Configuration
```python
# Backend: CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

### 12. Rate Limiting
```python
# Backend: Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/stocks")
@limiter.limit("10/minute")  # 10 requests per minute
async def create_stock(request: Request):
    pass
```

### 13. API Key Security
```python
# Backend: API Key Validation
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key
```

## XSS Prevention

### 14. Frontend XSS Prevention
- **React Escaping**: React automatically escapes content
- **DangerouslySetInnerHTML**: Avoid unless absolutely necessary
- **Content Security Policy**: Implement CSP headers
- **Sanitize**: Sanitize user-generated content

```typescript
// ✅ Good: React automatically escapes
<div>{userInput}</div>

// ❌ Bad: Dangerous
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ Good: If you must use dangerouslySetInnerHTML, sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

### 15. Content Security Policy
```typescript
// Next.js: CSP Headers
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
    `.replace(/\s{2,}/g, ' ').trim()
  }
];
```

## Dependency Security

### 16. Dependency Management
- **Regular Updates**: Regularly update dependencies
- **Security Audits**: Run security audits (`npm audit`, `pip-audit`)
- **Vulnerability Scanning**: Scan for known vulnerabilities
- **Minimal Dependencies**: Use minimal dependencies

```bash
# Frontend: Security Audit
npm audit
npm audit fix

# Backend: Security Audit
pip-audit
pip list --outdated
```

### 17. Dependency Pinning
```python
# Backend: requirements.txt
# Pin versions for security
fastapi==0.104.1
pydantic==2.5.0
sqlalchemy==2.0.23
```

```json
// Frontend: package.json
{
  "dependencies": {
    "react": "^18.2.0",  // Use ^ for minor updates only
    "next": "14.0.0"     // Pin major versions
  }
}
```

## Logging & Monitoring

### 18. Security Logging
- **Log Security Events**: Log authentication attempts, authorization failures
- **No Sensitive Data**: Never log passwords, tokens, or sensitive data
- **Structured Logging**: Use structured logging for security events
- **Alert on Anomalies**: Set up alerts for suspicious activity

```python
# Backend: Security Logging
import logging

security_logger = logging.getLogger("security")

def log_failed_login(username: str, ip_address: str):
    security_logger.warning(
        "Failed login attempt",
        extra={
            "event": "failed_login",
            "username": username,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## HTTPS & SSL/TLS

### 19. HTTPS Requirements
- **Always HTTPS**: Always use HTTPS in production
- **Redirect HTTP**: Redirect HTTP to HTTPS
- **HSTS**: Implement HTTP Strict Transport Security
- **Certificate Validation**: Validate SSL certificates

### 20. Security Headers
```python
# Backend: Security Headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["app.example.com", "*.example.com"]
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

## Key Rules Summary

1. **Never** trust user input - validate and sanitize
2. **Always** use HTTPS in production
3. **Never** commit secrets to repository
4. **Always** hash passwords (never store plain text)
5. **Implement** rate limiting on APIs
6. **Use** parameterized queries (prevent SQL injection)
7. **Keep** dependencies updated and audited
8. **Implement** proper authentication and authorization
9. **Log** security events (without sensitive data)
10. **Follow** principle of least privilege
