# Security Policy

## Supported Versions

We actively support the latest minor version of easylimit. Security updates are provided for:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

As the project is currently in pre-1.0 development, we recommend always using the latest release from PyPI.

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in easylimit, please follow these steps:

### Please DO NOT:
- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before we've had a chance to address it

### Please DO:
1. **Email us privately** at opensource@man8.com
2. **Include details:**
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact and attack scenarios
   - Affected versions
   - Suggested fix (if you have one)

### What to Expect:
- **Acknowledgment:** We'll respond within 48 hours
- **Assessment:** We'll evaluate the severity and impact
- **Updates:** We'll keep you informed of our progress
- **Credit:** We'll credit you in the security advisory (unless you prefer to remain anonymous)
- **Timeline:** We aim to release fixes within:
  - Critical vulnerabilities: 7 days
  - High severity: 30 days
  - Medium/Low severity: 90 days

## Security Update Process

When a security issue is confirmed:

1. We'll develop and test a fix in a private branch
2. We'll prepare a security advisory with CVSS scoring
3. We'll release a patched version to PyPI
4. We'll publish the GitHub Security Advisory with credit to the reporter
5. We'll notify users through GitHub releases and issue notifications

## Security Considerations for easylimit

### Thread Safety
easylimit is designed to be thread-safe and uses `threading.RLock()` to protect all state access. However:
- Ensure you're using the same `RateLimiter` instance across threads (not creating new instances)
- When using async methods, ensure proper event loop management

### Dependency Security
easylimit has **zero runtime dependencies**, minimizing supply chain attack surface. All imports are from Python's standard library.

### Input Validation
While easylimit performs input validation on constructor parameters, users should:
- Avoid passing untrusted user input directly to `RateLimiter()` constructor
- Validate rate limits are within reasonable bounds for your use case
- Be aware that extremely small `period` values or large `limit` values could cause performance issues

## Security Best Practices for Users

- **Keep updated:** Always use the latest version from PyPI: `pip install --upgrade easylimit`
- **Monitor advisories:** Watch the [GitHub repository](https://github.com/man8/easylimit) for security advisories
- **Report issues:** If you notice any suspicious behavior, report it immediately
- **Review dependencies:** While easylimit has no runtime dependencies, audit your full dependency tree
- **Use virtual environments:** Isolate easylimit and your application dependencies

## Scope

This security policy covers:
- The easylimit Python package distributed via PyPI
- The source code in the official GitHub repository

This policy does NOT cover:
- Third-party forks or modified versions
- Security issues in dependencies of your application (not easylimit itself)
- Issues in Python itself or the Python standard library

Thank you for helping keep easylimit and its users safe!
