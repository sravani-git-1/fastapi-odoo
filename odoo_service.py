import os
import xmlrpc.client
from pathlib import Path
from urllib.parse import quote
from fastapi import HTTPException
import json

# -----------------------
# Config Loading with Fallback
# -----------------------

def load_config():
    """
    Load configuration with multiple fallbacks:
    1. Try environment variables first
    2. If they look corrupted, try loading from config.json
    3. If Render is detected, use special handling
    """
    
    # Try to load from environment
    config = {
        "ODOO_URL": os.getenv("ODOO_URL", "").strip(),
        "ODOO_DB": os.getenv("ODOO_DB", "").strip(),
        "ODOO_USERNAME": os.getenv("ODOO_USERNAME", "").strip(),
        "ODOO_PASSWORD": os.getenv("ODOO_PASSWORD", "").strip(),
    }
    
    # Check if running on Render
    is_render = os.getenv("RENDER") == "true"
    
    # Detect if variables are corrupted (e.g., password value in DB field)
    is_corrupted = config["ODOO_DB"] and ("@" in config["ODOO_DB"] or "&" in config["ODOO_DB"])
    
    print("\n" + "="*70)
    print("[INFO] Configuration Loading:")
    print("="*70)
    print(f"Running on Render: {is_render}")
    print(f"Env vars corrupted: {is_corrupted}")
    print(f"ODOO_DB value: {repr(config['ODOO_DB'][:30] if config['ODOO_DB'] else 'empty')}")
    
    # If corrupted, try loading from config file
    if is_corrupted or not all(config.values()):
        config_file = Path(__file__).parent / "config.json"
        if config_file.exists():
            print(f"⚠️  Environment variables corrupted, loading from {config_file}")
            try:
                with open(config_file) as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    print("✅ Config loaded from file successfully")
            except Exception as e:
                print(f"❌ Failed to load config.json: {e}")
        else:
            print(f"⚠️  config.json not found at {config_file}")
    
    # Load .env as final fallback (local development)
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            print(f"✅ Loaded .env from {env_path}")
    except:
        pass
    
    print("="*70 + "\n")
    return config

# Load configuration
config = load_config()

# -----------------------
# Config Variables
# -----------------------
ODOO_URL = config["ODOO_URL"] or os.getenv("ODOO_URL", "https://your-instance.odoo.com")
ODOO_DB = config["ODOO_DB"] or os.getenv("ODOO_DB", "your_database_name")
ODOO_USERNAME = config["ODOO_USERNAME"] or os.getenv("ODOO_USERNAME", "your_email@example.com")
ODOO_PASSWORD = config["ODOO_PASSWORD"] or os.getenv("ODOO_PASSWORD", "your_api_key_or_password")

# Debug logging
print("[DEBUG] Final Configuration:")
print(f"  ODOO_URL       : {ODOO_URL[:50]}..." if len(ODOO_URL) > 50 else f"  ODOO_URL       : {ODOO_URL}")
print(f"  ODOO_DB        : {ODOO_DB}")
print(f"  ODOO_USERNAME  : {ODOO_USERNAME}")
print(f"  ODOO_PASSWORD  : {'*' * min(10, len(ODOO_PASSWORD))}")

# Validate credentials are loaded
errors = []
if not ODOO_URL or ODOO_URL == "https://your-instance.odoo.com":
    errors.append("ODOO_URL")
if not ODOO_DB or ODOO_DB == "your_database_name":
    errors.append("ODOO_DB")
if not ODOO_USERNAME or ODOO_USERNAME == "your_email@example.com":
    errors.append("ODOO_USERNAME")
if not ODOO_PASSWORD or ODOO_PASSWORD == "your_api_key_or_password":
    errors.append("ODOO_PASSWORD")

if errors:
    error_msg = f"""
❌ MISSING CONFIGURATION!

The following variables are not set:
  - {', '.join(errors)}

SOLUTIONS:

On Render:
  1. Add a 'config.json' file to your repository with:
     {{
       "ODOO_URL": "your-url",
       "ODOO_DB": "your-db",
       "ODOO_USERNAME": "your-email",
       "ODOO_PASSWORD": "your-password"
     }}
  
  2. Or set these environment variables (with special chars properly quoted):
     ODOO_URL="https://..."
     ODOO_DB="dbname"
     ODOO_USERNAME="email@example.com"
     ODOO_PASSWORD="password"

Locally:
  1. Create a .env file with the same variables
  2. Run: python -m uvicorn main:app --reload
"""
    raise ValueError(error_msg)


