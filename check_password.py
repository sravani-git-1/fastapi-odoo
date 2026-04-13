#!/usr/bin/env python3
"""
Check what's actually in config.json
"""
import json

print("\n" + "="*60)
print("CHECKING CONFIG.JSON")
print("="*60 + "\n")

try:
    with open("config.json", "r") as f:
        content = f.read()
        print("Raw file content:")
        print(content)
        print()
        
        config = json.loads(content)
        
        print("Parsed values:")
        print(f"  ODOO_URL: {config.get('ODOO_URL')}")
        print(f"  ODOO_DB: {config.get('ODOO_DB')}")
        print(f"  ODOO_USERNAME: {config.get('ODOO_USERNAME')}")
        
        password = config.get('ODOO_PASSWORD')
        print(f"\n  ODOO_PASSWORD analysis:")
        print(f"    Full value: {password}")
        print(f"    Length: {len(password)}")
        print(f"    Character breakdown:")
        for i, char in enumerate(password, 1):
            print(f"      {i}: '{char}' (ASCII: {ord(char)})")
        
        print()
        
        # Expected password
        expected = "P@$$W0rd&$@"
        print(f"  Expected password: {expected}")
        print(f"  Expected length: {len(expected)}")
        
        if password == expected:
            print(f"  ✅ PASSWORD MATCHES EXPECTED!")
        else:
            print(f"  ❌ PASSWORD DOES NOT MATCH!")
            print(f"     Current:  '{password}'")
            print(f"     Expected: '{expected}'")
            
except FileNotFoundError:
    print("❌ config.json not found!")
except json.JSONDecodeError as e:
    print(f"❌ config.json is invalid JSON: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
