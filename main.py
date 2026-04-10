from fastapi import FastAPI, HTTPException, Depends
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

# Create tables
Base.metadata.create_all(bind=engine)

# -----------------------
# Pydantic Schemas
# -----------------------

# Item schemas
class ItemCreate(BaseModel):
    name: str

class ItemResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True   # ✅ Pydantic v2 fix


# Odoo Partner Create
class PartnerCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company_type: Optional[Literal["person", "company"]] = "person"
    vat: Optional[str] = None
    role: Optional[Literal["customer", "vendor", "all"]] = "customer"


# Odoo Partner Update (all optional)
class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company_type: Optional[Literal["person", "company"]] = None
    vat: Optional[str] = None
    role: Optional[Literal["customer", "vendor", "all"]] = None


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

# ✅ GET partners
@app.get("/odoo/partners")
def get_odoo_partners(role: str = "customer", limit: int = 100):
    try:
        return odoo_service.get_partners(role=role, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ GET customers shortcut
@app.get("/odoo/customers")
def get_odoo_customers(limit: int = 100):
    try:
        return odoo_service.get_customers(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ POST create partner
@app.post("/odoo/partners")
def create_odoo_partner(partner: PartnerCreate):
    try:
        return odoo_service.create_partner(partner.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ PUT update partner
@app.put("/odoo/partners/{partner_id}")
def update_odoo_partner(partner_id: int, partner: PartnerUpdate):
    try:
        return odoo_service.update_partner(partner_id, partner.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ DELETE partner
@app.delete("/odoo/partners/{partner_id}")
def delete_odoo_partner(partner_id: int):
    try:
        return odoo_service.delete_partner(partner_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Verify Odoo auth
@app.get("/odoo/auth-verify")
def verify_odoo_auth():
    try:
        return odoo_service.verify_auth()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))