from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.config import config
import asyncio

DATABASE_URL = config.DATABASE_URL
async_engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_models():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def connect_to_db():
    retries = 5
    while retries > 0:
        try:
            async with async_engine.begin() as conn:
                print("Connected to the database!")
                return conn
        except Exception as e:
            print(f"Database connection failed: {e}")
            retries -= 1
            await asyncio.sleep(5)
    raise Exception("Failed to connect to the database after retries.")


if __name__ == "__main__":
    asyncio.run(connect_to_db())
