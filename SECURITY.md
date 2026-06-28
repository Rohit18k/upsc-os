# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please do NOT open a public issue.

Instead, send a report to security@upscos.io.

Please include:

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Any potential mitigations

You can expect:

- Acknowledgment within 24 hours
- A detailed response within 72 hours
- Regular updates on remediation progress

## Disclosure Policy

We follow coordinated disclosure. Please allow us 90 days to address the issue before any public disclosure.

## Security Measures

- OWASP Top 10 protections enforced
- OWASP API Security Top 10 enforced
- Zero Trust Architecture
- All inputs validated and sanitized
- JWT with refresh token rotation
- RBAC enforced at every layer
- Row Level Security on database
- Structured audit logging
- Rate limiting on all endpoints
- CSP and secure headers configured
- Secrets never committed to repository
