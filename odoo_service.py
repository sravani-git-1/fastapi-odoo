import os
import json
import xmlrpc.client
from fastapi import HTTPException

# Optional: load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

# -----------------------
# Config
# -----------------------
def load_config():
    """Load config from env variables, .env file, or config.json"""
    config = {
        "ODOO_URL": os.getenv("ODOO_URL"),
        "ODOO_DB": os.getenv("ODOO_DB"),
        "ODOO_USERNAME": os.getenv("ODOO_USERNAME"),
        "ODOO_PASSWORD": os.getenv("ODOO_PASSWORD"),
    }
    
    # If any config is missing, try to load from config.json
    if not all(config.values()):
        try:
            with open("config.json", "r") as f:
                json_config = json.load(f)
                for key in config:
                    if not config[key]:
                        config[key] = json_config.get(key)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    # Use defaults if still missing
    defaults = {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DB": "your_database_name",
        "ODOO_USERNAME": "your_email@example.com",
        "ODOO_PASSWORD": "your_api_key_or_password"
    }
    
    for key in config:
        if not config[key]:
            config[key] = defaults[key]
    
    return config

config = load_config()
ODOO_URL = config["ODOO_URL"]
ODOO_DB = config["ODOO_DB"]
ODOO_USERNAME = config["ODOO_USERNAME"]
ODOO_PASSWORD = config["ODOO_PASSWORD"]


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

            return uid

        except HTTPException:
            raise
        except Exception as exc:
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
                        "vat",
                        "customer_rank",
                        "supplier_rank"
                    ]
                },
            )

            # Add a computed 'role' field to each partner based on their ranks
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

            # Verify creation was successful
            if not partner_id or partner_id <= 0:
                raise HTTPException(
                    status_code=502,
                    detail="Failed to create partner: Invalid ID returned"
                )

            # Verify partner exists by reading it
            verify_creation = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "read",
                [partner_id],
                {"fields": ["id", "name", "customer_rank", "supplier_rank"]}
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

            update_result = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "write",
                [[partner_id], update_data],
            )

            # Verify update was successful
            if not update_result:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to update partner {partner_id}: Write operation returned false"
                )

            # Read back updated values to verify changes were applied
            read_fields = ["id", "name", "customer_rank", "supplier_rank"] + [f for f in update_data.keys() if f not in ["customer_rank", "supplier_rank"]]
            updated_partner = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "read",
                [partner_id],
                {"fields": read_fields}
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
            # Verify partner exists before deletion
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

            # Attempt to delete
            result = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "unlink",
                [[partner_id]],
            )

            # Verify deletion was successful
            if not result:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to delete partner {partner_id}: Unlink operation returned false"
                )

            # Double-check partner no longer exists
            verify_deleted = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "search",
                [[["id", "=", partner_id]]],
                {"limit": 1},
            )

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