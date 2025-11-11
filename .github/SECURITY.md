# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please report it privately using one of the following methods:

### Option 1: GitHub Security Advisory (Preferred)

1. Go to the [Security tab](https://github.com/Lostenergydrink/styletts2-dataset-toolkit/security) in the repository
2. Click "Report a vulnerability"
3. Fill out the security advisory form

### Option 2: Email

If you prefer email, please contact the maintainers directly (contact information available in repository settings).

---

## What to Include

When reporting a security vulnerability, please include:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** of the vulnerability
- **Suggested fix** (if you have one)
- **Affected versions** (if known)

---

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity (see below)

---

## Severity Levels

### Critical
- **Impact**: Remote code execution, data breach, system compromise
- **Response**: Immediate attention, fix within 7 days

### High
- **Impact**: Significant security issue, privilege escalation
- **Response**: Priority attention, fix within 14 days

### Medium
- **Impact**: Moderate security issue, information disclosure
- **Response**: Standard attention, fix within 30 days

### Low
- **Impact**: Minor security issue, best practice violation
- **Response**: Normal attention, fix in next release

---

## Security Best Practices

### For Users

1. **Keep dependencies updated:**
   ```powershell
   pip install --upgrade -r requirements.txt
   ```

2. **Use virtual environments** to isolate dependencies

3. **Don't commit secrets** (API keys, passwords, etc.)

4. **Review code** before running scripts from untrusted sources

5. **Keep Python updated** to the latest supported version

### For Contributors

1. **Never commit secrets** (API keys, passwords, tokens)
2. **Review dependencies** before adding new packages
3. **Use environment variables** for sensitive configuration
4. **Validate user input** in scripts
5. **Follow secure coding practices**

---

## Known Security Considerations

### This Project

- **No network services** exposed by default
- **Local processing only** - no data sent to external servers
- **User-provided audio files** - ensure you have rights to process them
- **GPU access** - requires appropriate system permissions

### Dependencies

This project uses several third-party libraries. We rely on:
- **PyTorch** for GPU acceleration
- **Demucs** for audio separation
- **StyleTTS2** for text-to-speech
- **Gradio** for web interfaces

Please review the security policies of these dependencies:
- [PyTorch Security](https://pytorch.org/docs/stable/security.html)
- [Gradio Security](https://www.gradio.app/guides/security)

---

## Disclosure Policy

- Security vulnerabilities will be disclosed after a fix is available
- We will credit security researchers who responsibly disclose vulnerabilities
- Public disclosure will be coordinated with the reporter

---

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 1.0.1)
- Documented in release notes
- Tagged with security labels on GitHub

---

## Questions?

If you have questions about this security policy, please open a [GitHub Discussion](https://github.com/Lostenergydrink/styletts2-dataset-toolkit/discussions) (not an issue).

---

**Last Updated:** 2025-01-27








