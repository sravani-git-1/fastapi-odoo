import xmlrpc.client
from fastapi import HTTPException


class OdooService:
    def __init__(self):
        # 🔥 YOUR DIRECT CREDENTIALS
        self.url = "https://odoo.avowaldatasystems.in"
        self.db = "odooKmmDb"
        self.username = "rajugenai@gmail.com"
        self.password = "Pa$$Word&$@"

        self.url = self.url.rstrip("/")

        self.common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", allow_none=True
        )
        self.models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )

    # ---------------- AUTH ----------------
    def authenticate(self):
        uid = self.common.authenticate(
            self.db,
            self.username,
            self.password,
            {}
        )

        if not uid:
            raise HTTPException(
                status_code=401,
                detail="Odoo auth failed"
            )

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
    def delete_partner(self, id):
        uid = self.authenticate()

        result = self.models.execute_kw(
            self.db, uid, self.password,
            "res.partner", "unlink",
            [[id]]
        )

        if not result:
            raise HTTPException(status_code=400, detail="Delete failed")

        return {"message": "Deleted successfully"}

    def delete_customer(self, id):
        return self.delete_partner(id)

    def delete_vendor(self, id):
        return self.delete_partner(id)