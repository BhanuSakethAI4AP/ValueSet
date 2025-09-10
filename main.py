from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from config.database import connect_to_mongo, close_mongo_connection
from routers.valuesets_router import router as valuesets_router
from src.auth.auth_router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Connecting to MongoDB Atlas...")
    print(f"Database: {settings.db_name}")
    
    await connect_to_mongo()
    
    print("Application ready!")
    
    yield
    
    await close_mongo_connection()


app = FastAPI(
    title="ValueSets Platform API",
    description="API for managing platform value sets (enums) with authentication",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(valuesets_router)


@app.get("/")
async def root():
    return {
        "service": "ValueSets Platform",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "valuesets"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)