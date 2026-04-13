import os
import json
import sys
import xmlrpc.client
from fastapi import HTTPException

# Optional: load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

# -----------------------
# Config - Production Ready
# -----------------------
class Config:
    """Robust configuration management for local and production"""
    
    @staticmethod
    def get_from_env_or_file():
        """Load config with proper priority: env vars > config.json > error"""
        # Priority 1: Environment variables (production)
        url = os.getenv("ODOO_URL", "").strip()
        db = os.getenv("ODOO_DB", "").strip()
        username = os.getenv("ODOO_USERNAME", "").strip()
        password = os.getenv("ODOO_PASSWORD", "").strip()
        
        # If env vars are set, use them
        if url and db and username and password:
            return {
                "ODOO_URL": url,
                "ODOO_DB": db,
                "ODOO_USERNAME": username,
                "ODOO_PASSWORD": password,
                "source": "environment variables"
            }
        
        # Priority 2: config.json (development)
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    json_config = json.load(f)
                    # Validate all keys exist in config.json
                    if all(key in json_config for key in ["ODOO_URL", "ODOO_DB", "ODOO_USERNAME", "ODOO_PASSWORD"]):
                        return {
                            "ODOO_URL": json_config["ODOO_URL"].strip(),
                            "ODOO_DB": json_config["ODOO_DB"].strip(),
                            "ODOO_USERNAME": json_config["ODOO_USERNAME"].strip(),
                            "ODOO_PASSWORD": json_config["ODOO_PASSWORD"].strip(),
                            "source": "config.json"
                        }
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            pass
        
        # Priority 3: Raise error with instructions
        raise ValueError(
            "FATAL: No valid configuration found!\n"
            "For LOCAL development:\n"
            "  1. Create config.json in project root with Odoo credentials\n"
            "  2. Format: { \"ODOO_URL\": \"...\", \"ODOO_DB\": \"...\", \"ODOO_USERNAME\": \"...\", \"ODOO_PASSWORD\": \"...\" }\n"
            "For RENDER deployment:\n"
            "  1. Go to Service Settings > Environment\n"
            "  2. Add these 4 environment variables:\n"
            "     - ODOO_URL\n"
            "     - ODOO_DB\n"
            "     - ODOO_USERNAME\n"
            "     - ODOO_PASSWORD\n"
            "  3. Redeploy service"
        )

# Load configuration on startup
try:
    _config = Config.get_from_env_or_file()
    ODOO_URL = _config["ODOO_URL"]
    ODOO_DB = _config["ODOO_DB"]
    ODOO_USERNAME = _config["ODOO_USERNAME"]
    ODOO_PASSWORD = _config["ODOO_PASSWORD"]
