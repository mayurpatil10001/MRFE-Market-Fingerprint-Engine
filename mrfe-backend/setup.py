from setuptools import setup, find_packages

setup(
    name="mrfe-backend",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.115.0",
        "uvicorn[standard]==0.34.0",
        "sqlalchemy[asyncio]==2.0.36",
        "asyncpg==0.30.0",
        "aiosqlite==0.20.0",
        "alembic==1.14.0",
        "pydantic==2.10.0",
        "pydantic-settings==2.6.0",
        "structlog==24.4.0",
        "prometheus-client==0.21.0",
        "redis==5.2.0",
        "celery==5.4.0",
        "python-multipart==0.0.17",
        "cryptography==43.0.3",
        "python-jose[cryptography]==3.3.0",
        "motor==3.6.0",
    ],
    author="MRFE Team",
    description="Enterprise-grade Market Reaction Fingerprint Engine backend",
    python_requires=">=3.11",
)
