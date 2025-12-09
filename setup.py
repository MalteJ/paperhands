"""Setup script for paperhands package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="paperhands",
    version="0.1.0",
    author="Your Name",
    description="A backtesting framework for stock and options trading strategies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=["paperhands", "paperhands.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "tqdm>=4.65.0",
    ],
    extras_require={
        "alpaca": ["alpaca-py>=0.9.0"],
        "yahoo": ["yfinance>=0.2.28"],
        "plotting": ["matplotlib>=3.7.0", "seaborn>=0.12.0"],
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=6.0.0"],
    },
)
