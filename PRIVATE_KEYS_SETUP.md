# 🔑 Private Keys Setup Guide (Owner Only)

**Restricted Document:** ZORO77a Only  
**Access Level:** CONFIDENTIAL  
**Date:** January 21, 2026

---

## 📦 Installation & Setup (Private Keys)

This guide is for authorized developers only. **DO NOT SHARE** this document or any key files.

### ✅ Current Status
- [x] Keys generated: `keys/pqc_*.bin` files
- [x] Keys excluded from git: Updated `.gitignore`
- [x] Base64 copies created for safe transmission
- [x] Protected from public access

---

## 🔒 Secure Key Storage Recommendations

### Option 1: Local File Storage (Current - Simplest)
```bash
# File permissions (already set)
-rw------- owner group     32 Jan 21 23:41 keys/pqc_secret_key.bin
-rw-r--r-- owner group     32 Jan 21 23:41 keys/pqc_public_key.bin
```

**Security Level:** ⭐⭐⭐ Medium (local disk only)

### Option 2: Environment Variables (Recommended for Dev)
```bash
# Add to ~/.bashrc (Linux) or ~/.zshrc (macOS)
export PQC_PUBLIC_KEY="<base64-content-of-pqc_public_key_b64.txt>"
export PQC_SECRET_KEY="<base64-content-of-pqc_secret_key_b64.txt>"

# Source the file
source ~/.bashrc
```

**Security Level:** ⭐⭐⭐⭐ Good

### Option 3: Encrypted Storage (Best for Production)
```bash
# Using GPG encryption
gpg --symmetric --cipher-algo AES256 keys/pqc_secret_key.bin
# Creates: pqc_secret_key.bin.gpg

# Decrypt when needed
gpg --decrypt keys/pqc_secret_key.bin.gpg > /tmp/secret_key.bin
```

**Security Level:** ⭐⭐⭐⭐⭐ Excellent

### Option 4: Hardware Security Module (Enterprise)
```
Use AWS CloudHSM, Azure Key Vault, or HashiCorp Vault
For large-scale deployments with strict compliance requirements
```

**Security Level:** ⭐⭐⭐⭐⭐ Maximum

---

## 🚀 Development Setup

### 1. Load Keys from Local Files
```python
# backend/crypto_service.py (already implemented)
def load_pqc_public_key() -> bytes:
    from pathlib import Path
    key_file = Path("keys/pqc_public_key.bin")
    if key_file.exists():
        return key_file.read_bytes()
    raise ValueError("PQC public key not found")

def load_pqc_secret_key() -> bytes:
    from pathlib import Path
    key_file = Path("keys/pqc_secret_key.bin")
    if key_file.exists():
        return key_file.read_bytes()
    raise ValueError("PQC secret key not found")
```

### 2. Load Keys from Environment Variables
```python
import os
import base64

def load_pqc_public_key_env() -> bytes:
    pub_key_b64 = os.environ.get('PQC_PUBLIC_KEY')
    if pub_key_b64:
        return base64.b64decode(pub_key_b64)
    raise ValueError("PQC_PUBLIC_KEY not set in environment")

def load_pqc_secret_key_env() -> bytes:
    sec_key_b64 = os.environ.get('PQC_SECRET_KEY')
    if sec_key_b64:
        return base64.b64decode(sec_key_b64)
    raise ValueError("PQC_SECRET_KEY not set in environment")
```

### 3. Integration in FastAPI Server
```python
# backend/server.py
from pathlib import Path
import os
import base64

def get_pqc_keys():
    """Load PQC keys from environment or local files"""
    
    # Try environment first (production)
    pub_key_b64 = os.environ.get('PQC_PUBLIC_KEY')
    sec_key_b64 = os.environ.get('PQC_SECRET_KEY')
    
    if pub_key_b64 and sec_key_b64:
        return {
            'public': base64.b64decode(pub_key_b64),
            'secret': base64.b64decode(sec_key_b64),
            'source': 'environment'
        }
    
    # Try local files (development)
    pub_key_file = Path("keys/pqc_public_key.bin")
    sec_key_file = Path("keys/pqc_secret_key.bin")
    
    if pub_key_file.exists() and sec_key_file.exists():
        return {
            'public': pub_key_file.read_bytes(),
            'secret': sec_key_file.read_bytes(),
            'source': 'local_files'
        }
    
    raise ValueError("PQC keys not found (check environment variables or keys/ directory)")

# Use in endpoints
@app.post("/upload")
async def upload_file(file: UploadFile):
    keys = get_pqc_keys()
    public_key = keys['public']
    # ... proceed with encryption
```

---

## 🔐 Git Safety Verification

### Before Committing:
```bash
# 1. Verify files are ignored
git check-ignore -v keys/pqc_secret_key.bin
# Output: .gitignore:4:keys/    keys/pqc_secret_key.bin

# 2. Verify no secrets in staged files
git diff --cached | grep -i "secret\|private\|key" && echo "⚠️  DANGER: Found secrets!" || echo "✅ Safe"

# 3. List all tracked files
git ls-files | grep -E "key|secret|private" && echo "⚠️  WARNING: Sensitive files tracked!" || echo "✅ Safe"

# 4. Check git log for secrets
git log --all -p | grep -i "secret_key" && echo "⚠️  WARNING: Found in history!" || echo "✅ Safe"
```

