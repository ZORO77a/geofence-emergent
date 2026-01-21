# Post-Quantum Cryptography - Code Examples

## File Upload with PQC Encryption

### Before (Classical AES-256)
```python
@api_router.post("/upload")
async def upload_file(file: UploadFile, current_user: dict = Depends(get_current_user)):
    """Classical file upload - no longer recommended"""
    file_data = await file.read()
    new_file_id = str(uuid.uuid4())
    
    # Generate random key
    key = crypto_service.generate_key()
    
    # Encrypt with classical AES
    encrypted_data = crypto_service.encrypt_file(file_data, key)
    
    # Store in GridFS
    file_id = await fs.upload_from_stream(
        new_file_id,
        encrypted_data
    )
    
    # Store metadata
    file_meta = {
        "file_id": new_file_id,
        "filename": file.filename,
        "uploaded_by": current_user["username"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "encrypted": True,
        "size": len(file_data),
        "encryption_key": crypto_service.key_to_string(key)  # ⚠️ Key stored in DB
    }
    await db.file_metadata.insert_one(file_meta)
    
    return {"file_id": new_file_id, "status": "uploaded"}
```

### After (Post-Quantum Hybrid)
```python
@api_router.post("/upload")
async def upload_file(file: UploadFile, current_user: dict = Depends(get_current_user)):
    """Post-quantum file upload - quantum-resistant"""
    file_data = await file.read()
    new_file_id = str(uuid.uuid4())
    
    # Load admin's public key (from environment or database)
    admin_public_key = load_pqc_public_key()  # bytes
    
    # Encrypt with hybrid post-quantum method
    encrypted_result = crypto_service.encrypt_hybrid(file_data, admin_public_key)
    
    # Store encrypted file + encapsulated key
    file_id = await fs.upload_from_stream(
        new_file_id,
        base64.b64decode(encrypted_result["encrypted_file"])
    )
    
    # Store metadata with PQC info
    file_meta = {
        "file_id": new_file_id,
        "filename": file.filename,
        "uploaded_by": current_user["username"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "encrypted": True,
        "encryption_method": "hybrid_kyber_aes256",
        "pqc_available": encrypted_result["pqc_available"],
        "size": len(file_data),
        "encapsulated_key": encrypted_result["encapsulated_key"],  # ✅ No key needed
    }
    await db.file_metadata.insert_one(file_meta)
    
    logger.info(f"File {new_file_id} uploaded with hybrid PQC encryption")
    return {"file_id": new_file_id, "status": "uploaded", "method": "hybrid_kyber_aes256"}
```

## File Download with PQC Decryption

### Before (Classical AES-256)
```python
@api_router.post("/access_file")
async def access_file(request: AccessRequest, current_user: dict = Depends(get_current_user)):
    """Classical file access - retrieves and decrypts"""
    
    # Get file metadata
    file_meta = await db.file_metadata.find_one({"file_id": request.file_id})
    
    # Download encrypted file from GridFS
    grid_out = await fs.open_download_stream(ObjectId(file_meta["file_id"]))
    encrypted_data = await grid_out.read()
    
    # Decrypt using stored key
    key = crypto_service.string_to_key(file_meta["encryption_key"])  # ⚠️ Key from DB
    plaintext = crypto_service.decrypt_file(encrypted_data, key)
    
    # Return file
    return StreamingResponse(
        io.BytesIO(plaintext),
        media_type="application/octet-stream"
    )
```

### After (Post-Quantum Hybrid)
```python
@api_router.post("/access_file")
async def access_file(request: AccessRequest, current_user: dict = Depends(get_current_user)):
    """Post-quantum file access - quantum-resistant decryption"""
    
    # Get file metadata
    file_meta = await db.file_metadata.find_one({"file_id": request.file_id})
    
    # Determine encryption method
    encryption_method = file_meta.get("encryption_method", "classical")
    
    if encryption_method == "hybrid_kyber_aes256":
        # New PQC method
        logger.debug(f"Decrypting file {request.file_id} using PQC method")
        
        # Load admin's secret key
        admin_secret_key = load_pqc_secret_key()  # bytes
        
        # Download encrypted file
        grid_out = await fs.open_download_stream(ObjectId(file_meta["file_id"]))
        encrypted_file_b64 = await grid_out.read()
        
        # Prepare encrypted result
        encrypted_result = {
            "encapsulated_key": file_meta["encapsulated_key"],
            "encrypted_file": encrypted_file_b64.decode('utf-8'),
            "algorithm": "hybrid_kyber_aes256"
        }
        
        # Decrypt using post-quantum method
        plaintext = crypto_service.decrypt_hybrid(encrypted_result, admin_secret_key)
        
    else:
        # Legacy classical method (backward compatibility)
        logger.debug(f"Decrypting file {request.file_id} using classical method")
        
        # Download encrypted file
        grid_out = await fs.open_download_stream(ObjectId(file_meta["file_id"]))
        encrypted_data = await grid_out.read()
        
        # Decrypt using stored key
        key = crypto_service.string_to_key(file_meta["encryption_key"])
        plaintext = crypto_service.decrypt_file(encrypted_data, key)
    
    # Log successful access
    logger.info(f"File {request.file_id} accessed and decrypted by {current_user['username']}")
    
    # Return file
    return StreamingResponse(
        io.BytesIO(plaintext),
        media_type="application/octet-stream"
    )
```

