from pydantic import BaseModel
from typing import Optional


class BusinessCreate(BaseModel):
    name: str
    name_en: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    city_en: Optional[str] = ""
    postal_code: Optional[str] = ""
    region: Optional[str] = ""
    phone: Optional[str] = ""
    mobile: Optional[str] = ""
    email: Optional[str] = ""
    website: Optional[str] = ""
    category: Optional[str] = ""
    category_en: Optional[str] = ""
    description_gr: Optional[str] = ""
    description_en: Optional[str] = ""
    hours: Optional[str] = ""
    facebook: Optional[str] = ""
    instagram: Optional[str] = ""
    linkedin: Optional[str] = ""
    logo_path: Optional[str] = ""
    tax_id: Optional[str] = ""
    contact_person: Optional[str] = ""


class BusinessUpdate(BusinessCreate):
    name: Optional[str] = None


class SubmissionRequest(BaseModel):
    business_id: int
    directories: list[str]


class HumanActionComplete(BaseModel):
    action: str = "continue"