class OdooService:
    def __init__(self):
        self.url = ODOO_URL.rstrip("/")
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD

        # Cache proxies
        self._common_proxy = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self._models_proxy = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    # -----------------------
    # Internal helpers
    # -----------------------
    def _common(self):
        return self._common_proxy

    def _models(self):
        return self._models_proxy

    # -----------------------
    # Authentication
    # -----------------------
    def authenticate(self):
        try:
            print(f"[DEBUG] Authenticating with:")
            print(f"  URL: {self.url}")
            print(f"  DB: {self.db}")
            print(f"  Username: {self.username}")
            
            uid = self._common().authenticate(
                self.db,
                self.username,
                self.password,
                {}
            )

            if not uid:
                raise HTTPException(
                    status_code=401,
                    detail="Odoo authentication failed"
                )

            print(f"[DEBUG] ✅ Authentication successful! UID: {uid}")
            return uid

        except HTTPException:
            raise
        except Exception as exc:
            print(f"[DEBUG] ❌ Authentication failed: {str(exc)}")
            raise HTTPException(
                status_code=502,
                detail=f"Odoo auth error: {str(exc)}"
            )

    # -----------------------
    # Normalize role
    # -----------------------
    def _normalize_role(self, role: str) -> str:
        role = role.strip().lower()

        if role.endswith("s") and role in ["customers", "vendors"]:
            role = role[:-1]

        if role not in ["customer", "vendor", "all"]:
            raise HTTPException(
                status_code=400,
                detail="role must be customer, vendor, or all"
            )

        return role

    # -----------------------
    # GET partners
    # -----------------------
    def get_partners(self, role: str = "customer", limit: int = 100):
        uid = self.authenticate()
        models = self._models()

        role = self._normalize_role(role)

        try:
            if role == "vendor":
                domains_to_try = [
                    [["supplier_rank", ">", 0]],
                    [["is_supplier", "=", True]],
                ]
            elif role == "all":
                domains_to_try = [
                    ['|', ['customer_rank', '>', 0], ['supplier_rank', '>', 0]],
                    ['|', ['is_customer', '=', True], ['is_supplier', '=', True]],
                ]
            else:
                domains_to_try = [
                    [["customer_rank", ">", 0]],
                    [["is_customer", "=", True]],
                ]

            partner_ids = []
            last_error = None

            for domain in domains_to_try:
                try:
                    partner_ids = models.execute_kw(
                        self.db,
                        uid,
                        self.password,
                        "res.partner",
                        "search",
                        [domain],
                        {"limit": limit},
                    )
                    if partner_ids:
                        break
                except Exception as exc:
                    last_error = exc

            if not partner_ids:
                if last_error:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Odoo search failed: {str(last_error)}"
                    )
                return []

            partners = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "read",
                [partner_ids],
                {
                    "fields": [
                        "id",
                        "name",
                        "email",
                        "phone",
                        "mobile",
                        "company_type",
                        "vat"
                    ]
                },
            )

            return partners

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Odoo data retrieval error: {str(exc)}"
            )

    # -----------------------
    # POST create partner
    # -----------------------
    def create_partner(self, data: dict):
        uid = self.authenticate()
        models = self._models()

        try:
            partner_data = {
                "name": data.get("name"),
                "email": data.get("email"),
                "phone": data.get("phone"),
                "mobile": data.get("mobile"),
                "company_type": data.get("company_type", "person"),
                "vat": data.get("vat"),
            }

            role = data.get("role", "customer").lower()

            if role == "customer":
                partner_data["customer_rank"] = 1
            elif role == "vendor":
                partner_data["supplier_rank"] = 1
            elif role == "all":
                partner_data["customer_rank"] = 1
                partner_data["supplier_rank"] = 1

            partner_data = {k: v for k, v in partner_data.items() if v is not None}

            partner_id = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "create",
                [partner_data],
            )

            return {
                "message": "Partner created successfully",
                "id": partner_id,
                "data": partner_data
            }

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Odoo create error: {str(exc)}"
            )

    # -----------------------
    # PUT update partner
    # -----------------------
    def update_partner(self, partner_id: int, data: dict):
        uid = self.authenticate()
        models = self._models()

        try:
            existing = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "search",
                [[["id", "=", partner_id]]],
                {"limit": 1},
            )

            if not existing:
                raise HTTPException(status_code=404, detail="Partner not found")

            update_data = {k: v for k, v in data.items() if v is not None}

            if not update_data:
                raise HTTPException(status_code=400, detail="No valid fields to update")

            role = update_data.pop("role", None)
            if role:
                role = role.lower()
                if role == "customer":
                    update_data["customer_rank"] = 1
                elif role == "vendor":
                    update_data["supplier_rank"] = 1
                elif role == "all":
                    update_data["customer_rank"] = 1
                    update_data["supplier_rank"] = 1

            models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "write",
                [[partner_id], update_data],
            )

            return {
                "message": f"Partner {partner_id} updated successfully",
                "updated_fields": update_data
            }

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Odoo update error: {str(exc)}"
            )

    # -----------------------
    # DELETE partner
    # -----------------------
    def delete_partner(self, partner_id: int):
        uid = self.authenticate()
        models = self._models()

        try:
            existing = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "search",
                [[["id", "=", partner_id]]],
                {"limit": 1},
            )

            if not existing:
                raise HTTPException(status_code=404, detail="Partner not found")

            models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "unlink",
                [[partner_id]],
            )

            return {
                "message": f"Partner {partner_id} deleted successfully"
            }

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Odoo delete error: {str(exc)}"
            )

    # -----------------------
    # Shortcuts
    # -----------------------
    def get_customers(self, limit: int = 100):
        return self.get_partners(role="customer", limit=limit)

    def get_vendors(self, limit: int = 100):
        return self.get_partners(role="vendor", limit=limit)

    # -----------------------
    # Verify auth
    # -----------------------
    def verify_auth(self):
        uid = self.authenticate()
        return {
            "authenticated": True,
            "uid": uid,
            "db": self.db,
            "user": self.username
        }