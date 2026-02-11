from pydantic import BaseModel
from typing import Optional


# -------- PAGE 1 : Basic Info & Address --------

class BasicInfo(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: str
    phone: str
    gender: str
    profession: str
    father_name: str


class Address(BaseModel):
    province: str
    district: str
    municipality: str
    ward: int  # Changed from ward_no to match frontend


class KYCPageOneSchema(BaseModel):
    user_id: str
    basic_info: BasicInfo
    permanent_address: Address
    temporary_address: Address  # Changed from temporary_location (lat/lng)
    submitted_at: int


# -------- PAGE 2 : Government ID --------

class IDDetails(BaseModel):
    id_type: str            # NID or CITIZENSHIP
    id_number: str
    issue_date: str


class IDImages(BaseModel):
    front_image_ref: str    # file path / cloud reference
    back_image_ref: str


class KYCPageTwoSchema(BaseModel):
    user_id: str
    id_details: IDDetails
    id_images: IDImages
    submitted_at: int


# -------- PAGE 3 : Declaration Video --------

class DeclarationVideo(BaseModel):
    video_ref: Optional[str] = None          # legacy video path
    selfie_image_ref: Optional[str] = None   # new selfie image path
    language: Optional[str] = None           # "ne"
    declared_text: Optional[str] = None


class KYCPageThreeSchema(BaseModel):
    user_id: str
    declaration_video: DeclarationVideo
    submitted_at: int
