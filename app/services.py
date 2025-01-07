import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.cluster import KMeans, DBSCAN
from pydantic import UUID4
from passlib.context import CryptContext
from decimal import Decimal
from datetime import datetime
from app.schemas import *
from app.models import *
from app.utils import error_response
import pickle
import os


# region DASHBOARD
CACHE_FILE = "segmentation_cache.pkl"


class SegmentationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.df_rfm = None
        self.segmented_data = None
        self.algorithm = None

    async def preprocess(self, start_date: datetime = None, end_date: datetime = None, num_batches: int = 20, algorithm: str = "kmeans"):
        # Check if there are existing segmentation results for the algorithm
        algorithm = algorithm.lower()
        existing_results = await self.db.execute(select(SegmentationResult).where(SegmentationResult.algorithm == algorithm))
        existing_results = existing_results.scalars().all()

        if existing_results:
            # Load existing segmentation results
            self.segmented_data = pd.DataFrame(
                [
                    {
                        "CustomerID": result.customer_id,
                        "RFMCategory": result.rfm_category,
                        "Cluster": result.cluster,
                        "Recency": result.recency,
                        "Frequency": result.frequency,
                        "Monetary": result.monetary,
                    }
                    for result in existing_results
                ]
            )
            self.algorithm = algorithm
            return

        all_data = []
        start_batch = 0

        # Get the total number of transactions
        total_transactions_query = select(func.count(Transaction.id))
        if start_date:
            total_transactions_query = total_transactions_query.filter(Transaction.date >= start_date)
        if end_date:
            total_transactions_query = total_transactions_query.filter(Transaction.date <= end_date)
        total_transactions_result = await self.db.execute(total_transactions_query)
        total_transactions = total_transactions_result.scalar()

        # Calculate the batch size based on the total number of transactions and the desired number of batches
        batch_size = (total_transactions + num_batches - 1) // num_batches

        # Check if there is cached data
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "rb") as f:
                all_data = pickle.load(f)
                start_batch = len(all_data) // batch_size

        for batch_num in range(start_batch, num_batches):
            print(f"Processing batch {batch_num + 1}/{num_batches}...")
            print(f"Total data: {total_transactions}, Processed data: {len(all_data)}")
            query = select(Transaction).options(selectinload(Transaction.transaction_details)).limit(batch_size).offset(batch_num * batch_size)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            result = await self.db.execute(query)
            transactions = result.scalars().all()

            if not transactions:
                break

            data = [
                {
                    "CustomerID": t.customer_id,
                    "InvoiceNo": t.id,
                    "Quantity": td.quantity,
                    "UnitPrice": td.price_per_unit,
                    "Date": t.date,
                }
                for t in transactions
                for td in t.transaction_details
            ]
            all_data.extend(data)

            # Cache the intermediate results
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(all_data, f)

        if not all_data:
            raise HTTPException(status_code=404, detail="No transactions found.")

        df = pd.DataFrame(all_data)

        # Data cleaning
        df = df[df["CustomerID"].notna()]
        df = df[df["Quantity"] > 0]
        df = df[df["UnitPrice"] > 0]
        df["Revenue"] = df["Quantity"] * df["UnitPrice"]

        # Feature engineering
        if end_date is None:
            end_date = datetime.now()
        df["Recency"] = (end_date - df["Date"]).dt.days
        df_rfm = (
            df.groupby("CustomerID")
            .agg({"Recency": "min", "InvoiceNo": "count", "Revenue": "sum"})
            .rename(columns={"InvoiceNo": "Frequency", "Revenue": "Monetary"})
        ).reset_index()

        self.df_rfm = df_rfm

    async def with_kmeans(self):
        if self.df_rfm is None:
            raise ValueError("Data not preprocessed. Call preprocess() first.")

        if len(self.df_rfm) < 3:
            raise ValueError("Not enough data points to perform KMeans clustering.")

        # Fit KMeans on the entire dataset
        kmeans = KMeans(n_clusters=3, random_state=42)
        self.df_rfm["Cluster"] = kmeans.fit_predict(self.df_rfm[["Recency", "Frequency", "Monetary"]])

        self.assign_rfm_categories_kmeans()
        self.segmented_data = self.df_rfm.copy()
        self.algorithm = AlgorithmEnum.kmeans

        await self.save_segmentation_results()

    async def with_dbscan(self):
        if self.df_rfm is None:
            raise ValueError("Data not preprocessed. Call preprocess() first.")

        rfm_scaled = StandardScaler().fit_transform(self.df_rfm[["Recency", "Frequency", "Monetary"]])

        # Fit DBSCAN on the entire dataset
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.df_rfm["Cluster"] = dbscan.fit_predict(rfm_scaled)

        self.assign_rfm_categories_dbscan()
        self.segmented_data = self.df_rfm.copy()
        self.algorithm = AlgorithmEnum.dbscan

        await self.save_segmentation_results()

    def assign_rfm_categories_kmeans(self):
        # Define cluster labels based on RFM statistics
        def assign_labels(row):
            cluster = row["Cluster"]

            # Assign labels based on cluster number
            if cluster == 2:
                return RFMCategoryEnum.occasional_customer
            elif cluster == 1:
                return RFMCategoryEnum.loyal_customer
            elif cluster == 0:
                return RFMCategoryEnum.low_value_customer
            else:
                return RFMCategoryEnum.others

        # Apply labels to clusters
        self.df_rfm["RFMCategory"] = self.df_rfm.apply(assign_labels, axis=1)

    def assign_rfm_categories_dbscan(self):
        # Calculate mean RFM values for each cluster
        cluster_means = self.df_rfm.groupby("Cluster").agg({"Recency": "mean", "Frequency": "mean", "Monetary": "mean"}).reset_index()

        # Define thresholds for labeling clusters
        recency_threshold_low = cluster_means["Recency"].quantile(0.33)
        recency_threshold_high = cluster_means["Recency"].quantile(0.67)
        frequency_threshold_low = cluster_means["Frequency"].quantile(0.33)
        frequency_threshold_high = cluster_means["Frequency"].quantile(0.67)
        monetary_threshold_low = cluster_means["Monetary"].quantile(0.33)
        monetary_threshold_high = cluster_means["Monetary"].quantile(0.67)

        # Define cluster labels based on RFM statistics
        def assign_labels(row):
            cluster = row["Cluster"]

            # Handle noise cluster (-1)
            if cluster == -1:
                return RFMCategoryEnum.noise

            # Extract mean RFM values for the cluster
            recency = row["Recency"]
            frequency = row["Frequency"]
            monetary = row["Monetary"]

            # Compare with thresholds to assign labels
            if recency > recency_threshold_low and frequency < frequency_threshold_low and monetary < monetary_threshold_low:
                return RFMCategoryEnum.low_value_customer
            elif recency < recency_threshold_high and frequency > frequency_threshold_high and monetary > monetary_threshold_high:
                return RFMCategoryEnum.loyal_customer
            elif recency < recency_threshold_low and frequency > frequency_threshold_low and monetary > monetary_threshold_low:
                return RFMCategoryEnum.occasional_customer
            else:
                return RFMCategoryEnum.others

        # Apply labels to clusters
        self.df_rfm["RFMCategory"] = self.df_rfm.apply(assign_labels, axis=1)

    async def save_segmentation_results(self):
        # Clear existing segmentation results for the current algorithm
        await self.db.execute(delete(SegmentationResult).where(SegmentationResult.algorithm == self.algorithm))
        await self.db.commit()

        # Save new segmentation results
        segmentation_results = [
            SegmentationResult(
                customer_id=row["CustomerID"],
                rfm_category=row["RFMCategory"],
                cluster=row["Cluster"],
                recency=row["Recency"],
                frequency=row["Frequency"],
                monetary=row["Monetary"],
                algorithm=self.algorithm,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for _, row in self.df_rfm.iterrows()
        ]
        self.db.add_all(segmentation_results)
        await self.db.commit()

    async def result(self):
        if self.segmented_data is None:
            raise ValueError("Segmentation not performed. Call with_kmeans() or with_dbscan() first.")

        # Group by RFMCategory and calculate count and total revenue
        result = self.segmented_data.groupby("RFMCategory").agg(count=("CustomerID", "size"), total_revenue=("Monetary", "sum")).reset_index()

        # Convert Decimal to float
        result["total_revenue"] = result["total_revenue"].apply(lambda x: float(x) if isinstance(x, Decimal) else x)

        # if any category is missing, add it with 0 count and revenue
        missing_categories = [category.value for category in RFMCategoryEnum if category.value not in result["RFMCategory"].values]

        for category in missing_categories:
            missing_category = pd.DataFrame({"RFMCategory": [category], "count": [0], "total_revenue": [0]})
            result = pd.concat([result, missing_category], ignore_index=True)

        result = result.rename(columns={"RFMCategory": "rfm_category"})

        # Calculate silhouette score and Davies-Bouldin index
        rfm_values = self.segmented_data[["Recency", "Frequency", "Monetary"]]
        clusters = self.segmented_data["Cluster"]
        silhouette_avg = silhouette_score(rfm_values, clusters)
        db_index = davies_bouldin_score(rfm_values, clusters)

        return {
            "algorithm": self.algorithm,
            "segmentation": result.to_dict(orient="records"),
            "evaluation": {"silhouette_score": silhouette_avg, "davies_bouldin_index": db_index},
        }


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_metrics(self, start_date: datetime = None, end_date: datetime = None):
        # Total sales
        query = select(func.sum(Transaction.total_amount))
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        total_sales_result = await self.db.execute(query)
        total_sales = total_sales_result.scalar() or 0

        # Total transactions
        query = select(func.count(Transaction.id))
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        total_transactions_result = await self.db.execute(query)
        total_transactions = total_transactions_result.scalar() or 0

        # Products sold
        query = select(func.sum(TransactionDetail.quantity)).join(Transaction)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        products_sold_result = await self.db.execute(query)
        products_sold = products_sold_result.scalar() or 0

        # Total memberships
        query = select(func.count(Membership.id))
        total_memberships_result = await self.db.execute(query)
        total_memberships = total_memberships_result.scalar() or 0

        return {
            "total_sales": total_sales,
            "total_transactions": total_transactions,
            "products_sold": products_sold,
            "total_memberships": total_memberships,
        }

    async def get_dashboard_segmentation(self, segmentation_service: SegmentationService):
        segmentation_result = await segmentation_service.result()
        return {
            "algorithm": segmentation_result["algorithm"],
            "segmentation": segmentation_result["segmentation"],
            "evaluation": segmentation_result["evaluation"],
        }


# endregion


# region PRODUCTS
class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_product_categories(self, limit: int, offset: int):
        result = await self.db.execute(select(ProductCategory).limit(limit).offset(offset))
        categories = result.scalars().all()
        return [ProductCategorySchema.model_validate(category) for category in categories]

    async def get_products(self, limit: int, offset: int):
        result = await self.db.execute(select(Product).where(Product.deleted == False).limit(limit).offset(offset))
        products = result.scalars().all()
        return [ProductSchema.model_validate(product) for product in products]

    async def get_product(self, product_id: UUID4):
        result = await self.db.execute(select(Product).filter_by(id=product_id, deleted=False))
        product = result.scalars().first()
        return ProductSchema.model_validate(product)

    async def create_product(self, product: ProductCreate):
        new_product = Product(
            category_id=product.category_id,
            name=product.name,
            description=product.description,
            stock=product.stock,
            price=product.price,
            deleted=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(new_product)
        await self.db.commit()
        await self.db.refresh(new_product)
        return ProductSchema.model_validate(new_product)

    async def update_product(self, product_id: UUID4, product: ProductUpdate):
        result = await self.db.execute(select(Product).filter_by(id=product_id))
        existing_product = result.scalars().first()

        if existing_product:
            existing_product.category_id = product.category_id
            existing_product.name = product.name
            existing_product.description = product.description
            existing_product.stock = product.stock
            existing_product.price = product.price
            existing_product.updated_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(existing_product)
            return ProductSchema.model_validate(existing_product)
        else:
            return None

    async def delete_product(self, product_id: UUID4):
        result = await self.db.execute(select(Product).filter_by(id=product_id, deleted=False))
        product = result.scalars().first()

        if product:
            product.deleted = True
            product.updated_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(product)
            return ProductSchema.model_validate(product)
        else:
            return None


# endregion


# region AUTHENTICATION
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    async def is_user_exists(self, username: str):
        result = await self.db.execute(select(Account).filter(Account.username == username))
        user = result.scalars().first()
        return user is not None

    async def register_user(self, user: UserCreate):
        if await self.is_user_exists(user.username):
            return None

        hashed_password = self.get_password_hash(user.password)
        db_user = Account(
            username=user.username,
            password=hashed_password,
            role="customer",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def login_user(self, user: UserLogin):
        result = await self.db.execute(select(Account).filter(Account.username == user.username))
        db_user = result.scalars().first()
        if not db_user or not self.verify_password(user.password, db_user.password):
            return None
        return db_user


# endregion


# region TRANSACTION
class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_transactions(self, limit: int, offset: int):
        result = await self.db.execute(select(Transaction).options(selectinload(Transaction.transaction_details)).limit(limit).offset(offset))
        transactions = result.scalars().all()
        return [TransactionSchema.model_validate(transaction) for transaction in transactions]

    async def get_transaction_details(self, transaction_id: UUID4):
        result = await self.db.execute(select(TransactionDetail).where(TransactionDetail.transaction_id == transaction_id))
        transaction_details = result.scalars().all()
        return [TransactionDetailSchema.model_validate(detail) for detail in transaction_details]

    async def create_anonymous_customer(self):
        anonymous_customer = Customer(
            name="Anonymous",
            gender=GenderEnum.male,
            age=0,
            phone_number="0000000000",
            email="anonymous@example.com",
            address=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(anonymous_customer)
        await self.db.commit()
        await self.db.refresh(anonymous_customer)
        return anonymous_customer

    async def create_transaction(self, transaction_data: TransactionCreate):
        if not transaction_data.membership_id:
            anonymous_customer = await self.create_anonymous_customer()
            customer_id = anonymous_customer.id
        else:
            membership = await self.db.execute(select(Membership).filter_by(id=transaction_data.membership_id))
            membership = membership.scalars().first()
            if not membership:
                return error_response(404, "Membership not found.")
            customer_id = membership.customer_id

        new_transaction = Transaction(
            customer_id=customer_id,
            membership_id=transaction_data.membership_id,
            date=transaction_data.date,
            total_amount=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(new_transaction)
        await self.db.commit()
        await self.db.refresh(new_transaction)

        total_amount = 0
        for detail in transaction_data.transaction_details:
            total_amount += detail.quantity * detail.price_per_unit
            new_detail = TransactionDetail(
                transaction_id=new_transaction.id,
                product_id=detail.product_id,
                quantity=detail.quantity,
                price_per_unit=detail.price_per_unit,
                total_amount=detail.quantity * detail.price_per_unit,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(new_detail)

        new_transaction.total_amount = total_amount
        await self.db.commit()
        await self.db.refresh(new_transaction)

        return TransactionSchema.model_validate(new_transaction)


# endregion


# region MEMBERSHIP
class MembershipService:
    def __init__(self, db: AsyncSession):
        self.db = db


class MembershipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_memberships(self, limit: int, offset: int):
        result = await self.db.execute(select(Membership, Customer.name).join(Customer, Membership.customer_id == Customer.id).limit(limit).offset(offset))
        memberships = result.all()
        return [{**MembershipSchema.model_validate(membership).model_dump(), "name": customer_name} for membership, customer_name in memberships]

    async def get_membership(self, membership_id: str):
        result = await self.db.execute(
            select(Membership, Customer.name).join(Customer, Membership.customer_id == Customer.id).where(Membership.id == membership_id)
        )
        membership_data = result.first()
        if membership_data:
            membership, customer_name = membership_data
            return {**MembershipSchema.model_validate(membership).model_dump(), "name": customer_name}
        return None

    async def create_membership(self, membership_data: MembershipCreate):
        new_membership = Membership(
            customer_id=membership_data.customer_id,
            start_period=membership_data.start_period,
            end_period=membership_data.end_period,
            tier=membership_data.tier,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(new_membership)
        await self.db.commit()
        await self.db.refresh(new_membership)
        return MembershipSchema.model_validate(new_membership)

    async def update_membership(self, membership_id: UUID4, membership_data: MembershipUpdate):
        result = await self.db.execute(select(Membership).where(Membership.id == membership_id))
        membership = result.scalar_one_or_none()
        if membership:
            membership.start_period = membership_data.start_period
            membership.end_period = membership_data.end_period
            membership.tier = membership_data.tier
            membership.updated_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(membership)
        return MembershipSchema.model_validate(membership)

    async def delete_membership(self, membership_id: UUID4):
        result = await self.db.execute(select(Membership).where(Membership.id == membership_id))
        membership = result.scalar_one_or_none()
        if membership:
            await self.db.delete(membership)
            await self.db.commit()
            return True
        return False


# endregion

# region CUSTOMER

# endregion
