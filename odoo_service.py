import os
import xmlrpc.client
from fastapi import HTTPException


class OdooService:
    def __init__(self):
        self.url = os.getenv("ODOO_URL")
        self.db = os.getenv("ODOO_DB")
        self.username = os.getenv("ODOO_USERNAME")
        self.password = os.getenv("ODOO_PASSWORD")

        # ✅ Safe check (no crash)
        self.is_configured = all([
            self.url,
            self.db,
            self.username,
            self.password
        ])

        if self.is_configured:
            self.url = self.url.rstrip("/")
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        else:
            self.common = None
            self.models = None

    # ---------------- AUTH ----------------
    def authenticate(self):
        if not self.is_configured:
            raise HTTPException(
                status_code=500,
                detail="Odoo not configured (set env vars in Render)"
            )

        uid = self.common.authenticate(
            self.db,
            self.username,
            self.password,
            {}
        )

        if not uid:
            raise HTTPException(status_code=401, detail="Odoo auth failed")

        return uid

    # ---------------- CREATE ----------------
    def create_partner(self, data, role="customer"):
        uid = self.authenticate()

        partner_data = {
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "mobile": data.get("mobile"),
        }

        if role == "customer":
            partner_data["customer_rank"] = 1
        elif role == "vendor":
            partner_data["supplier_rank"] = 1

        partner_data = {k: v for k, v in partner_data.items() if v}

        partner_id = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "create",
            [partner_data]
        )

        return {"id": partner_id, "message": f"{role} created"}

    def create_customer(self, data):
        return self.create_partner(data, "customer")

    def create_vendor(self, data):
        return self.create_partner(data, "vendor")

    # ---------------- LIST ----------------
    def get_customers(self):
        uid = self.authenticate()

        ids = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "search",
            [[["customer_rank", ">", 0]]]
        )

        return self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "read",
            [ids]
        )

    def get_vendors(self):
        uid = self.authenticate()

        ids = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "search",
            [[["supplier_rank", ">", 0]]]
        )

        return self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "read",
            [ids]
        )

    # ---------------- READ ----------------
    def get_customer_by_id(self, id):
        return self._get_by_id(id)

    def get_vendor_by_id(self, id):
        return self._get_by_id(id)

    def _get_by_id(self, id):
        uid = self.authenticate()

        result = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "read",
            [[id]]
        )

        if not result:
            raise HTTPException(status_code=404, detail="Not found")

        return result

    # ---------------- SEARCH ----------------
    def search_customers(self, query):
        return self._search(query)

    def search_vendors(self, query):
        return self._search(query)

    def _search(self, query):
        uid = self.authenticate()

        ids = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "search",
            [[["name", "ilike", query]]]
        )

        return self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "read",
            [ids]
        )

    # ---------------- UPDATE ----------------
    def update_partner(self, id, data):
        uid = self.authenticate()

        result = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "write",
            [[id], data]
        )

        if not result:
            raise HTTPException(status_code=400, detail="Update failed")

        return {"message": "Updated successfully"}

    # ---------------- DELETE ----------------
    def delete_customer(self, id):
        return self._delete(id)

    def delete_vendor(self, id):
        return self._delete(id)

    def _delete(self, id):
        uid = self.authenticate()

        result = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "unlink",
            [[id]]
        )

        if not result:
            raise HTTPException(status_code=400, detail="Delete failed")

        return {"message": "Deleted successfully"}