## Key Loading Functions

### Load Public Key (for encryption)
```python
import os
import base64

def load_pqc_public_key() -> bytes:
    """Load post-quantum public key for encryption"""
    
    # Option 1: From environment variable
    pub_key_b64 = os.environ.get('PQC_PUBLIC_KEY')
    if pub_key_b64:
        return base64.b64decode(pub_key_b64)
    
    # Option 2: From file
    from pathlib import Path
    key_file = Path("keys/pqc_public_key.bin")
    if key_file.exists():
        return key_file.read_bytes()
    
    # Option 3: From database
    from motor.motor_asyncio import AsyncIOMotorClient
    # config = await db.admin_config.find_one({})
    # return base64.b64decode(config['pqc_public_key'])
    
    raise ValueError("PQC public key not found")

def load_pqc_secret_key() -> bytes:
    """Load post-quantum secret key for decryption"""
    
    # Option 1: From environment variable (SECURE)
    sec_key_b64 = os.environ.get('PQC_SECRET_KEY')
    if sec_key_b64:
        return base64.b64decode(sec_key_b64)
    
    # Option 2: From secure vault (RECOMMENDED)
    # import hvac
    # client = hvac.Client(url='http://localhost:8200')
    # secret = client.secrets.kv.read_secret_version(path='geofence/pqc_secret_key')
    # return base64.b64decode(secret['data']['data']['secret_key'])
    
    # Option 3: From encrypted database (less secure)
    # config = await db.admin_config.find_one({})
    # encrypted_key = config['pqc_secret_key_encrypted']
    # return decrypt_with_master_key(encrypted_key)
    
    raise ValueError("PQC secret key not found")
```

## Database Schema Migration

### Old Schema
```python
# File metadata with encryption key
file_meta = {
    "_id": ObjectId(),
    "file_id": "uuid-1234",
    "filename": "document.pdf",
    "uploaded_by": "admin",
    "uploaded_at": "2025-01-21T10:00:00+00:00",
    "encrypted": True,
    "size": 102400,
    "encryption_key": "base64_encoded_aes_key"  # ❌ Key in database
}
```

### New Schema (PQC)
```python
# File metadata with encapsulated key
file_meta = {
    "_id": ObjectId(),
    "file_id": "uuid-1234",
    "filename": "document.pdf",
    "uploaded_by": "admin",
    "uploaded_at": "2025-01-21T10:00:00+00:00",
    "encrypted": True,
    "encryption_method": "hybrid_kyber_aes256",  # ✅ New field
    "pqc_available": True,  # ✅ New field
    "size": 102400,
    "encapsulated_key": "base64_kem_ciphertext",  # ✅ New field
    # "encryption_key": null  # ❌ No longer needed for PQC
}
```

### Migration Script
```python
async def migrate_file_metadata():
    """Add PQC fields to existing file metadata"""
    
    # For new files uploaded, they'll have the new schema automatically
    # For old files, you can:
    
    # Option 1: Add default values
    await db.file_metadata.update_many(
        {"encryption_method": {"$exists": False}},
        {"$set": {
            "encryption_method": "classical_aes256",
            "pqc_available": False
        }}
    )
    
    # Option 2: Re-encrypt old files with PQC (optional)
    # Requires reading each file, decrypting with old key, 
    # re-encrypting with new public key
    old_files = await db.file_metadata.find({
        "encryption_method": "classical_aes256"
    }).to_list(1000)
    
    public_key = load_pqc_public_key()
    
    for file_meta in old_files:
        # Skip re-encryption for now, just update metadata
        # Later can implement async batch re-encryption
        pass

# Run migration
# asyncio.run(migrate_file_metadata())
```

## Testing Code

