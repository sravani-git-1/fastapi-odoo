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
    
    print(f"\n{'='*60}")
    print(f"CONFIG LOADING CHECK")
    print(f"{'='*60}")
    print(f"Checking environment variables...")
    print(f"  ODOO_URL env: {'SET' if url else 'NOT SET'}")
    print(f"  ODOO_DB env: {'SET' if db else 'NOT SET'}")
    print(f"  ODOO_USERNAME env: {'SET' if username else 'NOT SET'}")
    print(f"  ODOO_PASSWORD env: {'SET' if password else 'NOT SET'}")
    
    if url and db and username and password:
        print(f"\n✅ All environment variables are set!")
        return {"url": url, "db": db, "username": username, "password": password, "source": "env"}
    
    # Try config.json
    print(f"\nChecking config.json...")
    try:
        with open("config.json", "r") as f:
            config_text = f.read()
            print(f"  ✅ config.json found")
            print(f"  Content preview: {config_text[:100]}...")
            
            config = json.loads(config_text)
            result = {
                "url": (config.get("ODOO_URL") or "").strip(),
                "db": (config.get("ODOO_DB") or "").strip(),
                "username": (config.get("ODOO_USERNAME") or "").strip(),
                "password": (config.get("ODOO_PASSWORD") or "").strip(),
                "source": "config.json"
            }
            
            if all(result.values()):
                print(f"  ✅ All keys present and have values")
                return result
            else:
                missing = [k for k, v in result.items() if not v]
                print(f"  ❌ Missing or empty keys: {missing}")
                return None
    except FileNotFoundError:
        print(f"  ❌ config.json not found")
    except json.JSONDecodeError as e:
        print(f"  ❌ config.json is not valid JSON: {e}")
    except Exception as e:
        print(f"  ❌ Error reading config.json: {e}")
    
    return None

def test_connection():
    """Test Odoo connection"""
    print(f"\n{'='*60}")
    print(f"ODOO CONNECTION DIAGNOSTIC TOOL")
    print(f"{'='*60}\n")
    
    # Load config
    config = load_config()
    if not config or not all(config.values()):
        print(f"\n❌ FAILED: No valid configuration found")
        print(f"Please create config.json with Odoo credentials or set environment variables")
        return False
    
    url = config["url"].rstrip("/")
    db = config["db"]
    username = config["username"]
    password = config["password"]
    
    print(f"\n{'='*60}")
    print(f"LOADED CONFIGURATION:")
    print(f"{'='*60}")
    print(f"  Source: {config['source']}")
    print(f"  URL: {url}")
    print(f"  Database: {db}")
    print(f"  Username: {username}")
    print(f"  Password length: {len(password)} characters")
    print(f"  Password preview: {password[:3]}***{password[-3:] if len(password) > 6 else ''}")
    print()
    
    # Test 1: URL is accessible
    print(f"{'='*60}")
    print(f"TEST 1: Testing if Odoo URL is accessible")
    print(f"{'='*60}")
    try:
        import urllib.request
        response = urllib.request.urlopen(url, timeout=5)
        print(f"✅ SUCCESS: Odoo URL is accessible (HTTP {response.status})")
    except Exception as e:
        print(f"❌ FAILED: Cannot reach Odoo at {url}")
        print(f"   Error: {e}")
        print(f"   This means the URL is wrong or Odoo is down")
        return False
    
    print()
    
    # Test 2: Connect to XML-RPC common service
    print(f"{'='*60}")
    print(f"TEST 2: Testing XML-RPC connection")
    print(f"{'='*60}")
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        version = common.version()
        print(f"✅ SUCCESS: Connected to Odoo XML-RPC")
        print(f"   Odoo Version: {version.get('version_info', version.get('server_version', 'Unknown'))}")
    except Exception as e:
        print(f"❌ FAILED: Cannot connect to XML-RPC common service")
        print(f"   Error: {e}")
        return False
    
    print()
    
    # Test 3: Authenticate
    print(f"{'='*60}")
    print(f"TEST 3: Testing authentication")
    print(f"{'='*60}")
    print(f"Attempting: common.authenticate('{db}', '{username}', '***', {{}})")
    
    try:
        uid = common.authenticate(db, username, password, {})
        print(f"Raw response from authenticate(): {uid}")
        print(f"Response type: {type(uid).__name__}")
        
        if uid and uid != 0 and uid != False:
            print(f"✅ SUCCESS: Authentication successful")
            print(f"   User ID: {uid}")
        else:
            print(f"❌ FAILED: Authentication returned invalid UID: {uid}")
            print()
            print(f"This means one of these is wrong:")
            print(f"   1. Database name: '{db}' doesn't exist in {url}")
            print(f"   2. Username: '{username}' doesn't exist in database '{db}'")
            print(f"   3. Password: '***' is incorrect for user '{username}'")
            print()
            print(f"HOW TO FIX:")
            print(f"   1. Verify database '{db}' exists in Odoo")
            print(f"   2. Verify user '{username}' exists in that database")
            print(f"   3. Verify password is correct (check for typos and special characters)")
            print(f"   4. Make sure user is ACTIVE (not deactivated)")
            return False
    except Exception as e:
        print(f"❌ EXCEPTION during authentication:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {e}")
        print()
        if "xmlrpc" in str(e).lower():
            print(f"This is an XML-RPC protocol error")
        else:
            print(f"This might be a network or Odoo error")
        return False
    
    print()
    
    # Test 4: Connect to models and check partner
    print(f"{'='*60}")
    print(f"TEST 4: Testing if res.partner model is accessible")
    print(f"{'='*60}")
    try:
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        partner_ids = models.execute_kw(db, uid, password, "res.partner", "search", [[["customer_rank", ">", 0]]], {"limit": 1})
        print(f"✅ SUCCESS: res.partner model is accessible")
        print(f"   Found {len(partner_ids)} customers")
    except Exception as e:
        print(f"❌ FAILED: Cannot access res.partner model")
        print(f"   Error: {e}")
        return False
    
    print()
    print(f"{'='*60}")
    print(f"✅ ALL TESTS PASSED!")
    print(f"{'='*60}")
    print(f"\nYour configuration is correct and working!")
    print(f"You can now safely deploy to Render with these credentials.")
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
