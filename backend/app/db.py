from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Convert sqlite:/// to sqlite+aiosqlite:///
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

engine = create_async_engine(db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight SQLite migration for existing DevAD databases.
        if db_url.startswith("sqlite+"):
            result = await conn.exec_driver_sql("PRAGMA table_info(campaigns)")
            columns = {row[1] for row in result.fetchall()}
            if "product_image_path" not in columns:
                await conn.exec_driver_sql("ALTER TABLE campaigns ADD COLUMN product_image_path VARCHAR(500)")