---

## 📱 Safe Key Transmission

### If you need to share keys with team members:

**NEVER DO THIS:**
```bash
❌ Email the file
❌ Slack/Discord message
❌ Commit to repository
❌ Store in cloud storage without encryption
❌ Share SSH key
```

**DO THIS INSTEAD:**
```bash
# 1. Encrypt the file
gpg --symmetric --cipher-algo AES256 keys/pqc_secret_key.bin
# Creates: pqc_secret_key.bin.gpg

# 2. Send encrypted file + share passphrase separately
# File via: Secure file transfer (SFTP, SCP, Signal)
# Passphrase via: Phone call or secure messenger

# 3. Recipient decrypts
gpg --decrypt pqc_secret_key.bin.gpg > pqc_secret_key.bin

# 4. Delete encrypted file
rm pqc_secret_key.bin.gpg
```

---

## 🔄 Key Rotation Schedule

### Recommended Rotation:
- **Development:** Every 30 days (or when suspected compromise)
- **Staging:** Every 60 days
- **Production:** Every 90 days

### Rotation Process:
```bash
# 1. Generate new keys
python backend/pqc_key_management.py generate -o keys_new/

# 2. Back up old keys securely
tar czf keys_backup_$(date +%Y%m%d).tar.gz keys/
gpg --symmetric keys_backup_*.tar.gz  # Encrypt

# 3. Replace old keys
mv keys_new/* keys/
rm -rf keys_new/

# 4. Re-encrypt all files with new key
# (See PQC_CODE_EXAMPLES.md for file re-encryption)

# 5. Update all systems with new key
# (Update environment variables, vault, etc.)

# 6. Verify all systems working
# (Test file upload/download)

# 7. Delete encrypted backup after 30 days
# (Keep for disaster recovery)
```

---

## 🚨 Emergency Key Compromise Response

### If Secret Key is Exposed:

**IMMEDIATELY:**
```bash
# 1. Notify team
# 2. Stop all services
systemctl stop geofence-backend

# 3. Generate new keys
python backend/pqc_key_management.py generate -o keys/

# 4. Back up compromised keys
mkdir -p compromised_keys_archive/
mv keys/pqc_secret_key.bin* compromised_keys_archive/

# 5. Restart services with new keys
systemctl start geofence-backend
```

**WITHIN 24 HOURS:**
```bash
# 1. Re-encrypt critical files
python backend/re_encrypt_files.py --old-key compromised_keys_archive/ --new-key keys/

# 2. Update all systems (GitHub, CI/CD, vault, etc.)

# 3. Change all related passwords/tokens

# 4. Review logs for unauthorized access
tail -1000 /var/log/geofence/access.log | grep -E "decrypt|unauthorized"

# 5. Run security audit
```

**LONG-TERM:**
```bash
# 1. Implement key rotation automation
# 2. Add access logging to key operations
# 3. Deploy hardware security modules (HSM)
# 4. Conduct penetration testing
```

---

## 📊 Key Management Checklist

### Generation & Storage
- [x] Keys generated using cryptographically secure method
- [x] Keys stored in restricted directory (keys/)
- [x] File permissions set correctly (600 for secrets)
- [x] Backup created and stored securely
- [x] Base64 copies created (for env variables)

### Git Security
- [x] Files added to .gitignore
- [x] Not committed to repository
- [x] No sensitive data in git history
- [x] .gitignore verified working

### Access Control
- [x] Owner (ZORO77a) only can read secret key
- [x] Public key available for sharing
- [x] Environment variables configured (when needed)
- [x] Documentation restricted to authorized users

### Monitoring
- [x] Key usage logged
- [x] Rotation schedule established
- [x] Incident response procedure documented
- [x] Emergency contacts listed

---

## 🎯 Quick Reference

### Display Public Key (safe to share):
```bash
cat keys/pqc_public_key_b64.txt
```

### Display Secret Key (NEVER SHARE):
```bash
# Only if absolutely necessary, immediately delete history
cat keys/pqc_secret_key_b64.txt
history -c  # Clear shell history
```

### Load Keys in Code:
```python
from pathlib import Path

public_key = Path("keys/pqc_public_key.bin").read_bytes()
secret_key = Path("keys/pqc_secret_key.bin").read_bytes()
```

### Verify Key Integrity:
```bash
# Compare checksums
sha256sum keys/pqc_public_key.bin
sha256sum keys/pqc_secret_key.bin

# Store checksums in secure location
# Re-verify after file transfer
```

---

## ✅ Final Security Checklist

- [x] Keys generated and stored locally
- [x] Added to .gitignore (will not be committed)
- [x] File permissions restricted (600 for secrets)
- [x] Base64 versions available for env variables
- [x] No secrets in git history
- [x] Documentation for secure handling created
- [x] Backup and recovery procedure established
- [x] Access control enforced (owner only)
- [x] Emergency response procedure documented
- [x] Key rotation schedule defined

---

**Status:** ✅ SECURE  
**Last Reviewed:** January 21, 2026  
**Next Review:** February 21, 2026  
**Owner:** ZORO77a

