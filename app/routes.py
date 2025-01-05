import random
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from pydantic import UUID4
from fastapi import APIRouter, Depends, Query
from faker import Faker
from datetime import datetime
from app.utils import error_response, success_response
from app.services import *
from app.schemas import *
from app.models import *
from app.db import get_db

fake = Faker()

router = APIRouter()


# region AUTHENTICATION
@router.post("/register", response_model=UserSchema)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = AuthService(db)
        new_user = await service.register_user(user)
        if not new_user:
            return error_response(400, "User already exists")
        return success_response(201, "User registered successfully", new_user)
    except Exception as e:
        return error_response(500, f"An error occurred while registering user: {str(e)}")


@router.post("/login", response_model=UserSchema)
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        service = AuthService(db)
        logged_in_user = await service.login_user(user)
        if not logged_in_user:
            return error_response(401, "Invalid username or password")
        return success_response(200, "User logged in successfully", logged_in_user)
    except Exception as e:
        return error_response(500, f"An error occurred while logging in user: {str(e)}")


# endregion


# region DASHBOARD
@router.get("/dashboard/", response_model=DashboardDataSchema)
async def get_dashboard_data(
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
    model: str = Query("kmeans", regex="^(kmeans|dbscan)$"),
    db: AsyncSession = Depends(get_db),
):
    try:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        segmentation_service = SegmentationService(db)
        await segmentation_service.preprocess(start_date_dt, end_date_dt)

        if model == "kmeans":
            await segmentation_service.with_kmeans()
        elif model == "dbscan":
            await segmentation_service.with_dbscan()
        else:
            return error_response(400, "Invalid model specified. Choose either 'kmeans' or 'dbscan'.")

        dashboard_service = DashboardService(db)
        data = await dashboard_service.get_dashboard_data(segmentation_service)
        return success_response(200, "Dashboard data retrieved successfully", data)
    except ValueError as e:
        return error_response(400, f"Invalid date format: {str(e)}")
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving dashboard data: {str(e)}")


# endregion


# region PRODUCTS
@router.get("/product-categories/", response_model=List[ProductCategorySchema])
async def get_product_categories(db: AsyncSession = Depends(get_db)):
    try:
        service = ProductService(db)
        categories = await service.get_product_categories()
        return success_response(200, "Product categories retrieved successfully", categories)
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving product categories: {str(e)}")


@router.get("/products/", response_model=List[ProductSchema])
async def get_products(db: AsyncSession = Depends(get_db)):
    try:
        service = ProductService(db)
        products = await service.get_products()
        return success_response(200, "Products retrieved successfully", products)
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving products: {str(e)}")


@router.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: UUID4, db: AsyncSession = Depends(get_db)):
    try:
        service = ProductService(db)
        product = await service.get_product(product_id)
        if not product:
            return error_response(404, "Product not found")
        return success_response(200, "Product found", product)
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving product: {str(e)}")


@router.post("/products/", response_model=ProductSchema)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = ProductService(db)
        new_product = await service.create_product(product)
        return success_response(201, "Product created successfully", new_product)
    except Exception as e:
        return error_response(500, f"An error occurred while creating product: {str(e)}")


@router.put("/products/{product_id}", response_model=ProductSchema)
async def update_product(product_id: UUID4, product: ProductUpdate, db: AsyncSession = Depends(get_db)):
    try:
        service = ProductService(db)
        updated_product = await service.update_product(product_id, product)
        if not updated_product:
            return error_response(404, "Product not found")
        return success_response(200, "Product updated successfully", updated_product)
    except Exception as e:
        return error_response(500, f"An error occurred while updating product: {str(e)}")


@router.delete("/products/{product_id}", response_model=bool)
async def delete_product(product_id: UUID4, db: AsyncSession = Depends(get_db)):
    try:
        service = ProductService(db)
        deleted = await service.delete_product(product_id)
        if not deleted:
            return error_response(404, "Product not found")
        return success_response(200, "Product deleted successfully", deleted)
    except Exception as e:
        return error_response(500, f"An error occurred while deleting product: {str(e)}")


# endregion


# region TRANSACTIONS
@router.get("/transactions/", response_model=List[TransactionSchema])
async def get_all_transactions(db: AsyncSession = Depends(get_db)):
    try:
        service = TransactionService(db)
        transactions = await service.get_all_transactions()
        return success_response(200, "Transactions retrieved successfully", transactions)
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving transactions: {str(e)}")


@router.get("/transactions/{transaction_id}", response_model=List[TransactionDetailSchema])
async def get_transaction_details(transaction_id: UUID4, db: AsyncSession = Depends(get_db)):
    try:
        service = TransactionService(db)
        transaction_details = await service.get_transaction_details(transaction_id)
        return success_response(200, "Transaction details retrieved successfully", transaction_details)
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving transaction details: {str(e)}")


