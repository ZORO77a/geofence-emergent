# Post-Quantum Cryptography Integration Guide

## Quick Start

### 1. Install Post-Quantum Library
```bash
# Install liboqs with Python bindings
pip install liboqs-python==0.9.1

# Verify installation
python -c "import liboqs; print('✓ liboqs installed')"
```

### 2. Generate Keypair
```bash
cd backend
python pqc_key_management.py generate -o keys/
```

This creates:
- `keys/pqc_public_key.bin` - Public key for encryption (safe to share)
- `keys/pqc_secret_key.bin` - Secret key for decryption (KEEP SECURE!)
- `keys/pqc_public_key_b64.txt` - Base64 encoded public key for database storage
- `keys/pqc_secret_key_b64.txt` - Base64 encoded secret key for database storage

### 3. Test Encryption
```bash
# Test with built-in test message
python pqc_key_management.py test keys/pqc_public_key.bin keys/pqc_secret_key.bin

# Test with actual file
python pqc_key_management.py test keys/pqc_public_key.bin keys/pqc_secret_key.bin -f document.pdf
```

### 4. View Cryptographic Info
```bash
python pqc_key_management.py info
```

Expected output:
```
📋 Cryptographic Configuration:

  Pqc Available: True
  Pqc Algorithm: ML-KEM-768
  Symmetric Encryption: AES-256-GCM
  Mode: Hybrid (PQC key exchange + AES symmetric)
  Aes Key Size: 256 bits
  Nonce Size: 128 bits
  Tag Size: 128 bits
  Kdf: PBKDF2 with 100,000 iterations

✅ Post-Quantum Cryptography is AVAILABLE and ACTIVE
```

## Integration with Existing Code

### Current File Upload (Classical AES)
```python
# Old method - still works
file_meta = {
    "file_id": new_file_id,
    "filename": file.filename,
    "uploaded_by": current_user["username"],
    "uploaded_at": datetime.now(timezone.utc).isoformat(),
    "encrypted": True,
    "size": len(file_data),
    "encryption_key": crypto_service.key_to_string(key)  # Stored key
}
encrypted_data = crypto_service.encrypt_file(file_data, key)
```

### New File Upload (Post-Quantum Hybrid)
```python
# New method - post-quantum secure
public_key = load_admin_public_key()  # Load from secure storage

# Encrypt with hybrid PQC
encrypted_result = crypto_service.encrypt_hybrid(file_data, public_key)

file_meta = {
    "file_id": new_file_id,
    "filename": file.filename,
    "uploaded_by": current_user["username"],
    "uploaded_at": datetime.now(timezone.utc).isoformat(),
    "encrypted": True,
    "encryption_method": "hybrid_kyber_aes256",
    "pqc_available": encrypted_result["pqc_available"],
    "size": len(file_data),
    "encapsulated_key": encrypted_result["encapsulated_key"],
    "encrypted_data": encrypted_result["encrypted_file"]
}
```

### Decryption (Backward Compatible)
```python
# Works with both old and new encrypted files
if file_meta.get("encryption_method") == "hybrid_kyber_aes256":
    # New PQC method
    secret_key = load_admin_secret_key()
    encrypted_result = {
        "encapsulated_key": file_meta["encapsulated_key"],
        "encrypted_file": file_meta["encrypted_data"],
        "algorithm": "hybrid_kyber_aes256"
    }
    plaintext = crypto_service.decrypt_hybrid(encrypted_result, secret_key)
else:
    # Old classical method (still supported)
    key = crypto_service.string_to_key(file_meta["encryption_key"])
    plaintext = crypto_service.decrypt_file(encrypted_data, key)
```

## Migration Strategy

### Phase 1: Setup (Day 1)
1. Install `liboqs-python` dependency
2. Generate PQC keypair
3. Store keys securely in environment/database
4. Deploy updated `crypto_service.py`

### Phase 2: Gradual Migration (Week 1-2)
1. New file uploads use hybrid encryption automatically
2. Old files continue to work (backward compatible)
3. Monitor logs for any issues
4. Test with various file types and sizes

### Phase 3: Maintenance (Ongoing)
1. Optionally re-encrypt old files on access
2. Keep classical decryption available
3. Monitor cryptographic health via logs
4. Update libraries as new versions release

## Database Schema Changes

### Old File Metadata
```json
{
  "file_id": "...",
  "filename": "document.pdf",
  "uploaded_by": "admin",
  "uploaded_at": "2025-01-21T10:00:00+00:00",
  "encrypted": true,
  "size": 102400,
  "encryption_key": "base64_encoded_key"
}
```

### New File Metadata
```json
{
  "file_id": "...",
  "filename": "document.pdf",
  "uploaded_by": "admin",
  "uploaded_at": "2025-01-21T10:00:00+00:00",
  "encrypted": true,
  "encryption_method": "hybrid_kyber_aes256",
  "pqc_available": true,
  "size": 102400,
  "encapsulated_key": "base64_kem_ciphertext",
  "encrypted_data": "base64_encrypted_file"
}
```

## Security Best Practices

