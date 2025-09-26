"""
Setup script for Value Set Library
This allows the library to be packaged and installed as a reusable module
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="value-set-lib",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A reusable library for managing value sets with MongoDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/value-set-lib",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "motor>=3.0.0",
        "pymongo>=4.0.0",
        "pydantic>=2.0.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
        "fastapi": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
        ],
    },
    py_modules=["value_set_lib"],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            # Add any CLI commands here if needed
        ],
    },
)