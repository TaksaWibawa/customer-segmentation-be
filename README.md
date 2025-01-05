# Retail Backend Service

## How to Run the FastAPI Application

1. **Clone the repository:**

  ```sh
  git clone https://github.com/TaksaWibawa/customer-segmentation-be.git .
  ```

2.**Create and activate a virtual environment:**

  ```sh
  python -m venv venv
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
  ```

3.**Install the dependencies:**

  ```sh
  pip install -r requirements.txt
  ```

4.**Run the FastAPI application:**

  ```sh
  uvicorn main:app --reload
  ```

## Database Migrations

### Create a New Migration

To create a new migration, run the following command:

```sh
alembic revision --autogenerate -m "description of the migration"
```

### Apply Migrations

To apply the migrations, run:

```sh
alembic upgrade head
```

### Update an Existing Migration

To update an existing migration, modify the migration script located in the `alembic/versions` directory and then apply the changes using:

```sh
alembic upgrade head
```

## API Documentation

### Authentication

#### Register User

- **URL:** `/register`
- **Method:** `POST`
- **Request Body:**

  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```

- **Response:**

  ```json
  {
    "status": "success",
    "message": "User registered successfully",
    "data": {
      "id": "UUID4",
      "username": "string",
      "role": "RoleEnum",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

#### Login User

- **URL:** `/login`
- **Method:** `POST`
- **Request Body:**

  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```

- **Response:**

  ```json
  {
    "status": "success",
    "message": "User logged in successfully",
    "data": {
      "id": "UUID4",
      "username": "string",
      "role": "RoleEnum",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

### Dashboard

#### Get Dashboard Data

- **URL:** `/dashboard/`
- **Method:** `GET`
- **Query Params:**
  - `start_date`: `YYYY-MM-DD`
  - `end_date`: `YYYY-MM-DD`
  - `model`: `kmeans` or `dbscan`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Dashboard data retrieved successfully",
    "data": {
      "total_sales": "float",
      "total_transactions": "int",
      "products_sold": "int",
      "new_memberships": "int",
      "customer_segments": {
        "algorithm": "string",
        "segmentation": [
          {
            "RFMCategory": "string",
            "count": "int",
            "total_revenue": "float"
          }
        ],
        "evaluation": {
          "silhouette_score": "float",
          "davies_bouldin_index": "float"
        }
      }
    }
  }
  ```

### Products

#### Get Product Categories

- **URL:** `/product-categories/`
- **Method:** `GET`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Product categories retrieved successfully",
    "data": [
      {
        "id": "UUID4",
        "name": "string",
        "description": "string",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ]
  }
  ```

#### Get Products

- **URL:** `/products/`
- **Method:** `GET`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Products retrieved successfully",
    "data": [
      {
        "id": "UUID4",
        "category_id": "UUID4",
        "name": "string",
        "description": "string",
        "stock": "int",
        "price": "float",
        "deleted": "bool",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ]
  }
  ```

#### Get Product

- **URL:** `/products/{product_id}`
- **Method:** `GET`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Product found",
    "data": {
      "id": "UUID4",
      "category_id": "UUID4",
      "name": "string",
      "description": "string",
      "stock": "int",
      "price": "float",
      "deleted": "bool",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

#### Create Product

- **URL:** `/products/`
- **Method:** `POST`
- **Request Body:**

  ```json
  {
    "category_id": "UUID4",
    "name": "string",
    "description": "string",
    "stock": "int",
    "price": "float"
  }
  ```

- **Response:**

  ```json
  {
    "status": "success",
    "message": "Product created successfully",
    "data": {
      "id": "UUID4",
      "category_id": "UUID4",
      "name": "string",
      "description": "string",
      "stock": "int",
      "price": "float",
      "deleted": "bool",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

#### Update Product

- **URL:** `/products/{product_id}`
- **Method:** `PUT`
- **Request Body:**

  ```json
  {
    "category_id": "UUID4",
    "name": "string",
    "description": "string",
    "stock": "int",
    "price": "float",
    "updated_at": "datetime"
  }
  ```

- **Response:**

  ```json
  {
    "status": "success",
    "message": "Product updated successfully",
    "data": {
      "id": "UUID4",
      "category_id": "UUID4",
      "name": "string",
      "description": "string",
      "stock": "int",
      "price": "float",
      "deleted": "bool",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

#### Delete Product

- **URL:** `/products/{product_id}`
- **Method:** `DELETE`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Product deleted successfully",
    "data": true
  }
  ```

### Transactions

#### Get All Transactions

- **URL:** `/transactions/`
- **Method:** `GET`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Transactions retrieved successfully",
    "data": [
      {
        "id": "UUID4",
        "customer_id": "UUID4",
        "membership_id": "UUID4",
        "date": "datetime",
        "total_amount": "float",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ]
  }
  ```

#### Get Transaction Details

- **URL:** `/transactions/{transaction_id}`
- **Method:** `GET`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Transaction details retrieved successfully",
    "data": [
      {
        "id": "UUID4",
        "transaction_id": "UUID4",
        "product_id": "UUID4",
        "quantity": "int",
        "price_per_unit": "float",
        "total_amount": "float",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ]
  }
  ```

#### Create Transaction

- **URL:** `/transactions/`
- **Method:** `POST`
- **Request Body:**

  ```json
  {
    "customer_id": "UUID4",
    "membership_id": "UUID4",
    "date": "datetime",
    "transaction_details": [
      {
        "product_id": "UUID4",
        "quantity": "int",
        "price_per_unit": "float"
      }
    ]
  }
  ```

- **Response:**

  ```json
  {
    "status": "success",
    "message": "Transaction created successfully",
    "data": {
      "id": "UUID4",
      "customer_id": "UUID4",
      "membership_id": "UUID4",
      "date": "datetime",
      "total_amount": "float",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

### Memberships

#### Get All Memberships

- **URL:** `/memberships/`
- **Method:** `GET`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Memberships retrieved successfully",
    "data": [
      {
        "id": "UUID4",
        "customer_id": "UUID4",
        "start_period": "date",
        "end_period": "date",
        "tier": "TierEnum",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ]
  }
  ```

#### Get Membership

- **URL:** `/memberships/{membership_id}`
- **Method:** `GET`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Membership found",
    "data": {
      "id": "UUID4",
      "customer_id": "UUID4",
      "start_period": "date",
      "end_period": "date",
      "tier": "TierEnum",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

#### Create Membership

- **URL:** `/memberships/`
- **Method:** `POST`
- **Request Body:**

  ```json
  {
    "customer_id": "UUID4",
    "start_period": "date",
    "end_period": "date",
    "tier": "TierEnum"
  }
  ```

- **Response:**

  ```json
  {
    "status": "success",
    "message": "Membership created successfully",
    "data": {
      "id": "UUID4",
      "customer_id": "UUID4",
      "start_period": "date",
      "end_period": "date",
      "tier": "TierEnum",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

#### Update Membership

- **URL:** `/memberships/{membership_id}`
- **Method:** `PUT`
- **Request Body:**

  ```json
  {
    "start_period": "date",
    "end_period": "date",
    "tier": "TierEnum"
  }
  ```

- **Response:**

  ```json
  {
    "status": "success",
    "message": "Membership updated successfully",
    "data": {
      "id": "UUID4",
      "customer_id": "UUID4",
      "start_period": "date",
      "end_period": "date",
      "tier": "TierEnum",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```

#### Delete Membership

- **URL:** `/memberships/{membership_id}`
- **Method:** `DELETE`
- **Response:**

  ```json
  {
    "status": "success",
    "message": "Membership deleted successfully",
    "data": true
  }
  ```
