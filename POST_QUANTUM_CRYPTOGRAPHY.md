# Post-Quantum Cryptography Implementation

## Overview
Implemented hybrid post-quantum cryptography for secure file encryption combining NIST-standardized post-quantum algorithms with proven symmetric encryption.

## Cryptographic Architecture

### Hybrid Encryption Model
The system uses a **hybrid encryption approach**:

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID ENCRYPTION PROCESS                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. KEY ENCAPSULATION (Post-Quantum)                         │
│     ├─ Algorithm: ML-KEM-768 (CRYSTALS-Kyber)               │
│     ├─ Encapsulate shared secret with public key             │
│     └─ Result: Encapsulated key + Shared secret              │
│                                                               │
│  2. KEY DERIVATION (Classical Cryptography)                  │
│     ├─ Input: Shared secret from KEM                         │
│     ├─ Method: PBKDF2 with 100,000 iterations                │
│     └─ Output: AES-256 symmetric key                         │
│                                                               │
│  3. FILE ENCRYPTION (Symmetric)                              │
│     ├─ Algorithm: AES-256-GCM                                │
│     ├─ Nonce: 128-bit random value                           │
│     ├─ Authentication tag: 128-bit for integrity             │
│     └─ Result: Ciphertext with authentication                │
│                                                               │
│  4. TRANSMISSION/STORAGE                                     │
│     └─ Store: Encapsulated key + Encrypted file              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Algorithms Used

### 1. ML-KEM-768 (CRYSTALS-Kyber)
**Role**: Post-quantum key encapsulation mechanism

**Why Kyber?**
- ✅ NIST-standardized (FIPS 203, released Aug 2024)
- ✅ Fastest post-quantum algorithm
- ✅ Compact key sizes (~1KB)
- ✅ Secure against quantum computers
- ✅ Production-ready in OpenSSL 3.0+

**Parameters**:
- **Security level**: ML-KEM-768 (medium, equivalent to ~192-bit classical security)
- **Public key size**: ~1,184 bytes
- **Ciphertext size**: ~1,088 bytes
- **Shared secret size**: 32 bytes

**How it works**:
1. Alice generates keypair (public_key, secret_key)
2. Alice sends public_key to Bob
3. Bob encapsulates a random shared secret using Alice's public key
4. Bob sends encapsulated secret to Alice
5. Alice decapsulates using her secret key to recover the same shared secret
6. Both use the shared secret for symmetric encryption

### 2. AES-256-GCM
**Role**: Symmetric file encryption with authentication

**Specifications**:
- **Key size**: 256 bits (32 bytes)
- **Block size**: 128 bits (16 bytes)
- **Nonce size**: 128 bits (16 bytes) - randomly generated per encryption
- **Authentication tag size**: 128 bits (16 bytes)
- **Mode**: Galois/Counter Mode (GCM) - authenticated encryption with associated data

**Advantages**:
- ✅ Quantum-resistant for symmetric encryption (due to large key size)
- ✅ Authenticated encryption (detects tampering)
- ✅ Parallelizable (fast)
- ✅ NIST-approved
- ✅ Hardware-accelerated support on modern CPUs

### 3. PBKDF2 Key Derivation
**Role**: Strengthen the shared secret into a full AES key

**Parameters**:
- **Hash function**: HMAC-SHA256
- **Iterations**: 100,000
- **Salt**: "geofence_file_encryption_salt"
- **Output length**: 256 bits (32 bytes)

**Why?**
- Expands the shared secret to full cryptographic key length
- Adds computational cost to resist brute-force attacks
- Provides domain separation with the salt

## Security Properties

