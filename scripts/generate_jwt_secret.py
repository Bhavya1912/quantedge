#!/usr/bin/env python3
"""
Generate a secure JWT secret for production use.
Run this locally to get a strong random string.
"""
import secrets

# Generate 32 bytes of random data and encode as hex
secret = secrets.token_hex(16)  # 32 hex characters = 16 bytes

print("=" * 60)
print("🔐 GENERATED JWT SECRET (Use in Render Environment)")
print("=" * 60)
print(f"\nJWT_SECRET = {secret}\n")
print("⚠️  Copy this value to Render Dashboard:")
print("   quantedge-backend → Environment → JWT_SECRET")
print("\n" + "=" * 60)
