from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal

from odoo_service import OdooService

app = FastAPI()

# -----------------------
# Odoo Service
# -----------------------
odoo_service = OdooService()

# -----------------------
# Database Setup
# -----------------------
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

# -----------------------
# DB Model
# -----------------------
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# -----------------------
# Pydantic Schemas
# -----------------------

class ItemCreate(BaseModel):
    name: str

class ItemResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PartnerCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company_type: Optional[Literal["person", "company"]] = "person"
    vat: Optional[str] = None
    role: Optional[Literal["customer", "vendor", "all"]] = "customer"


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company_type: Optional[Literal["person", "company"]] = None
    vat: Optional[str] = None
    role: Optional[Literal["customer", "vendor", "all"]] = None


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
# DB Dependency
# -----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# Local Item APIs
# -----------------------
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/items/", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()


# -----------------------
# Odoo APIs (CRUD)
# -----------------------

@app.post("/customers")
async def customers(payload: PartnerActionPayload):
    clean_data = payload.dict(exclude_none=True)
    payload = PartnerActionPayload(**clean_data)

    action = payload.action

    try:
        if action == "create":
            partner_data = payload.dict(exclude_none=True)
            for key in ["action", "id", "query", "limit"]:
                partner_data.pop(key, None)
            if "role" not in partner_data or not partner_data["role"]:
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
                raise HTTPException(status_code=400, detail="update requires at least one field to change")

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


@app.post("/vendors")
async def vendors(payload: PartnerActionPayload):
    clean_data = payload.dict(exclude_none=True)
    payload = PartnerActionPayload(**clean_data)

    action = payload.action

    try:
        if action == "create":
            partner_data = payload.dict(exclude_none=True)
            for key in ["action", "id", "query", "limit"]:
                partner_data.pop(key, None)
            if "role" not in partner_data or not partner_data["role"]:
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
                raise HTTPException(status_code=400, detail="update requires at least one field to change")

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