### Quantum Resistance
- ✅ **Kyber**: Secure against quantum adversaries (lattice-based hard problem)
- ✅ **AES-256**: Security against quantum computers only slightly degraded (Grover's algorithm), but still >2^128 operations

### Authentication
- ✅ **AES-GCM**: Provides message authentication codes preventing tampering
- ✅ Detects any modification to ciphertext
- ✅ Decryption fails if integrity check fails

### Confidentiality
- ✅ **Kyber**: Post-quantum key agreement prevents eavesdropping even if P = NP
- ✅ **AES-256**: 2^256 effective key space
- ✅ **GCM mode**: Prevents information leakage about message length

### Forward Secrecy
- ✅ Per-file unique nonce in AES-GCM
- ✅ Each file encapsulation creates unique shared secret
- ✅ Compromise of one file doesn't affect others

## Implementation Details

### File Encryption Workflow

```python
# Encryption
file_data = b"sensitive data"
public_key = load_admin_public_key()

result = crypto_service.encrypt_hybrid(file_data, public_key)
# result = {
#     "encapsulated_key": "base64_encoded_kem_ciphertext",
#     "encrypted_file": "base64_encoded_aes_ciphertext",
#     "algorithm": "hybrid_kyber_aes256"
# }

# Store result in database or send over network

# Decryption
secret_key = load_admin_secret_key()
plaintext = crypto_service.decrypt_hybrid(result, secret_key)
# plaintext = b"sensitive data"
```

### Backward Compatibility

The classic encryption methods are still available:
```python
# Legacy method (still works, but not post-quantum)
key = crypto_service.generate_key()
encrypted = crypto_service.encrypt_file(file_data, key)
plaintext = crypto_service.decrypt_file(encrypted, key)
```

### Graceful Degradation

If `liboqs` is not installed:
- System falls back to AES-256 only
- Still secure, but not post-quantum resistant
- Logs warning message
- No crashes or failures

## API Reference

### Key Generation
```python
# Generate post-quantum keypair
public_key, secret_key = CryptoService.generate_pqc_keypair()

# Generate AES key (symmetric)
key = CryptoService.generate_key()
```

### Key Encapsulation
```python
# Encapsulate (sender side)
encapsulated_key, shared_secret = CryptoService.encapsulate(public_key)

# Decapsulate (receiver side)
shared_secret = CryptoService.decapsulate(secret_key, encapsulated_key)
```

### Symmetric Encryption
```python
# Encrypt file
encrypted_data = CryptoService.encrypt_file(file_data, aes_key)

# Decrypt file
plaintext = CryptoService.decrypt_file(encrypted_data, aes_key)
```

### Hybrid Encryption (Recommended)
```python
# All-in-one encryption
result = CryptoService.encrypt_hybrid(file_data, public_key)
# Returns: {encapsulated_key, encrypted_file, algorithm, pqc_available}

# All-in-one decryption
plaintext = CryptoService.decrypt_hybrid(result, secret_key)
```

### Utilities
```python
# Key conversion
key_string = CryptoService.key_to_string(key_bytes)
key_bytes = CryptoService.string_to_key(key_string)

# Crypto info
info = CryptoService.get_crypto_info()
# {
#     "pqc_available": True/False,
#     "pqc_algorithm": "ML-KEM-768",
#     "symmetric_encryption": "AES-256-GCM",
#     ...
# }
```

## Installation & Setup

### 1. Install liboqs (Optional but Recommended)
```bash
# macOS
brew install liboqs

# Ubuntu/Debian
sudo apt-get install liboqs-dev

# Windows
# Download from https://github.com/open-quantum-safe/liboqs/releases

# Or install Python bindings
pip install liboqs-python==0.9.1
```

### 2. Update requirements.txt
Already done! File includes `liboqs-python==0.9.1`

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```python
from backend.crypto_service import CryptoService

info = CryptoService.get_crypto_info()
print(info)
# Should show:
# {
#     "pqc_available": True,
#     "pqc_algorithm": "ML-KEM-768",
#     ...
# }
```

## Performance Characteristics

### Encryption Performance
- **AES-256-GCM**: ~5-10 GB/s on modern CPUs (with AES-NI)
- **Kyber encapsulation**: ~1-2 ms per operation
- **PBKDF2 derivation**: ~100-200 ms (by design, resists brute-force)

### Key Sizes
- **Public key**: 1,184 bytes
- **Secret key**: 2,400 bytes
- **Encapsulated key**: 1,088 bytes
- **Shared secret**: 32 bytes
- **AES key**: 32 bytes (256 bits)

### Storage Overhead
For a 1 MB file:
- Encapsulated key: ~1 KB (0.1% overhead)
- Nonce + tag: ~32 bytes (negligible)
- Total overhead: <1 KB per file

## Security Considerations

### Key Management
1. **Admin public key**: Safe to share, distribute to all employees
2. **Admin secret key**: Never share, store securely with proper access controls
3. **Per-file shared secret**: Unique to each encrypted file, not reused

### Threat Model
This implementation protects against:
- ✅ Eavesdropping (confidentiality)
- ✅ Tampering (authenticity)
- ✅ Brute force attacks (strong cryptographic parameters)
- ✅ Quantum computers (post-quantum algorithms)
- ✅ Replay attacks (unique nonces per encryption)

### Assumptions
- Admin secret key remains secret
- Cryptographic libraries are correctly implemented
- Random number generation is secure
- System time is roughly synchronized

## Migration Guide

### From Classical to Post-Quantum

**Step 1**: Update requirements
```bash
pip install liboqs-python==0.9.1
```

**Step 2**: Regenerate keys (one-time)
```python
# Generate new post-quantum keypair
public_key, secret_key = CryptoService.generate_pqc_keypair()
# Store securely in admin credentials
```

**Step 3**: Use hybrid encryption for new files
```python
# New files use hybrid encryption
result = CryptoService.encrypt_hybrid(file_data, public_key)
```

**Step 4**: Handle existing files
```python
# Old files encrypted with classical method still work
plaintext = CryptoService.decrypt_file(old_encrypted_data, old_key)

# Can re-encrypt with hybrid on access
result = CryptoService.encrypt_hybrid(plaintext, public_key)
```

## Testing Post-Quantum Cryptography

### Unit Tests
```python
def test_hybrid_encryption():
    # Generate keypair
    pub, sec = CryptoService.generate_pqc_keypair()
    
    # Test data
    test_file = b"confidential document"
    
    # Encrypt
    encrypted = CryptoService.encrypt_hybrid(test_file, pub)
    
    # Decrypt
    decrypted = CryptoService.decrypt_hybrid(encrypted, sec)
    
    # Verify
    assert decrypted == test_file
    print("✓ Hybrid encryption works")
```

### Performance Tests
```python
import time

def benchmark_encryption(file_size_mb=10):
    file_data = get_random_bytes(file_size_mb * 1024 * 1024)
    pub, _ = CryptoService.generate_pqc_keypair()
    
    start = time.time()
    encrypted = CryptoService.encrypt_hybrid(file_data, pub)
    encryption_time = time.time() - start
    
    print(f"Encrypted {file_size_mb}MB in {encryption_time:.2f}s")
    print(f"Throughput: {file_size_mb/encryption_time:.1f} MB/s")
```

## FAQ

### Q: Is AES-256 quantum-resistant?
**A**: Yes, but less than Kyber. AES-256 with quantum computers requires ~2^128 operations (still secure), while classical requires ~2^256.

### Q: Why hybrid and not pure PQC?
**A**: Kyber is only for key exchange. For actual file encryption, AES-GCM is faster, more mature, and hardware-accelerated. Hybrid approach combines both benefits.

### Q: What if liboqs fails to install?
**A**: System automatically falls back to AES-256 only. Files remain encrypted and secure, just not post-quantum resistant. Install liboqs separately anytime.

### Q: Can I use my own public key?
**A**: Yes! Pass any public key to `encrypt_hybrid()`. Useful for multi-recipient scenarios or integration with external PKI.

### Q: Is this NIST-approved?
**A**: Yes! ML-KEM-768 is officially standardized as FIPS 203. AES-256-GCM is FIPS 197.

### Q: What about digital signatures?
**A**: Can implement ML-DSA (CRYSTALS-Dilithium) for post-quantum signatures in future versions.

## References

- [NIST Post-Quantum Cryptography](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [FIPS 203: ML-KEM (Kyber)](https://csrc.nist.gov/pubs/fips/203/final)
- [liboqs Project](https://github.com/open-quantum-safe/liboqs)
- [AES-GCM Specification](https://csrc.nist.gov/publications/detail/sp/800-38d/final)

## Support & Troubleshooting

### Issue: "liboqs not available"
```
Solution: pip install liboqs-python
```

### Issue: Decryption fails with "authentication tag verification failed"
```
Cause: Ciphertext was modified or wrong key used
Solution: Verify ciphertext integrity and use correct secret key
```

### Issue: Key format errors
```
Solution: Use CryptoService.key_to_string() for storage,
         Use CryptoService.string_to_key() for loading
```
