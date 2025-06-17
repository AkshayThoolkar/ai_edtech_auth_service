from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers.auth_router import router as auth_router
from middleware.security_middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware
)

app = FastAPI(
    title="Auth Service",
    description="Authentication service for the EdTech platform",
    version="1.0.0"
)

# Add security middleware (order matters - first added is executed last)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls_per_minute=100)  # 100 requests per minute per IP

# Add CORS middleware with environment-driven configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Now loaded from environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Auth Service is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