### Key Storage
```python
# ❌ DON'T: Store keys in source code
SECRET_KEY = "abc123def456"

# ✅ DO: Store keys in environment or secure database
import os
secret_key = os.environ.get('PQC_SECRET_KEY')

# ✅ DO: Store in encrypted database field
# ✅ DO: Use key management service (AWS KMS, HashiCorp Vault, etc.)
```

### Key Rotation
```python
# Generate new keypair periodically
old_public_key, old_secret_key = load_current_keys()

# Generate new keypair
new_public_key, new_secret_key = CryptoService.generate_pqc_keypair()

# Transition period:
# 1. New files encrypted with new_public_key
# 2. Keep old_secret_key for backward compatibility
# 3. Old files can be re-encrypted with new key
# 4. After all files migrated, retire old_secret_key
```

### Audit Logging
```python
# Log all encryption/decryption operations
logger.info({
    "event": "file_encrypted",
    "file_id": file_id,
    "user": current_user,
    "method": "hybrid_kyber_aes256",
    "timestamp": datetime.now(timezone.utc).isoformat()
})
```

## Performance Tuning

### Benchmark Results (Expected)
```
File Size | Encryption Time | Decryption Time | Throughput
---------|-----------------|-----------------|----------
1 MB     | 2-5 ms          | 2-5 ms          | 200+ MB/s
10 MB    | 20-50 ms        | 20-50 ms        | 200+ MB/s
100 MB   | 200-500 ms      | 200-500 ms      | 200+ MB/s
1 GB     | 2-5 seconds     | 2-5 seconds     | 200+ MB/s
```

### Optimization Tips
1. Use hardware AES acceleration (AES-NI on Intel/AMD)
2. Process large files in streaming mode if needed
3. Cache encapsulated keys to avoid repeated KEM operations
4. Use async I/O for database operations

## Troubleshooting

### Issue: "No module named 'liboqs'"
```bash
# Solution: Install the library
pip install liboqs-python==0.9.1

# If pip install fails, try conda
conda install -c conda-forge liboqs-python
```

### Issue: "Authentication tag verification failed"
```python
# Cause: File corrupted or wrong key used
# Debug: Check that decryption uses same secret_key as encryption

# Solution:
# 1. Verify file wasn't tampered with
# 2. Verify correct secret_key is being used
# 3. Check database for correct encapsulated_key
```

### Issue: Slow encryption/decryption
```bash
# Cause: Missing hardware acceleration
# Solution: Ensure python-pycryptodome is compiled with AES-NI support

pip install --upgrade pycryptodome
# Or compile from source for optimization
```

### Issue: Backward compatibility with old files
```python
# Solution: Keep both decryption methods available
if "encryption_method" in file_meta:
    # New PQC method
    ...
else:
    # Fall back to old method
    plaintext = crypto_service.decrypt_file(encrypted_data, key)
```

## Monitoring & Alerts

### Log Encryption Failures
```python
try:
    encrypted = CryptoService.encrypt_hybrid(file_data, public_key)
except Exception as e:
    logger.error(f"Encryption failed: {e}", extra={
        "file_id": file_id,
        "user": current_user,
        "error_type": type(e).__name__
    })
    raise
```

### Monitor Cryptographic Health
```python
# Check if PQC is available
info = CryptoService.get_crypto_info()
if not info['pqc_available']:
    logger.warning("PQC not available, using classical encryption only")
    # Alert security team
    send_alert("PQC cryptography unavailable")
```

## Testing

### Unit Test Example
```python
import pytest
from crypto_service import CryptoService

def test_hybrid_encryption_and_decryption():
    """Test that hybrid encryption roundtrips correctly"""
    # Setup
    public_key, secret_key = CryptoService.generate_pqc_keypair()
    test_data = b"Test document content"
    
    # Encrypt
    encrypted = CryptoService.encrypt_hybrid(test_data, public_key)
    assert "encapsulated_key" in encrypted
    assert "encrypted_file" in encrypted
    
    # Decrypt
    decrypted = CryptoService.decrypt_hybrid(encrypted, secret_key)
    assert decrypted == test_data

def test_backward_compatibility():
    """Test that old classical encryption still works"""
    key = CryptoService.generate_key()
    test_data = b"Test document"
    
    # Classical encryption
    encrypted = CryptoService.encrypt_file(test_data, key)
    decrypted = CryptoService.decrypt_file(encrypted, key)
    assert decrypted == test_data
```

## References

- [Post-Quantum Cryptography Guide](./POST_QUANTUM_CRYPTOGRAPHY.md)
- [NIST PQC Standards](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [liboqs Documentation](https://liboqs.org/)
- [OpenSSL 3.0+ PQC Support](https://www.openssl.org/docs/man3.0/man7/ossl_prov_enc_postquantum.html)

## Support

For questions or issues:
1. Check POST_QUANTUM_CRYPTOGRAPHY.md for detailed specifications
2. Review pqc_key_management.py for examples
3. Test with the provided test command
4. Enable debug logging for troubleshooting

---

**Status**: ✅ Post-Quantum Cryptography Implemented
**Algorithm**: ML-KEM-768 (NIST FIPS 203) + AES-256-GCM
**Security Level**: 256-bit equivalent (post-quantum secure)
**Date**: January 2025
