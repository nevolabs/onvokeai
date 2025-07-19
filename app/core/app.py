"""
FastAPI application factory and configuration.
"""
from fastapi import FastAPI
from app.api.routes import router
from app.core.database import get_supabase_client
from app.core.initializers import service_manager  # Initialize all services early

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    """
    app = FastAPI(
        title="SOP Generation API",
        description="API for generating Standard Operating Procedures using AI",
        version="1.0.0"
    )
    
    # Services are already initialized by importing service_manager
    # Just verify Supabase connection
    get_supabase_client()
    
    # Include API routes
    app.include_router(router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        return {"message": "SOP Generation API is running", "status": "healthy"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "message": "Service is operational"}
    
    return app
