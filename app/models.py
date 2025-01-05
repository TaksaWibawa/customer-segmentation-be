from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Date, DateTime, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum, uuid

Base = declarative_base()


# Enum Definitions
class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"


class RoleEnum(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    customer = "customer"


class TierEnum(str, enum.Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"


#! WILL CHANGED LATER
class RFMCategoryEnum(str, enum.Enum):
    loyal_customer = "Loyal Customer"
    occasional_customer = "Occasional Customer"
    low_value_customer = "Low Value Customer"
    others = "Others"
    noise = "Noise"


# Models
class Employee(Base):
    __tablename__ = "employees"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    age = Column(Integer, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class Account(Base):
    __tablename__ = "accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    age = Column(Integer, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class Membership(Base):
    __tablename__ = "memberships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    start_period = Column(Date, nullable=False)
    end_period = Column(Date, nullable=False)
    tier = Column(Enum(TierEnum), nullable=False)
    customer = relationship("Customer", back_populates="memberships")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


Customer.memberships = relationship("Membership", back_populates="customer")


class ProductCategory(Base):
    __tablename__ = "product_categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    stock = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    deleted = Column(Boolean, default=False)
    category = relationship("ProductCategory", back_populates="products")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


ProductCategory.products = relationship("Product", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    membership_id = Column(UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=True)
    date = Column(DateTime, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    customer = relationship("Customer", back_populates="transactions")
    membership = relationship("Membership", back_populates="transactions")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


Customer.transactions = relationship("Transaction", back_populates="customer")
Membership.transactions = relationship("Transaction", back_populates="membership")


class TransactionDetail(Base):
    __tablename__ = "transaction_details"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    transaction = relationship("Transaction", back_populates="transaction_details")
    product = relationship("Product", back_populates="transaction_details")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


Transaction.transaction_details = relationship("TransactionDetail", back_populates="transaction")
Product.transaction_details = relationship("TransactionDetail", back_populates="product")
