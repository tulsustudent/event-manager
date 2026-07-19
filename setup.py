from setuptools import setup, find_packages

setup(
    name="practice",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi", "uvicorn[standard]", "sqlalchemy",
        "psycopg2-binary", "pydantic", "python-jose[cryptography]",
        "passlib", "python-dotenv", "redis", "flet", "requests"
    ],
)