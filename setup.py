# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pydataquality",
    version="0.1.6",
    author="Dominion Akinrotimi",
    author_email="contact.dominionakinrotimi@gmail.com",
    description="Enterprise-grade automated data quality assessment and reporting engine for pandas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DominionAkinrotimi/pydataquality",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.2",
        "jinja2>=3.0.0",
        "PyYAML>=5.4",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
        ],
        "notebook": [
            "ipython>=7.0",
            "jupyter>=1.0",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    keywords="data-quality, data-analysis, pandas, visualization",
    project_urls={
        "Bug Reports": "https://github.com/DominionAkinrotimi/pydataquality/issues",
        "Source": "https://github.com/DominionAkinrotimi/pydataquality",
    },

)









