#!/usr/bin/env python3
"""
Odoo Connection Diagnostic Tool
This script tests if your Odoo instance is accessible and credentials are valid
Run this locally first before deploying to Render
"""

import os
import json
import xmlrpc.client
import sys

def load_config():
    """Load config from environment or config.json"""
    # Try env vars first
    url = (os.getenv("ODOO_URL") or "").strip()
    db = (os.getenv("ODOO_DB") or "").strip()
    username = (os.getenv("ODOO_USERNAME") or "").strip()
    password = (os.getenv("ODOO_PASSWORD") or "").strip()
    
    if url and db and username and password:
        return {"url": url, "db": db, "username": username, "password": password}
    
    # Try config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return {
                "url": config.get("ODOO_URL", "").strip(),
                "db": config.get("ODOO_DB", "").strip(),
                "username": config.get("ODOO_USERNAME", "").strip(),
                "password": config.get("ODOO_PASSWORD", "").strip(),
            }
    except:
        return None

def test_connection():
    """Test Odoo connection"""
    print("\n" + "="*60)
    print("ODOO CONNECTION DIAGNOSTIC TOOL")
    print("="*60 + "\n")
    
    # Load config
    config = load_config()
    if not config or not all(config.values()):
        print("❌ FAILED: No valid configuration found")
        print("   Please create config.json with Odoo credentials or set environment variables")
        return False
    
    url = config["url"].rstrip("/")
    db = config["db"]
    username = config["username"]
    password = config["password"]
    
    print("Configuration Loaded:")
    print(f"  URL: {url}")
    print(f"  Database: {db}")
    print(f"  Username: {username}")
    print(f"  Password length: {len(password)} chars")
    print()
    
    # Test 1: URL is accessible
    print("TEST 1: Testing if Odoo URL is accessible...")
    try:
        import urllib.request
        response = urllib.request.urlopen(url, timeout=5)
        print(f"  ✅ SUCCESS: Odoo URL is accessible (HTTP {response.status})")
    except Exception as e:
        print(f"  ❌ FAILED: Cannot reach Odoo at {url}")
        print(f"     Error: {e}")
        return False
    
    print()
    
    # Test 2: Connect to XML-RPC common service
    print("TEST 2: Testing XML-RPC connection to common service...")
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        version = common.version()
        print(f"  ✅ SUCCESS: Connected to Odoo XML-RPC")
        print(f"     Odoo Version: {version.get('version_info', 'Unknown')}")
    except Exception as e:
        print(f"  ❌ FAILED: Cannot connect to XML-RPC common service")
        print(f"     Error: {e}")
        return False
    
    print()
    
    # Test 3: Authenticate
    print("TEST 3: Testing authentication...")
    try:
        uid = common.authenticate(db, username, password, {})
        if uid:
            print(f"  ✅ SUCCESS: Authentication successful")
            print(f"     User ID: {uid}")
        else:
            print(f"  ❌ FAILED: Authentication returned empty UID")
            print(f"     Likely cause: Invalid credentials")
            print(f"     Database: {db}")
            print(f"     Username: {username}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Authentication error")
        print(f"     Error: {e}")
        return False
    
    print()
    
    # Test 4: Connect to models and check partner
    print("TEST 4: Testing if res.partner model is accessible...")
    try:
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        partner_ids = models.execute_kw(db, uid, password, "res.partner", "search", [[["customer_rank", ">", 0]]], {"limit": 1})
        print(f"  ✅ SUCCESS: res.partner model is accessible")
        print(f"     Found {len(partner_ids)} customers")
    except Exception as e:
        print(f"  ❌ FAILED: Cannot access res.partner model")
        print(f"     Error: {e}")
        return False
    
    print()
    print("="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour configuration is correct and working!")
    print("You can now deploy with confidence to Render.")
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
