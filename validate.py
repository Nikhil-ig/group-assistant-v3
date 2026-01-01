#!/usr/bin/env python3
"""
V3 Bot - Import Validation Script

This script validates that all modules can be imported without errors.
Run this before starting the bot to catch configuration issues.

Usage:
    python validate.py
"""

import sys
import os

# Add parent directory to path to make imports work as packages
v3_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(v3_dir)
sys.path.insert(0, parent_dir)

print("=" * 70)
print(" V3 TELEGRAM BOT - IMPORT VALIDATION")
print("=" * 70)

# Track import results
results = []

def test_import(module_name, description):
    """Test importing a module and track results."""
    try:
        __import__(module_name)
        print(f"✅ {description:<50} {module_name}")
        results.append((True, description))
        return True
    except Exception as e:
        print(f"❌ {description:<50} {module_name}")
        print(f"   Error: {str(e)}")
        results.append((False, description))
        return False

print("\n📦 TESTING IMPORTS:\n")

# Test core dependencies
test_import("telegram", "Telegram library")
test_import("fastapi", "FastAPI framework")
test_import("motor", "Async MongoDB driver")
test_import("pydantic", "Pydantic validation")
test_import("jwt", "JWT authentication")
test_import("uvicorn", "Uvicorn server")
test_import("dotenv", "Python dotenv")

print("\n🔧 TESTING OUR MODULES:\n")

# Change to v3 directory for relative imports
os.chdir(v3_dir)

# Test our modules (with v3 prefix since we're in parent directory)
test_import("v3.config.settings", "Configuration module")
test_import("v3.services.database", "Database service")
test_import("v3.services.auth", "Auth service")
test_import("v3.bot.handlers", "Bot handlers")
test_import("v3.api.endpoints", "API endpoints")
test_import("v3.core.models", "Core models")
test_import("v3.utils.helpers", "Utility helpers")

print("\n" + "=" * 70)

# Summary
passed = sum(1 for ok, _ in results if ok)
total = len(results)

print(f"\n✅ PASSED: {passed}/{total}")

if passed == total:
    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    print("\nYou can now run: python main.py")
    sys.exit(0)
else:
    print(f"\n⚠️  FAILED: {total - passed} imports failed")
    print("\nPlease fix the errors above before running the bot")
    sys.exit(1)
