from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

from odoo_service import OdooService

app = FastAPI()

# -----------------------
# Odoo Service
# -----------------------
odoo_service = OdooService()

# -----------------------
# Pydantic Schemas
# -----------------------

class PartnerActionPayload(BaseModel):
    action: Literal["create", "read", "update", "delete", "list"]
    id: Optional[int] = None
    query: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company_type: Optional[Literal["person", "company"]] = None
    vat: Optional[str] = None
    role: Optional[Literal["customer", "vendor", "all"]] = None
    limit: Optional[int] = 100


# -----------------------
# Odoo APIs (Customers)
# -----------------------

@app.post("/customers")
async def customers(request: Request):
    raw_data = await request.json()
    clean_data = {k: v for k, v in raw_data.items() if v not in ["", None]}
    payload = PartnerActionPayload(**clean_data)

    action = payload.action

    try:
        if action == "create":
            partner_data = payload.dict(exclude_none=True)
            for key in ["action", "id", "query", "limit"]:
                partner_data.pop(key, None)

            partner_data["role"] = "customer"
            return odoo_service.create_customer(partner_data)

        elif action == "read":
            if payload.id is not None:
                return odoo_service.get_customer_by_id(payload.id)
            if payload.query:
                return odoo_service.search_customers(payload.query, limit=payload.limit or 100)
            raise HTTPException(status_code=400, detail="read requires either id or query")

        elif action == "update":
            if payload.id is None:
                raise HTTPException(status_code=400, detail="update requires id")

            update_data = payload.dict(exclude_none=True)
            for key in ["action", "id", "query", "limit"]:
                update_data.pop(key, None)

            if not update_data:
                raise HTTPException(status_code=400, detail="update requires at least one field")

            return odoo_service.update_partner(payload.id, update_data)

        elif action == "delete":
            if payload.id is None:
                raise HTTPException(status_code=400, detail="delete requires id")

            return odoo_service.delete_customer(payload.id)

        elif action == "list":
            return odoo_service.get_customers(limit=payload.limit or 100)

        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# -----------------------
# Odoo APIs (Vendors)
# -----------------------

@app.post("/vendors")
async def vendors(request: Request):
    raw_data = await request.json()
    clean_data = {k: v for k, v in raw_data.items() if v not in ["", None]}
    payload = PartnerActionPayload(**clean_data)

    action = payload.action

    try:
        if action == "create":
            partner_data = payload.dict(exclude_none=True)
            for key in ["action", "id", "query", "limit"]:
                partner_data.pop(key, None)

            partner_data["role"] = "vendor"
            return odoo_service.create_vendor(partner_data)

        elif action == "read":
            if payload.id is not None:
                return odoo_service.get_vendor_by_id(payload.id)
            if payload.query:
                return odoo_service.search_vendors(payload.query, limit=payload.limit or 100)
            raise HTTPException(status_code=400, detail="read requires either id or query")

        elif action == "update":
            if payload.id is None:
                raise HTTPException(status_code=400, detail="update requires id")

            update_data = payload.dict(exclude_none=True)
            for key in ["action", "id", "query", "limit"]:
                update_data.pop(key, None)

            if not update_data:
                raise HTTPException(status_code=400, detail="update requires at least one field")

            return odoo_service.update_partner(payload.id, update_data)

        elif action == "delete":
            if payload.id is None:
                raise HTTPException(status_code=400, detail="delete requires id")

            return odoo_service.delete_vendor(payload.id)

        elif action == "list":
            return odoo_service.get_vendors(limit=payload.limit or 100)

        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))