@router.post("/transactions/", response_model=TransactionSchema)
async def create_transaction(transaction_data: TransactionCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = TransactionService(db)
        new_transaction = await service.create_transaction(transaction_data)
        return success_response(201, "Transaction created successfully", new_transaction)
    except Exception as e:
        return error_response(500, f"An error occurred while creating the transaction: {str(e)}")


# endregion


# region MEMBERSHIPS
@router.get("/memberships/", response_model=List[MembershipSchema])
async def get_all_memberships(db: AsyncSession = Depends(get_db)):
    try:
        service = MembershipService(db)
        memberships = await service.get_all_memberships()
        return success_response(200, "Memberships retrieved successfully", memberships)
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving memberships: {str(e)}")


@router.get("/memberships/{membership_id}", response_model=MembershipSchema)
async def get_membership(membership_id: UUID4, db: AsyncSession = Depends(get_db)):
    try:
        service = MembershipService(db)
        membership = await service.get_membership(membership_id)
        if not membership:
            return error_response(404, "Membership not found")
        return success_response(200, "Membership found", membership)
    except Exception as e:
        return error_response(500, f"An error occurred while retrieving membership: {str(e)}")


@router.post("/memberships/", response_model=MembershipSchema)
async def create_membership(membership: MembershipCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = MembershipService(db)
        new_membership = await service.create_membership(membership)
        return success_response(201, "Membership created successfully", new_membership)
    except Exception as e:
        return error_response(500, f"An error occurred while creating membership: {str(e)}")


@router.put("/memberships/{membership_id}", response_model=MembershipSchema)
async def update_membership(membership_id: UUID4, membership: MembershipUpdate, db: AsyncSession = Depends(get_db)):
    try:
        service = MembershipService(db)
        updated_membership = await service.update_membership(membership_id, membership)
        if not updated_membership:
            return error_response(404, "Membership not found")
        return success_response(200, "Membership updated successfully", updated_membership)
    except Exception as e:
        return error_response(500, f"An error occurred while updating membership: {str(e)}")


@router.delete("/memberships/{membership_id}", response_model=bool)
async def delete_membership(membership_id: UUID4, db: AsyncSession = Depends(get_db)):
    try:
        service = MembershipService(db)
        deleted = await service.delete_membership(membership_id)
        if not deleted:
            return error_response(404, "Membership not found")
        return success_response(200, "Membership deleted successfully", deleted)
    except Exception as e:
        return error_response(500, f"An error occurred while deleting membership: {str(e)}")


# endregion


# region DUMMY DATA
@router.get("/dummy/")
async def create_dummy_data(db: AsyncSession = Depends(get_db)):
    try:
        # Delete existing data
        await db.execute(delete(TransactionDetail))
        await db.execute(delete(Transaction))
        await db.execute(delete(Membership))
        await db.execute(delete(Product))
        await db.execute(delete(ProductCategory))
        await db.execute(delete(Customer))
        await db.commit()

        # Create customers
        customers = []
        emails = set()
        for _ in range(1000):
            email = fake.unique.email()
            while email in emails:
                email = fake.unique.email()
            emails.add(email)
            customer = Customer(
                id=fake.uuid4(),
                name=fake.name(),
                gender=random.choice(list(GenderEnum)),
                age=random.randint(18, 70),
                phone_number=fake.phone_number(),
                email=email,
                address=fake.address(),
                created_at=fake.date_time_this_decade(),
                updated_at=fake.date_time_this_decade(),
            )
            customers.append(customer)
        db.add_all(customers)
        await db.commit()

        # Create product categories
        categories = []
        for _ in range(10):
            category = ProductCategory(
                id=fake.uuid4(),
                name=fake.word(),
                description=fake.text(),
                created_at=fake.date_time_this_decade(),
                updated_at=fake.date_time_this_decade(),
            )
            categories.append(category)
        db.add_all(categories)
        await db.commit()

        # Create products
        products = []
        for _ in range(100):
            product = Product(
                id=fake.uuid4(),
                category_id=random.choice(categories).id,
                name=fake.word(),
                description=fake.text(),
                stock=random.randint(1, 100),
                price=round(random.uniform(10.0, 1000.0), 2),
                deleted=False,
                created_at=fake.date_time_this_decade(),
                updated_at=fake.date_time_this_decade(),
            )
            products.append(product)
        db.add_all(products)
        await db.commit()

        # Create memberships
        memberships = []
        for customer in customers:
            membership = Membership(
                id=fake.uuid4(),
                customer_id=customer.id,
                start_period=fake.date_this_decade(),
                end_period=fake.date_this_decade(),
                tier=random.choice(list(TierEnum)),
                created_at=fake.date_time_this_decade(),
                updated_at=fake.date_time_this_decade(),
            )
            memberships.append(membership)
        db.add_all(memberships)
        await db.commit()

        # Create transactions and transaction details
        transactions = []
        transaction_details = []
        for _ in range(10000):
            customer = random.choice(customers)
            transaction = Transaction(
                id=fake.uuid4(),
                customer_id=customer.id,
                membership_id=random.choice(memberships).id if random.random() > 0.5 else None,
                date=fake.date_time_between_dates(datetime_start=datetime(2023, 1, 1), datetime_end=datetime(2024, 12, 31)),
                total_amount=0,  # Will be updated later
                created_at=fake.date_time_this_decade(),
                updated_at=fake.date_time_this_decade(),
            )
            transactions.append(transaction)
            num_items = random.randint(1, 10)
            total_amount = 0
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 5)
                price_per_unit = product.price
                total_amount += quantity * price_per_unit
                transaction_detail = TransactionDetail(
                    id=fake.uuid4(),
                    transaction_id=transaction.id,
                    product_id=product.id,
                    quantity=quantity,
                    price_per_unit=price_per_unit,
                    total_amount=quantity * price_per_unit,
                    created_at=fake.date_time_this_decade(),
                    updated_at=fake.date_time_this_decade(),
                )
                transaction_details.append(transaction_detail)
            transaction.total_amount = total_amount

        db.add_all(transactions)
        db.add_all(transaction_details)
        await db.commit()

        return success_response(200, "Dummy data created successfully", None)
    except Exception as e:
        return error_response(500, f"An error occurred while creating dummy data: {str(e)}")


# endregion
