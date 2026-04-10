import os
import xmlrpc.client
from pathlib import Path
from fastapi import HTTPException
import json
import sys

# -----------------------
# Config Loading with Fallback
# -----------------------

def load_config():
    """
    Load configuration with multiple fallbacks:
    1. Load from config.json (preferred for Render - no special char issues)
    2. Try environment variables (with validation)
    3. If corrupted, raise clear error
    """
    
    config = {
        "ODOO_URL": "",
        "ODOO_DB": "",
        "ODOO_USERNAME": "",
        "ODOO_PASSWORD": "",
    }
    
    config_file = Path(__file__).parent / "config.json"
    env_vars = os.environ
    
    print("\n" + "="*80)
    print("[INFO] CONFIGURATION LOADING")
    print("="*80)
    print(f"Script location: {Path(__file__).parent}")
    print(f"Config file path: {config_file}")
    print(f"Config file exists: {config_file.exists()}")
    print(f"Running on Render: {os.getenv('RENDER') == 'true'}")
    print()
    
    # STEP 1: Try loading from config.json
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
                print("✅ Loaded from config.json")
                print(f"   - ODOO_URL: {config['ODOO_URL'][:40]}...")
                print(f"   - ODOO_DB: {config['ODOO_DB']}")
                print(f"   - ODOO_USERNAME: {config['ODOO_USERNAME']}")
                print(f"   - ODOO_PASSWORD: {'*' * 8} (length: {len(config['ODOO_PASSWORD'])})")
                print("="*80 + "\n")
                return config
        except Exception as e:
            print(f"❌ Failed to load config.json: {e}")
            sys.exit(1)
    
    # STEP 2: Fall back to environment variables
    print("⚠️  config.json NOT found, trying environment variables...")
    config["ODOO_URL"] = os.getenv("ODOO_URL", "").strip()
    config["ODOO_DB"] = os.getenv("ODOO_DB", "").strip()
    config["ODOO_USERNAME"] = os.getenv("ODOO_USERNAME", "").strip()
    config["ODOO_PASSWORD"] = os.getenv("ODOO_PASSWORD", "").strip()
    
    print(f"   - ODOO_URL from env: {config['ODOO_URL'][:40] if config['ODOO_URL'] else 'EMPTY'}...")
    print(f"   - ODOO_DB from env: {config['ODOO_DB']}")
    print(f"   - ODOO_USERNAME from env: {config['ODOO_USERNAME']}")
    print(f"   - ODOO_PASSWORD from env: {'*' * 8 if config['ODOO_PASSWORD'] else 'EMPTY'}")
    
    # STEP 3: Check if environment variables are corrupted
    if config["ODOO_DB"] and ("@" in config["ODOO_DB"] or "&" in config["ODOO_DB"] or "$" in config["ODOO_DB"]):
        print(f"\n❌ ENVIRONMENT VARIABLES CORRUPTED!")
        print(f"   ODOO_DB contains special chars (got: {config['ODOO_DB']})")
        print(f"   This suggests password leaked into DB field!")
        sys.exit(1)
    
    # STEP 4: Try .env file (local dev)
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            print(f"\n📄 Loading from .env file...")
            load_dotenv(dotenv_path=env_path, override=True)
            config["ODOO_URL"] = os.getenv("ODOO_URL", config["ODOO_URL"]).strip()
            config["ODOO_DB"] = os.getenv("ODOO_DB", config["ODOO_DB"]).strip()
            config["ODOO_USERNAME"] = os.getenv("ODOO_USERNAME", config["ODOO_USERNAME"]).strip()
            config["ODOO_PASSWORD"] = os.getenv("ODOO_PASSWORD", config["ODOO_PASSWORD"]).strip()
            print("✅ Loaded from .env file")
    except:
        pass
    
    print("="*80 + "\n")
    return config

# Load configuration
try:
    config = load_config()
except SystemExit as e:
    print("\n" + "!"*80)
    print("FATAL: Could not load configuration. Please check above for errors.")
    print("!"*80)
    raise

# -----------------------
# Config Variables
# -----------------------
ODOO_URL = config["ODOO_URL"]
ODOO_DB = config["ODOO_DB"]
ODOO_USERNAME = config["ODOO_USERNAME"]
ODOO_PASSWORD = config["ODOO_PASSWORD"]

# -----------------------
# VALIDATION
# -----------------------
errors = []
if not ODOO_URL or ODOO_URL == "https://your-instance.odoo.com":
    errors.append("ODOO_URL is empty or default")
if not ODOO_DB or ODOO_DB == "your_database_name":
    errors.append("ODOO_DB is empty or default")
if not ODOO_USERNAME or ODOO_USERNAME == "your_email@example.com":
    errors.append("ODOO_USERNAME is empty or default")
if not ODOO_PASSWORD or ODOO_PASSWORD == "your_api_key_or_password":
    errors.append("ODOO_PASSWORD is empty or default")

if errors:
    error_msg = f"""
╔════════════════════════════════════════════════════════════════╗
║          ❌  MISSING OR INVALID CONFIGURATION  ❌              ║
╚════════════════════════════════════════════════════════════════╝

ERRORS:
  {chr(10).join(f'  - {e}' for e in errors)}

SOLUTION FOR RENDER DEPLOYMENT:
═══════════════════════════════
  1. Make sure config.json exists in your repository:
     {{
       "ODOO_URL": "https://odoo.avowaldatasystems.in/",
       "ODOO_DB": "odooKmmDb",
       "ODOO_USERNAME": "rajugenai@gmail.com",
       "ODOO_PASSWORD": "P@$$W0rd&$@"
     }}

  2. Commit and push it to git
  3. Redeploy on Render

SOLUTION FOR LOCAL DEVELOPMENT:
════════════════════════════════
  1. Create .env in project root:
     ODOO_URL=https://odoo.avowaldatasystems.in/
     ODOO_DB=odooKmmDb
     ODOO_USERNAME=rajugenai@gmail.com
     ODOO_PASSWORD=P@$$W0rd&$@

  2. Run: uvicorn main:app --reload

WARNING: NEVER commit credentials to git!
"""
    print(error_msg)
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