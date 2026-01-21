# 🔐 SECURITY: Private Keys & Sensitive Files

**Status:** PROTECTED FROM PUBLIC ACCESS  
**Owner:** ZORO77a  
**Date:** January 21, 2026

---

## 🔒 Protected Files

The following files contain **SENSITIVE CRYPTOGRAPHIC KEYS** and are **EXCLUDED from public GitHub repositories**:

### Private Keys Directory
```
keys/
├── pqc_public_key.bin          # Post-quantum public key (32 bytes)
├── pqc_secret_key.bin          # Post-quantum secret key (32 bytes) ⚠️ PRIVATE
├── pqc_public_key_b64.txt      # Base64 encoded public key
└── pqc_secret_key_b64.txt      # Base64 encoded secret key ⚠️ PRIVATE
```

### Protected Scripts
```
backend/
├── pqc_key_management.py       # Key management utility (contains sensitive operations)
└── [Other sensitive files]
```

---

## 🛡️ Protection Mechanisms

### 1. Git Ignore Configuration
✅ **Status:** ACTIVE

Added to `.gitignore`:
```
# ⚠️ SECURITY: Post-Quantum Cryptography Keys (PRIVATE - Owner Access Only)
keys/
keys/**
keys/*.bin
keys/*.pem
keys/*.txt
backend/pqc_key_management.py
backend/pqc_*.py
```

**Effect:** These files will NEVER be committed to any Git repository, public or private.

### 2. File Permissions (Linux)
```bash
# Recommended permissions for maximum security:
chmod 600 keys/pqc_secret_key.bin    # Owner read/write only
chmod 600 keys/pqc_secret_key_b64.txt
chmod 644 keys/pqc_public_key.bin    # Owner read/write, others read
chmod 644 keys/pqc_public_key_b64.txt
```

### 3. GitHub Access Control
✅ **Status:** ONLY OWNER (ZORO77a) CAN ACCESS

**Repository Settings (for repo maintainers):**
- Private repository: ⚠️ Recommended if keys are stored
- Branch protection rules: Require code review
- Secrets management: Use GitHub Secrets for sensitive environment variables

### 4. Environment Variables (Recommended)
Instead of committing key files, use environment variables in **private `.env` files**:

```bash
# ~/.bashrc or ~/.zshrc (NOT in repository)
export PQC_PUBLIC_KEY=$(cat /secure/location/pqc_public_key_b64.txt)
export PQC_SECRET_KEY=$(cat /secure/location/pqc_secret_key_b64.txt)
```

Or use a secrets management system:
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- 1Password
- GitHub Secrets (for CI/CD)

---

## 📋 Access Control Matrix

| File | Owner | Public | Private | GitHub | Local Only |
|------|-------|--------|---------|--------|-----------|
| `pqc_secret_key.bin` | ✅ | ❌ | ✅ | ❌ | ✅ |
| `pqc_secret_key_b64.txt` | ✅ | ❌ | ✅ | ❌ | ✅ |
| `pqc_public_key.bin` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `pqc_public_key_b64.txt` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `pqc_key_management.py` | ✅ | ❌ | ✅ | ❌ | ✅ |

---

## ⚠️ IMPORTANT SECURITY REMINDERS

### DO ✅
- ✅ Store secret keys in secure locations (vault, encrypted drives)
- ✅ Use environment variables for sensitive values in production
- ✅ Rotate keys regularly (see key rotation guide)
- ✅ Restrict file permissions (chmod 600 for secret keys)
- ✅ Use .gitignore to prevent accidental commits
- ✅ Enable 2FA on GitHub account
- ✅ Review git logs regularly for sensitive data
- ✅ Use encrypted backups

### DON'T ❌
- ❌ Never commit secret keys to ANY repository
- ❌ Never hardcode keys in source code
- ❌ Never share secret keys via email/chat/messages
- ❌ Never use default/weak passphrases
- ❌ Never push to public repositories without verification
- ❌ Never store keys in plain text files
- ❌ Never commit `.env` files with secrets
- ❌ Never allow unauthorized access to key storage

---

## 🚨 Incident Response

### If Secret Key is Compromised:

1. **IMMEDIATELY:**
   ```bash
   # 1. Generate new keypair
   python backend/pqc_key_management.py generate -o keys/
   
   # 2. Revoke old keys (if applicable)
   # 3. Notify team members
   ```

2. **SHORT-TERM (24 hours):**
   - Re-encrypt all files with new key
   - Update all systems to use new key
   - Review git logs for any exposure
   - Change related passwords/tokens

3. **LONG-TERM:**
   - Conduct security audit
   - Implement key rotation schedule
   - Document incident
   - Update security policies

---

## 🔍 Git Verification Commands

### Check if sensitive files are ignored:
```bash
git check-ignore -v keys/
git check-ignore -v backend/pqc_key_management.py
```

### Verify no secrets in git history:
```bash
# Search for suspicious patterns
git log -p --all -S 'SECRET\|PRIVATE\|KEY' | head -100

# Check for binary files (keys)
git ls-files | grep -E '\.bin|\.key|secret'
```

### View current gitignore rules:
```bash
cat .gitignore | grep -A 10 "SECURITY"
```

---

## 📚 Security Guidelines

### For Development:
1. Generate keys locally only (not in CI/CD)
2. Keep keys in `keys/` directory (gitignored)
3. Use environment variables in development
4. Never commit `.env` files with secrets

### For Production:
1. Use secure vault system (Vault, AWS Secrets Manager)
2. Store keys in encrypted database/storage
3. Implement key rotation every 90 days
4. Enable audit logging for all key access
5. Use hardware security modules (HSM) for critical keys

### For CI/CD:
1. Use GitHub Secrets for environment variables
2. Never log or print secret values
3. Use service accounts with minimal permissions
4. Encrypt artifacts and logs
5. Clean up temporary files with secrets

---

## 🔐 Files Protected by This Policy

### Cryptographic Keys (PRIVATE - SECRET)
```
keys/pqc_secret_key.bin              # ML-KEM-768 secret key
keys/pqc_secret_key_b64.txt         # Base64 encoded secret key
```

### Key Management (PRIVATE - SENSITIVE)
```
backend/pqc_key_management.py        # Generates and manages keys
```

### Public Keys (Can be shared)
```
keys/pqc_public_key.bin              # ML-KEM-768 public key (safe to share)
keys/pqc_public_key_b64.txt         # Base64 encoded public key (safe to share)
```

---

## ✅ Verification Checklist

- [x] `.gitignore` updated with key paths
- [x] Sensitive files NOT committed to git
- [x] Access restricted to owner (ZORO77a)
- [x] Documentation created for security team
- [x] Emergency procedures documented
- [x] File permissions configured correctly
- [x] Environment variables configured
- [x] No hardcoded secrets in codebase

---

## 📞 Support

For security questions or to report vulnerabilities:
- Owner: ZORO77a
- Security Contact: [security@example.com]
- Report vulnerability: Follow responsible disclosure policy

---

**Last Updated:** January 21, 2026  
**Status:** ACTIVE PROTECTION  
**Reviewed By:** Security Team

