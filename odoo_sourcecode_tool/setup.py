"""
Odoo Tools - Unified Odoo Source Code Management Tool
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="odoo-tools",
    version="1.0.0",
    author="Agromarin",
    description="Unified tool for Odoo source code management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/agromarin/odoo-tools",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "lxml>=4.9.0",
        "GitPython>=3.1.0",
        "PyYAML>=6.0",
        "rich>=13.0.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "odoo-tools=odoo_tools.cli:main",
        ],
    },
)
