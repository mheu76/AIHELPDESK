# Security Policy

## 🔒 Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## 🚨 Reporting a Vulnerability

We take the security of IT AI Helpdesk seriously. If you have discovered a security vulnerability, please follow these steps:

### 📧 How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities by emailing:

**security@example.com** (replace with your actual security contact)

### 📋 What to Include

Your report should include:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** of the vulnerability
4. **Suggested fix** (if you have one)
5. **Your contact information** for follow-up

### 🔄 Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity (see below)

### 🎯 Severity Levels

| Level    | Response Time | Description                                    |
|----------|--------------|------------------------------------------------|
| Critical | 24-48 hours  | Remote code execution, SQL injection, etc.     |
| High     | 3-7 days     | Privilege escalation, authentication bypass    |
| Medium   | 7-14 days    | XSS, CSRF, information disclosure              |
| Low      | 14-30 days   | Non-critical security improvements             |

## ⚠️ Known Security Considerations

### 🔐 Password Hashing (CRITICAL)

**Current Status**: Version 1.0.0 uses SHA-256 for password hashing.

⚠️ **This is NOT production-safe!**

**Before Production Deployment**:
- Replace `backend/app/core/security.py` password hashing with:
  - **bcrypt** (recommended), or
  - **argon2** (also recommended)

**Timeline**: Must be fixed before production deployment.

### 🔑 Secret Management

**Best Practices**:

1. **Never commit secrets** to version control
   - API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY)
   - JWT_SECRET_KEY
   - Database passwords
   - Any production credentials

2. **Use environment variables** for secrets
   - Development: `.env.docker` (local only)
   - Production: `.env.production` (secure storage)

3. **Rotate secrets regularly**
   - JWT_SECRET_KEY: Every 90 days
   - API keys: As recommended by provider
   - Database passwords: Every 90 days

4. **Generate strong secrets**
   ```bash
   # Generate JWT secret
   openssl rand -hex 32
   ```

### 🌐 CORS Configuration

**Production Checklist**:

- [ ] Set `ALLOWED_ORIGINS` to specific domains only
- [ ] Never use `["*"]` in production
- [ ] Verify `FRONTEND_URL` matches your actual frontend domain
- [ ] Enable credentials only when necessary

Example:
```env
ALLOWED_ORIGINS=["https://helpdesk.yourdomain.com"]
FRONTEND_URL=https://helpdesk.yourdomain.com
```

### 🔒 JWT Token Security

**Current Configuration**:
- Access Token: 480 minutes (8 hours)
- Refresh Token: 7 days
- Algorithm: HS256

**Best Practices**:

1. **Secure Storage**:
   - Use `httpOnly` cookies for tokens (recommended)
   - If using localStorage, be aware of XSS risks

2. **Token Rotation**:
   - Implement token refresh before expiration
   - Invalidate refresh tokens on logout

3. **Token Validation**:
   - Verify token signature
   - Check expiration
   - Validate user permissions

### 🗄️ Database Security

**Production Checklist**:

- [ ] Use strong database passwords (16+ characters, mixed case, symbols)
- [ ] Enable SSL/TLS for database connections
- [ ] Restrict database access by IP (whitelist only)
- [ ] Use managed database service with automatic backups
- [ ] Implement database encryption at rest
- [ ] Regular security updates for PostgreSQL

**Connection String Security**:
```env
# Bad (no SSL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Good (with SSL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

### 🔐 Input Validation

**Current Protections**:
- Pydantic validation for all API inputs
- SQLAlchemy ORM (prevents SQL injection)
- FastAPI automatic validation

**Best Practices**:
- Never trust user input
- Validate on both client and server
- Sanitize output to prevent XSS
- Use parameterized queries (ORM handles this)

### 🚪 Authentication & Authorization

**Security Measures**:

1. **Password Requirements** (enforce in production):
   - Minimum 8 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Password strength validation

2. **Rate Limiting** (implement before production):
   - Login attempts: 5 per 15 minutes per IP
   - API requests: 100 per minute per user
   - Use nginx or application-level rate limiting

3. **Account Lockout** (implement before production):
   - Lock account after 5 failed login attempts
   - Require email verification to unlock

### 📝 Logging & Monitoring

**Security Logging**:

- Log all authentication attempts
- Log authorization failures
- Log sensitive data access
- **Never log passwords or tokens**
- Use structured logging (JSON in production)

**Monitoring**:
- Set up alerts for:
  - Repeated failed login attempts
  - Unusual API activity
  - Error rate spikes
  - Database connection failures

### 🌐 Production Deployment Security

**Infrastructure**:

- [ ] Enable firewall (allow only 80, 443, SSH)
- [ ] Disable root login via SSH
- [ ] Use SSH keys instead of passwords
- [ ] Keep system packages updated
- [ ] Use non-root user for application
- [ ] Enable automatic security updates

**SSL/TLS**:

- [ ] Use Let's Encrypt or commercial certificate
- [ ] Enable HTTPS only (redirect HTTP to HTTPS)
- [ ] Use TLS 1.2+ (disable older versions)
- [ ] Configure strong cipher suites
- [ ] Enable HSTS header

**Docker Security**:

- [ ] Use non-root user in containers
- [ ] Scan images for vulnerabilities
- [ ] Keep base images updated
- [ ] Use minimal base images (alpine)
- [ ] Don't include development dependencies in production

## 🛡️ Security Headers

**Recommended Headers** (configure in Nginx):

```nginx
# Security Headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

## 🔍 Security Audit Checklist

Before production deployment, verify:

### Application Level
- [ ] Password hashing replaced with bcrypt/argon2
- [ ] All secrets moved to environment variables
- [ ] CORS configured for production domains only
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] Output sanitization to prevent XSS
- [ ] SQL injection protection verified
- [ ] CSRF protection enabled (for cookie-based auth)

### Infrastructure Level
- [ ] HTTPS/TLS configured and enforced
- [ ] Firewall rules configured
- [ ] SSH hardened (keys only, no root)
- [ ] Database access restricted by IP
- [ ] Automated backups configured
- [ ] Monitoring and alerting set up
- [ ] Log rotation configured
- [ ] Security updates automated

### Operational Level
- [ ] Incident response plan documented
- [ ] Security contact information published
- [ ] Regular security reviews scheduled
- [ ] Dependency vulnerability scanning automated
- [ ] Penetration testing completed

## 📚 Resources

### Security Best Practices

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Security](https://nextjs.org/docs/app/building-your-application/configuring/security-headers)

### Security Tools

- **Dependency Scanning**: 
  - [Safety](https://pyup.io/safety/) (Python)
  - [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit) (Node.js)
- **Container Scanning**: 
  - [Trivy](https://github.com/aquasecurity/trivy)
  - [Snyk](https://snyk.io/)
- **SAST**: 
  - [Bandit](https://github.com/PyCQA/bandit) (Python)
  - [ESLint Security](https://github.com/nodesecurity/eslint-plugin-security) (JavaScript)

## 📞 Contact

For security concerns, contact:
- **Email**: security@example.com (replace with your email)
- **PGP Key**: Available at [keybase.io/yourname]

---

**Last Updated**: 2026-04-06