### Unit Test - Hybrid Encryption
```python
import pytest
from crypto_service import CryptoService

@pytest.mark.asyncio
async def test_hybrid_encryption_roundtrip():
    """Test hybrid encryption and decryption"""
    
    # Generate keypair
    public_key, secret_key = CryptoService.generate_pqc_keypair()
    
    # Test data
    test_data = b"Confidential document content" * 100
    
    # Encrypt
    encrypted = CryptoService.encrypt_hybrid(test_data, public_key)
    
    # Verify structure
    assert "encapsulated_key" in encrypted
    assert "encrypted_file" in encrypted
    assert "algorithm" in encrypted
    assert encrypted["algorithm"] == "hybrid_kyber_aes256"
    
    # Decrypt
    decrypted = CryptoService.decrypt_hybrid(encrypted, secret_key)
    
    # Verify correctness
    assert decrypted == test_data
    print("✓ Hybrid encryption test passed")

@pytest.mark.asyncio
async def test_backward_compatibility():
    """Test that classical encryption still works"""
    
    # Classical method
    key = CryptoService.generate_key()
    test_data = b"Test data"
    
    # Encrypt and decrypt
    encrypted = CryptoService.encrypt_file(test_data, key)
    decrypted = CryptoService.decrypt_file(encrypted, key)
    
    assert decrypted == test_data
    print("✓ Backward compatibility test passed")

@pytest.mark.asyncio
async def test_file_upload_pqc():
    """Test complete file upload flow with PQC"""
    
    # Simulate file upload
    file_data = b"File content here"
    public_key, secret_key = CryptoService.generate_pqc_keypair()
    
    # Upload (encrypt)
    encrypted_result = CryptoService.encrypt_hybrid(file_data, public_key)
    
    file_meta = {
        "file_id": "test-123",
        "filename": "test.pdf",
        "encryption_method": "hybrid_kyber_aes256",
        "encapsulated_key": encrypted_result["encapsulated_key"],
    }
    
    # Simulate file access (decrypt)
    retrieved = {
        "encapsulated_key": file_meta["encapsulated_key"],
        "encrypted_file": encrypted_result["encrypted_file"],
        "algorithm": "hybrid_kyber_aes256"
    }
    
    decrypted = CryptoService.decrypt_hybrid(retrieved, secret_key)
    
    assert decrypted == file_data
    print("✓ File upload/access PQC flow test passed")
```

### Integration Test - Full Workflow
```python
async def test_full_pqc_workflow():
    """Test complete PQC encryption workflow"""
    
    print("1. Generating keys...")
    public_key, secret_key = CryptoService.generate_pqc_keypair()
    
    print("2. Creating test file...")
    test_file = b"Sensitive document" * 1000
    
    print("3. Encrypting with PQC...")
    encrypted = CryptoService.encrypt_hybrid(test_file, public_key)
    
    print("4. Simulating storage...")
    file_metadata = {
        "encapsulated_key": encrypted["encapsulated_key"],
        "pqc_available": encrypted["pqc_available"]
    }
    
    print("5. Retrieving and decrypting...")
    result = {
        "encapsulated_key": file_metadata["encapsulated_key"],
        "encrypted_file": encrypted["encrypted_file"],
        "algorithm": encrypted["algorithm"]
    }
    decrypted = CryptoService.decrypt_hybrid(result, secret_key)
    
    print("6. Verifying...")
    assert decrypted == test_file
    
    print("✅ Full PQC workflow test passed!")
    return True

# Run test
# asyncio.run(test_full_pqc_workflow())
```

## Error Handling

### Graceful Degradation
```python
def encrypt_with_fallback(file_data: bytes, public_key: bytes):
    """Encrypt with PQC, fallback to classical if needed"""
    
    try:
        # Try post-quantum hybrid
        result = crypto_service.encrypt_hybrid(file_data, public_key)
        logger.info("Encrypted with hybrid PQC")
        return result
    
    except Exception as e:
        logger.warning(f"PQC encryption failed, falling back: {e}")
        
        # Fallback to classical AES
        key = crypto_service.generate_key()
        encrypted = crypto_service.encrypt_file(file_data, key)
        
        return {
            "encapsulated_key": None,
            "encrypted_file": base64.b64encode(encrypted).decode('utf-8'),
            "algorithm": "classical_aes256",
            "fallback": True,
            "encryption_key": crypto_service.key_to_string(key)
        }
```

## Monitoring & Logging

### Log All Encryption Operations
```python
import logging

logger = logging.getLogger(__name__)

def encrypt_file_with_logging(file_data, filename, user, public_key):
    """Encrypt file and log operation"""
    
    logger.info(f"Starting encryption: {filename} by {user}")
    
    try:
        encrypted = crypto_service.encrypt_hybrid(file_data, public_key)
        
        logger.info({
            "event": "file_encrypted",
            "filename": filename,
            "user": user,
            "size": len(file_data),
            "method": "hybrid_kyber_aes256",
            "pqc_available": encrypted["pqc_available"]
        })
        
        return encrypted
    
    except Exception as e:
        logger.error({
            "event": "encryption_failed",
            "filename": filename,
            "user": user,
            "error": str(e)
        })
        raise
```

---

These examples show how to integrate post-quantum cryptography into your existing file upload/download system while maintaining backward compatibility with classical encryption.
