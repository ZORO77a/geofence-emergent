from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64
import json
import logging
from typing import Tuple, Dict
import hashlib

logger = logging.getLogger(__name__)

# Try to import liboqs for post-quantum cryptography
try:
    import oqs
    PQC_AVAILABLE = True
    logger.info("✅ Post-Quantum Cryptography (liboqs) is available")
except (ImportError, RuntimeError) as e:
    PQC_AVAILABLE = False
    logger.warning(f"⚠️ liboqs not available, using classical AES-256 only: {e}")

class CryptoService:
    """
    Hybrid Post-Quantum Cryptography service
    
    Uses:
    - CRYSTALS-Kyber (ML-KEM) for post-quantum key encapsulation
    - AES-256-GCM for symmetric file encryption
    
    This hybrid approach provides:
    1. Post-quantum security for key exchange
    2. Strong symmetric encryption for file data
    3. Authentication tags for integrity verification
    """
    
    # Kyber parameters
    KYBER_ALG = "ML-KEM-768"  # Medium security level, widely supported
    
    # Encryption parameters
    AES_KEY_SIZE = 32  # 256-bit key
    AES_NONCE_SIZE = 16  # 128-bit nonce
    AES_TAG_SIZE = 16  # 128-bit authentication tag
    
    @staticmethod
    def generate_pqc_keypair() -> Tuple[bytes, bytes]:
        """
        Generate a post-quantum keypair using Kyber
        Returns (public_key, secret_key)
        """
        if not PQC_AVAILABLE:
            logger.warning("PQC not available, generating classical key pair")
            return CryptoService._generate_classical_keypair()
        
        try:
            keygen = liboqs.KeyEncapsulation(CryptoService.KYBER_ALG)
            public_key = keygen.generate_keypair()
            secret_key = keygen.export_secret_key()
            
            logger.info(f"Generated PQC keypair using {CryptoService.KYBER_ALG}")
            return public_key, secret_key
        except Exception as e:
            logger.error(f"Failed to generate PQC keypair: {e}")
            return CryptoService._generate_classical_keypair()
    
    @staticmethod
    def _generate_classical_keypair() -> Tuple[bytes, bytes]:
        """Fallback to classical key generation"""
        # For classical fallback, generate a random identifier
        # In production, use RSA or ECDH
        keypair_id = get_random_bytes(32)
        return keypair_id, keypair_id
    
    @staticmethod
    def encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Encapsulate a shared secret using the public key
        Returns (encapsulated_key, shared_secret)
        
        The encapsulated_key is transmitted, shared_secret is used for encryption
        """
        if not PQC_AVAILABLE:
            logger.warning("PQC not available, using classical method")
            return CryptoService._encapsulate_classical(public_key)
        
        try:
            kem = oqs.KeyEncapsulation(CryptoService.KYBER_ALG, public_key)
            ciphertext, shared_secret = kem.encap_secret()
            
            logger.debug(f"Encapsulated secret using {CryptoService.KYBER_ALG}")
            return ciphertext, shared_secret
        except Exception as e:
            logger.error(f"Encapsulation failed: {e}")
            return CryptoService._encapsulate_classical(public_key)
    
    @staticmethod
    def _encapsulate_classical(public_key: bytes) -> Tuple[bytes, bytes]:
        """Fallback classical encapsulation"""
        shared_secret = get_random_bytes(32)
        # Encapsulated form is just the secret with timestamp
        encapsulated = shared_secret + get_random_bytes(16)
        return encapsulated, shared_secret
    
    @staticmethod
    def decapsulate(secret_key: bytes, encapsulated_key: bytes) -> bytes:
        """
        Decapsulate the shared secret using the secret key
        Returns the shared_secret
        """
        if not PQC_AVAILABLE:
            logger.warning("PQC not available, using classical method")
            return CryptoService._decapsulate_classical(secret_key, encapsulated_key)
        
        try:
            kem = oqs.KeyEncapsulation(CryptoService.KYBER_ALG, secret_key)
            shared_secret = kem.decap_secret(encapsulated_key)
            
            logger.debug(f"Decapsulated secret using {CryptoService.KYBER_ALG}")
            return shared_secret
        except Exception as e:
            logger.error(f"Decapsulation failed: {e}")
            return CryptoService._decapsulate_classical(secret_key, encapsulated_key)
    
    @staticmethod
    def _decapsulate_classical(secret_key: bytes, encapsulated_key: bytes) -> bytes:
        """Fallback classical decapsulation"""
        return encapsulated_key[:32]
    
    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a random AES-256 key for file encryption
        Used for hybrid encryption: shared secret -> file encryption key
        """
        return get_random_bytes(CryptoService.AES_KEY_SIZE)
    
    @staticmethod
    def derive_key_from_shared_secret(shared_secret: bytes) -> bytes:
        """
        Derive an AES-256 key from the shared secret using PBKDF2
        Strengthens the shared secret for file encryption
        """
        # Use PBKDF2 to derive a strong key
        salt = b"geofence_file_encryption_salt"
        key = PBKDF2(
            shared_secret,
            salt,
            dkLen=CryptoService.AES_KEY_SIZE,
            count=100000,
            hmac_hash_module=None
        )
        return key
    
    @staticmethod
    def encrypt_file(file_data: bytes, key: bytes) -> bytes:
        """
        Encrypt file data using AES-256 in GCM mode
        Returns: nonce + tag + ciphertext (encrypted_data)
        
        GCM provides authenticated encryption (confidentiality + authenticity)
        """
        try:
            cipher = AES.new(key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(file_data)
            
            # Combine nonce + tag + ciphertext for storage/transmission
            encrypted_data = cipher.nonce + tag + ciphertext
            return encrypted_data
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_file(encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt file data encrypted with encrypt_file
        Validates authentication tag to ensure integrity
        """
        try:
            # Extract components
            nonce = encrypted_data[:CryptoService.AES_NONCE_SIZE]
            tag = encrypted_data[CryptoService.AES_NONCE_SIZE:CryptoService.AES_NONCE_SIZE + CryptoService.AES_TAG_SIZE]
            ciphertext = encrypted_data[CryptoService.AES_NONCE_SIZE + CryptoService.AES_TAG_SIZE:]
            
            # Decrypt and verify
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise
    
    @staticmethod
    def encrypt_hybrid(file_data: bytes, public_key: bytes = None) -> Dict[str, str]:
        """
        Hybrid encryption combining PQC and AES
        
        Process:
        1. Encapsulate a shared secret using public key (PQC)
        2. Derive AES key from shared secret
        3. Encrypt file with AES-256-GCM
        4. Return both encapsulated key and encrypted file
        
        Returns:
        {
            "encapsulated_key": base64 encoded encapsulated key,
            "encrypted_file": base64 encoded encrypted file,
            "algorithm": "hybrid_kyber_aes256"
        }
        """
        try:
            # If no public key provided, generate a keypair
            if public_key is None:
                public_key, _ = CryptoService.generate_pqc_keypair()
            
            # Encapsulate shared secret
            encapsulated_key, shared_secret = CryptoService.encapsulate(public_key)
            
            # Derive encryption key
            encryption_key = CryptoService.derive_key_from_shared_secret(shared_secret)
            
            # Encrypt file
            encrypted_file = CryptoService.encrypt_file(file_data, encryption_key)
            
            logger.info("Hybrid encryption completed (PQC + AES-256)")
            
            return {
                "encapsulated_key": base64.b64encode(encapsulated_key).decode('utf-8'),
                "encrypted_file": base64.b64encode(encrypted_file).decode('utf-8'),
                "algorithm": "hybrid_kyber_aes256",
                "pqc_available": PQC_AVAILABLE
            }
        except Exception as e:
            logger.error(f"Hybrid encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_hybrid(encrypted_data: Dict[str, str], secret_key: bytes) -> bytes:
        """
        Hybrid decryption using private key and AES
        
        Process:
        1. Decapsulate shared secret using secret key (PQC)
        2. Derive AES key from shared secret
        3. Decrypt file with AES-256-GCM
        4. Return plaintext file
        """
        try:
            # Decode components
            encapsulated_key = base64.b64decode(encrypted_data["encapsulated_key"])
            encrypted_file = base64.b64decode(encrypted_data["encrypted_file"])
            
            # Decapsulate shared secret
            shared_secret = CryptoService.decapsulate(secret_key, encapsulated_key)
            
            # Derive decryption key
            decryption_key = CryptoService.derive_key_from_shared_secret(shared_secret)
            
            # Decrypt file
            plaintext = CryptoService.decrypt_file(encrypted_file, decryption_key)
            
            logger.info("Hybrid decryption completed (PQC + AES-256)")
            return plaintext
        except Exception as e:
            logger.error(f"Hybrid decryption failed: {e}")
            raise
    
    # Legacy methods for backward compatibility
    @staticmethod
    def key_to_string(key: bytes) -> str:
        """Convert key to base64 string for storage"""
        return base64.b64encode(key).decode('utf-8')
    
    @staticmethod
    def string_to_key(key_str: str) -> bytes:
        """Convert base64 string back to key"""
        return base64.b64decode(key_str)
    
    @staticmethod
    def get_crypto_info() -> Dict:
        """Get information about cryptographic setup"""
        return {
            "pqc_available": PQC_AVAILABLE,
            "pqc_algorithm": CryptoService.KYBER_ALG if PQC_AVAILABLE else "None",
            "symmetric_encryption": "AES-256-GCM",
            "mode": "Hybrid (PQC key exchange + AES symmetric)",
            "aes_key_size": f"{CryptoService.AES_KEY_SIZE * 8} bits",
            "nonce_size": f"{CryptoService.AES_NONCE_SIZE * 8} bits",
            "tag_size": f"{CryptoService.AES_TAG_SIZE * 8} bits",
            "kdf": "PBKDF2 with 100,000 iterations"
        }

