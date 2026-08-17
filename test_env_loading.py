"""
Test script to verify environment variable loading.
"""

import os
from dotenv import load_dotenv

print("=" * 80)
print("Testing Environment Variable Loading")
print("=" * 80)

# Load .env file
print("\n1. Loading .env file...")
load_dotenv()
print("✓ .env file loaded")

# Test MISTRAL_API_KEY
print("\n2. Testing MISTRAL_API_KEY...")
mistral_key = os.getenv("MISTRAL_API_KEY")
if mistral_key:
    print(f"✓ MISTRAL_API_KEY loaded: {mistral_key[:8]}...{mistral_key[-4:]}")
    print(f"  Length: {len(mistral_key)} characters")
    if mistral_key.startswith('"') and mistral_key.endswith('"'):
        print("  ⚠️ WARNING: API key has quotes around it! Remove quotes from .env")
    else:
        print("  ✓ No quotes - format is correct")
else:
    print("✗ MISTRAL_API_KEY not found!")

# Test SARVAM_API_KEY
print("\n3. Testing SARVAM_API_KEY...")
sarvam_key = os.getenv("SARVAM_API_KEY")
if sarvam_key:
    print(f"✓ SARVAM_API_KEY loaded: {sarvam_key[:8]}...{sarvam_key[-4:]}")
    print(f"  Length: {len(sarvam_key)} characters")
    if sarvam_key.startswith('"') and sarvam_key.endswith('"'):
        print("  ⚠️ WARNING: API key has quotes around it! Remove quotes from .env")
    else:
        print("  ✓ No quotes - format is correct")
else:
    print("✗ SARVAM_API_KEY not found!")

# Test SARVAM_STT_MODEL
print("\n4. Testing SARVAM_STT_MODEL...")
sarvam_model = os.getenv("SARVAM_STT_MODEL")
if sarvam_model:
    print(f"✓ SARVAM_STT_MODEL loaded: {sarvam_model}")
    if sarvam_model.startswith('"') and sarvam_model.endswith('"'):
        print("  ⚠️ WARNING: Model name has quotes around it! Remove quotes from .env")
    else:
        print("  ✓ No quotes - format is correct")
else:
    print("✗ SARVAM_STT_MODEL not found!")

# Test in transcriber context
print("\n5. Testing in transcriber context...")
try:
    from core.transcriber import SARVAM_API_KEY as TRANSCRIBER_KEY
    if TRANSCRIBER_KEY:
        print(f"✓ Transcriber loaded SARVAM_API_KEY: {TRANSCRIBER_KEY[:8]}...{TRANSCRIBER_KEY[-4:]}")
    else:
        print("✗ Transcriber SARVAM_API_KEY is None or empty!")
except ImportError as e:
    print(f"✗ Failed to import transcriber: {e}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)

issues = []
if not mistral_key:
    issues.append("MISTRAL_API_KEY not set")
elif mistral_key.startswith('"'):
    issues.append("MISTRAL_API_KEY has quotes")

if not sarvam_key:
    issues.append("SARVAM_API_KEY not set")
elif sarvam_key.startswith('"'):
    issues.append("SARVAM_API_KEY has quotes")

if not sarvam_model:
    issues.append("SARVAM_STT_MODEL not set")
elif sarvam_model.startswith('"'):
    issues.append("SARVAM_STT_MODEL has quotes")

if issues:
    print("✗ Issues found:")
    for issue in issues:
        print(f"  - {issue}")
    print("\nFix: Remove quotes from values in .env file")
    print("Example:")
    print("  Wrong: SARVAM_API_KEY=\"sk_xyz...\"")
    print("  Right: SARVAM_API_KEY=sk_xyz...")
else:
    print("✓ All environment variables loaded correctly!")
    print("\nYou can now:")
    print("  1. Restart backend: start.bat")
    print("  2. Test Hinglish transcription")

print("=" * 80)
