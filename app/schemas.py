from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime, date
from typing import List, Optional
from app.models import GenderEnum, RoleEnum, TierEnum


# region Employee Schemas
class EmployeeSchema(BaseModel):
    id: UUID4
    name: str
    gender: GenderEnum
    age: int
    phone_number: str
    email: EmailStr
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# endregion


# region User Schemas
class UserCreate(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    id: UUID4
    username: str
    role: RoleEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# endregion


# region Customer Schemas
class CustomerSchema(BaseModel):
    id: UUID4
    name: str
    gender: GenderEnum
    age: int
    phone_number: str
    email: EmailStr
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# endregion


# region Membership Schemas
class MembershipSchema(BaseModel):
    id: str
    customer_id: UUID4
    start_period: date
    end_period: date
    tier: TierEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        from_attributes = True


class MembershipCreate(BaseModel):
    customer_id: UUID4
    start_period: date
    end_period: date
    tier: TierEnum

    class Config:
        from_attributes = True


class MembershipUpdate(BaseModel):
    start_period: date
    end_period: date
    tier: TierEnum

    class Config:
        from_attributes = True


# endregion


# region Product Schemas
class ProductCategorySchema(BaseModel):
    id: UUID4
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductSchema(BaseModel):
    id: UUID4
    category_id: UUID4
    name: str
    description: Optional[str]
    stock: int
    price: float
    deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    category_id: UUID4
    name: str
    description: Optional[str] = None
    stock: int
    price: float

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    category_id: UUID4
    name: str
    description: Optional[str]
    stock: int
    price: float
    updated_at: datetime

    class Config:
        from_attributes = True


# endregion


# region Transaction Schemas
class TransactionDetailSchema(BaseModel):
    id: UUID4
    transaction_id: UUID4
    product_id: UUID4
    quantity: int
    price_per_unit: float
    total_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionSchema(BaseModel):
    id: UUID4
    customer_id: UUID4
    membership_id: Optional[UUID4]
    date: datetime
    total_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionDetailCreate(BaseModel):
    product_id: UUID4
    quantity: int
    price_per_unit: float


class TransactionCreate(BaseModel):
    customer_id: UUID4
    membership_id: Optional[UUID4]
    date: datetime
    transaction_details: List[TransactionDetailCreate]


# endregion


# region Segmentation Schemas
class SegmentationResultSchema(BaseModel):
    RFMCategory: str
    count: int
    total_revenue: float


class EvaluationSchema(BaseModel):
    silhouette_score: float
    davies_bouldin_index: float


class CustomerSegmentsSchema(BaseModel):
    algorithm: str
    segmentation: List[SegmentationResultSchema]
    evaluation: EvaluationSchema


# endregion


# region Dashboard Schemas
class MetricsSchema(BaseModel):
    total_sales: float
    total_transactions: int
    products_sold: int
    new_memberships: int


# endregion
