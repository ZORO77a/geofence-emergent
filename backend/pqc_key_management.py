#!/usr/bin/env python3
"""
Post-Quantum Cryptography Key Management Utility
Helps generate, manage, and test post-quantum keypairs
"""

import argparse
import json
import base64
import sys
from pathlib import Path
from crypto_service import CryptoService

def generate_keypair(output_dir: str = "."):
    """Generate a new post-quantum keypair and save to files"""
    print("🔐 Generating post-quantum keypair (ML-KEM-768)...")
    
    try:
        public_key, secret_key = CryptoService.generate_pqc_keypair()
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save public key
        pub_file = output_path / "pqc_public_key.bin"
        pub_file.write_bytes(public_key)
        print(f"✓ Public key saved to: {pub_file} ({len(public_key)} bytes)")
        
        # Save secret key
        sec_file = output_path / "pqc_secret_key.bin"
        sec_file.write_bytes(secret_key)
        print(f"✓ Secret key saved to: {sec_file} ({len(secret_key)} bytes)")
        
        # Save base64 encoded versions for easy database storage
        pub_b64_file = output_path / "pqc_public_key_b64.txt"
        pub_b64_file.write_text(base64.b64encode(public_key).decode('utf-8'))
        print(f"✓ Public key (base64) saved to: {pub_b64_file}")
        
        sec_b64_file = output_path / "pqc_secret_key_b64.txt"
        sec_b64_file.write_text(base64.b64encode(secret_key).decode('utf-8'))
        print(f"✓ Secret key (base64) saved to: {sec_b64_file}")
        
        print(f"\n📊 Keypair Info:")
        print(f"  Public key size: {len(public_key):,} bytes")
        print(f"  Secret key size: {len(secret_key):,} bytes")
        print(f"  Algorithm: ML-KEM-768 (NIST FIPS 203)")
        
    except Exception as e:
        print(f"❌ Error generating keypair: {e}", file=sys.stderr)
        sys.exit(1)

def test_encryption(public_key_file: str, secret_key_file: str, test_file: str = None):
    """Test hybrid encryption and decryption"""
    print("🧪 Testing hybrid encryption...")
    
    try:
        # Load keys
        public_key = Path(public_key_file).read_bytes()
        secret_key = Path(secret_key_file).read_bytes()
        
        # Test data
        if test_file:
            test_data = Path(test_file).read_bytes()
            print(f"Using file: {test_file} ({len(test_data):,} bytes)")
        else:
            test_data = b"This is a test message for post-quantum encryption" * 100
            print(f"Using test message ({len(test_data):,} bytes)")
        
        # Encrypt
        print("\n1️⃣ Encrypting...")
        encrypted = CryptoService.encrypt_hybrid(test_data, public_key)
        print(f"✓ Encryption successful")
        print(f"  Encapsulated key size: {len(base64.b64decode(encrypted['encapsulated_key'])):,} bytes")
        print(f"  Encrypted file size: {len(base64.b64decode(encrypted['encrypted_file'])):,} bytes")
        
        # Decrypt
        print("\n2️⃣ Decrypting...")
        decrypted = CryptoService.decrypt_hybrid(encrypted, secret_key)
        print(f"✓ Decryption successful")
        
        # Verify
        print("\n3️⃣ Verifying integrity...")
        if decrypted == test_data:
            print("✓ Decrypted data matches original!")
            print(f"\n✅ All tests passed! Post-quantum encryption is working correctly.")
        else:
            print(f"❌ Data mismatch! Decrypted data does not match original.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during testing: {e}", file=sys.stderr)
        sys.exit(1)

def show_crypto_info():
    """Display cryptographic configuration"""
    print("📋 Cryptographic Configuration:\n")
    
    info = CryptoService.get_crypto_info()
    
    for key, value in info.items():
        # Format key name
        display_key = key.replace('_', ' ').title()
        print(f"  {display_key}: {value}")
    
    if info['pqc_available']:
        print("\n✅ Post-Quantum Cryptography is AVAILABLE and ACTIVE")
    else:
        print("\n⚠️  Post-Quantum Cryptography is NOT available")
        print("   Install liboqs-python to enable PQC:")
        print("   pip install liboqs-python==0.9.1")

def load_keypair(public_key_file: str, secret_key_file: str):
    """Load and validate keypair"""
    print("🔑 Loading keypair...")
    
    try:
        public_key = Path(public_key_file).read_bytes()
        secret_key = Path(secret_key_file).read_bytes()
        
        print(f"✓ Loaded public key ({len(public_key):,} bytes)")
        print(f"✓ Loaded secret key ({len(secret_key):,} bytes)")
        
        # Simple validation
        if len(public_key) < 100 or len(secret_key) < 100:
            print("⚠️  Warning: Keys seem small, verify they're correct")
        
        return public_key, secret_key
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading keypair: {e}", file=sys.stderr)
        sys.exit(1)

def create_wrapper_script():
    """Create a sample usage script"""
    wrapper_code = '''#!/usr/bin/env python3
"""
Example: Using Post-Quantum Cryptography in your application
"""

from crypto_service import CryptoService
from pathlib import Path

# Load keys (in real app, load from secure storage)
public_key = Path("pqc_public_key.bin").read_bytes()
secret_key = Path("pqc_secret_key.bin").read_bytes()

# Read file to encrypt
file_data = Path("document.pdf").read_bytes()

# Encrypt with post-quantum cryptography
encrypted_result = CryptoService.encrypt_hybrid(file_data, public_key)

# Store encrypted result
import json
with open("document.encrypted", "w") as f:
    json.dump(encrypted_result, f)

print("✓ File encrypted with post-quantum cryptography")

# Later: decrypt the file
with open("document.encrypted", "r") as f:
    encrypted_result = json.load(f)

decrypted_data = CryptoService.decrypt_hybrid(encrypted_result, secret_key)
Path("document_decrypted.pdf").write_bytes(decrypted_data)

print("✓ File decrypted successfully")
'''
    
    script_path = Path("pqc_usage_example.py")
    script_path.write_text(wrapper_code)
    script_path.chmod(0o755)
    print(f"✓ Created example script: {script_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Post-Quantum Cryptography Key Management Utility"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate new keypair')
    gen_parser.add_argument('-o', '--output', default='.', help='Output directory')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test encryption/decryption')
    test_parser.add_argument('public_key', help='Path to public key file')
    test_parser.add_argument('secret_key', help='Path to secret key file')
    test_parser.add_argument('-f', '--file', help='File to test with (optional)')
    
    # Info command
    subparsers.add_parser('info', help='Show cryptographic configuration')
    
    # Wrapper command
    subparsers.add_parser('example', help='Create example usage script')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'generate':
        generate_keypair(args.output)
    
    elif args.command == 'test':
        test_encryption(args.public_key, args.secret_key, args.file)
    
    elif args.command == 'info':
        show_crypto_info()
    
    elif args.command == 'example':
        create_wrapper_script()

if __name__ == '__main__':
    main()
