from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import router
from app.db import init_models, connect_to_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_db()
        await init_models()
        yield
    except Exception as e:
        print(f"Failed to initialize the application: {e}")
        raise


app = FastAPI(title="Retail Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# ? Run with: `uvicorn app.main:app --reload`
