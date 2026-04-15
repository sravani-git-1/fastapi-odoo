from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from odoo_service import OdooService

app = FastAPI()
odoo_service = OdooService()


# ---------------- REQUEST MODEL ----------------
class RequestModel(BaseModel):
    action: str
    id: Optional[int] = None
    query: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None


@app.get("/")
def home():
    return {"message": "API running"}


# ---------------- CUSTOMERS ----------------
@app.post("/customers")
def customers(data: RequestModel):
    try:
        if data.action == "create":
            return odoo_service.create_customer(data.dict())

        elif data.action == "list":
            return odoo_service.get_customers()

        elif data.action == "read":
            if data.id:
                return odoo_service.get_customer_by_id(data.id)
            if data.query:
                return odoo_service.search_customers(data.query)
            raise HTTPException(400, "Provide id or query")

        elif data.action == "update":
            if not data.id:
                raise HTTPException(400, "id required")

            update_data = data.dict(exclude_none=True)
            update_data.pop("action", None)
            update_data.pop("id", None)

            return odoo_service.update_partner(data.id, update_data)

        elif data.action == "delete":
            if not data.id:
                raise HTTPException(400, "id required")

            return odoo_service.delete_customer(data.id)

        else:
            raise HTTPException(400, "Invalid action")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------- VENDORS ----------------
@app.post("/vendors")
def vendors(data: RequestModel):
    try:
        if data.action == "create":
            return odoo_service.create_vendor(data.dict())

        elif data.action == "list":
            return odoo_service.get_vendors()

        elif data.action == "read":
            if data.id:
                return odoo_service.get_vendor_by_id(data.id)
            if data.query:
                return odoo_service.search_vendors(data.query)
            raise HTTPException(400, "Provide id or query")

        elif data.action == "update":
            if not data.id:
                raise HTTPException(400, "id required")

            update_data = data.dict(exclude_none=True)
            update_data.pop("action", None)
            update_data.pop("id", None)

            return odoo_service.update_partner(data.id, update_data)

        elif data.action == "delete":
            if not data.id:
                raise HTTPException(400, "id required")

            return odoo_service.delete_vendor(data.id)

        else:
            raise HTTPException(400, "Invalid action")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))