except ValueError as e:
    print(f"\n{'='*60}\n{e}\n{'='*60}\n", file=sys.stderr)
    sys.exit(1)


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
        """Authenticate with Odoo and return user ID"""
        try:
            uid = self._common().authenticate(
                self.db,
                self.username,
                self.password,
                {}
            )

            if not uid:
                raise HTTPException(
                    status_code=401,
                    detail="Odoo authentication failed: Invalid credentials"
                )

            return uid

        except HTTPException:
            raise
        except Exception as exc:
            error_msg = str(exc)
            # Log full error for debugging
            import traceback
            full_traceback = traceback.format_exc()
            print(f"\n{'='*60}\nAUTH ERROR:\n{full_traceback}\n{'='*60}\n", file=sys.stderr)
            
            # Provide helpful error messages
            if "database" in error_msg.lower() and "does not exist" in error_msg.lower():
                raise HTTPException(
                    status_code=502,
                    detail=f"Odoo database '{self.db}' does not exist. Check ODOO_DB configuration."
                )
            elif "connection" in error_msg.lower():
                raise HTTPException(
                    status_code=502,
                    detail=f"Cannot connect to Odoo at {self.url}. Check ODOO_URL configuration and network connectivity."
                )
            elif "invalid credentials" in error_msg.lower() or "authenticate" in error_msg.lower():
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Odoo credentials. Check ODOO_USERNAME and ODOO_PASSWORD."
                )
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Odoo authentication error: {error_msg}"
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
            # Build domain based on role - use only valid Odoo fields
            if role == "vendor":
                domain = [["supplier_rank", ">", 0]]
            elif role == "all":
                domain = ['|', ["customer_rank", ">", 0], ["supplier_rank", ">", 0]]
            else:  # customer
                domain = [["customer_rank", ">", 0]]

            # Search for partner IDs
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
            except Exception as search_error:
                error_msg = str(search_error)
                print(f"\n{'='*60}\nSEARCH ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                
                if "Invalid field" in error_msg or "field" in error_msg.lower():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Odoo field error: The search field may not exist in your Odoo instance. Error: {error_msg}"
                    )
                else:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Odoo search error: {error_msg}"
                    )

            if not partner_ids:
                return []

            # Read partner data
            try:
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
                            "vat",
                            "customer_rank",
                            "supplier_rank"
                        ]
                    },
                )
            except Exception as read_error:
                error_msg = str(read_error)
                print(f"\n{'='*60}\nREAD ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(
                    status_code=502,
                    detail=f"Odoo read error: {error_msg}"
                )

            # Add computed fields
            for partner in partners:
                roles = []
                if partner.get("customer_rank", 0) > 0:
                    roles.append("customer")
                if partner.get("supplier_rank", 0) > 0:
                    roles.append("vendor")
                
                partner["roles"] = roles if roles else ["other"]
                partner["is_customer"] = partner.get("customer_rank", 0) > 0
                partner["is_vendor"] = partner.get("supplier_rank", 0) > 0

            return partners

        except HTTPException:
            raise
        except Exception as exc:
            error_msg = str(exc)
            print(f"\n{'='*60}\nGET PARTNERS ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
            raise HTTPException(
                status_code=502,
                detail=f"Odoo data retrieval error: {error_msg}"
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
                partner_data["supplier_rank"] = 0
            elif role == "vendor":
                partner_data["customer_rank"] = 0
                partner_data["supplier_rank"] = 1
            elif role == "all":
                partner_data["customer_rank"] = 1
                partner_data["supplier_rank"] = 1

            partner_data = {k: v for k, v in partner_data.items() if v is not None}

            print(f"DEBUG: Creating partner with data: {partner_data}", file=sys.stderr)

            try:
                partner_id = models.execute_kw(
                    self.db,
                    uid,
                    self.password,
                    "res.partner",
                    "create",
                    [partner_data],
                )
            except Exception as create_err:
                error_msg = str(create_err)
                print(f"\n{'='*60}\nCREATE ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(
                    status_code=502,
                    detail=f"Odoo create error: {error_msg}"
                )

            # Verify creation was successful
            if not partner_id or partner_id <= 0:
                raise HTTPException(
                    status_code=502,
                    detail="Failed to create partner: Invalid ID returned"
                )

            # Verify partner exists by reading it
            try:
                verify_creation = models.execute_kw(
                    self.db,
                    uid,
                    self.password,
                    "res.partner",
                    "read",
                    [partner_id],
                    {"fields": ["id", "name", "customer_rank", "supplier_rank"]}
                )
            except Exception as verify_err:
                error_msg = str(verify_err)
                print(f"\n{'='*60}\nVERIFY CREATE ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(
                    status_code=502,
                    detail=f"Creation verification failed: {error_msg}"
                )

            if not verify_creation:
                raise HTTPException(
                    status_code=502,
                    detail=f"Creation verification failed: Partner {partner_id} not found after creation"
                )

            # Compute roles
            created_partner = verify_creation[0]
            roles = []
            if created_partner.get("customer_rank", 0) > 0:
                roles.append("customer")
            if created_partner.get("supplier_rank", 0) > 0:
                roles.append("vendor")

            return {
                "message": "Partner created successfully",
                "id": partner_id,
                "data": partner_data,
                "roles": roles if roles else ["other"],
                "is_customer": created_partner.get("customer_rank", 0) > 0,
                "is_vendor": created_partner.get("supplier_rank", 0) > 0,
                "created": True
            }

        except HTTPException:
            raise
        except Exception as exc:
            error_msg = str(exc)
            print(f"\n{'='*60}\nCREATE PARTNER ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
            raise HTTPException(
                status_code=502,
                detail=f"Odoo create error: {error_msg}"
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
                    update_data["supplier_rank"] = 0
                elif role == "vendor":
                    update_data["customer_rank"] = 0
                    update_data["supplier_rank"] = 1
                elif role == "all":
                    update_data["customer_rank"] = 1
                    update_data["supplier_rank"] = 1

            print(f"DEBUG: Updating partner {partner_id} with data: {update_data}", file=sys.stderr)

            try:
                update_result = models.execute_kw(
                    self.db,
                    uid,
                    self.password,
                    "res.partner",
                    "write",
                    [[partner_id], update_data],
                )
            except Exception as update_err:
                error_msg = str(update_err)
                print(f"\n{'='*60}\nUPDATE ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(
                    status_code=502,
                    detail=f"Odoo update error: {error_msg}"
                )

            # Verify update was successful
            if not update_result:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to update partner {partner_id}: Write operation returned false"
                )

            # Read back updated values to verify changes were applied
            read_fields = ["id", "name", "customer_rank", "supplier_rank"] + [f for f in update_data.keys() if f not in ["customer_rank", "supplier_rank"]]
            try:
                updated_partner = models.execute_kw(
                    self.db,
                    uid,
                    self.password,
                    "res.partner",
                    "read",
                    [partner_id],
                    {"fields": read_fields}
                )
            except Exception as read_err:
                error_msg = str(read_err)
                print(f"\n{'='*60}\nVERIFY UPDATE ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(
                    status_code=502,
                    detail=f"Update verification failed: {error_msg}"
                )

            if not updated_partner:
                raise HTTPException(
                    status_code=502,
                    detail=f"Update verification failed: Partner {partner_id} not found after update"
                )

            # Compute roles
            partner_data = updated_partner[0]
            roles = []
            if partner_data.get("customer_rank", 0) > 0:
                roles.append("customer")
            if partner_data.get("supplier_rank", 0) > 0:
                roles.append("vendor")

            return {
                "message": f"Partner {partner_id} updated successfully",
                "updated_fields": update_data,
                "roles": roles if roles else ["other"],
                "is_customer": partner_data.get("customer_rank", 0) > 0,
                "is_vendor": partner_data.get("supplier_rank", 0) > 0,
                "updated": True,
                "verified_data": partner_data
            }

        except HTTPException:
            raise
        except Exception as exc:
            error_msg = str(exc)
            print(f"\n{'='*60}\nUPDATE PARTNER ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
            raise HTTPException(
                status_code=502,
                detail=f"Odoo update error: {error_msg}"
            )

    # -----------------------
    # DELETE partner
    # -----------------------
    def delete_partner(self, partner_id: int):
        uid = self.authenticate()
        models = self._models()

        try:
            # Verify partner exists before deletion
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
            except Exception as search_err:
                error_msg = str(search_err)
                print(f"\n{'='*60}\nDELETE SEARCH ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(status_code=502, detail=f"Search error: {error_msg}")

            if not existing:
                raise HTTPException(status_code=404, detail="Partner not found")

            # Attempt to delete
            print(f"DEBUG: Deleting partner {partner_id}", file=sys.stderr)
            try:
                result = models.execute_kw(
                    self.db,
                    uid,
                    self.password,
                    "res.partner",
                    "unlink",
                    [[partner_id]],
                )
            except Exception as delete_err:
                error_msg = str(delete_err)
                print(f"\n{'='*60}\nDELETE ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(status_code=502, detail=f"Odoo delete error: {error_msg}")

            # Verify deletion was successful
            if not result:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to delete partner {partner_id}: Unlink operation returned false"
                )

            # Double-check partner no longer exists
            try:
                verify_deleted = models.execute_kw(
                    self.db,
                    uid,
                    self.password,
                    "res.partner",
                    "search",
                    [[["id", "=", partner_id]]],
                    {"limit": 1},
                )
            except Exception as verify_err:
                error_msg = str(verify_err)
                print(f"\n{'='*60}\nDELETE VERIFY ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
                raise HTTPException(status_code=502, detail=f"Verification error: {error_msg}")

            if verify_deleted:
                raise HTTPException(
                    status_code=502,
                    detail=f"Deletion verification failed: Partner {partner_id} still exists"
                )

            return {
                "message": f"Partner {partner_id} deleted successfully",
                "deleted": True
            }

        except HTTPException:
            raise
        except Exception as exc:
            error_msg = str(exc)
            print(f"\n{'='*60}\nDELETE PARTNER ERROR:\n{error_msg}\n{'='*60}\n", file=sys.stderr)
            raise HTTPException(
                status_code=502,
                detail=f"Odoo delete error: {error_msg}"
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