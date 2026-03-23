from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="browsr",
    version="1.1.0",
    description="AI-powered Helium Python script generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["browsr"],
    install_requires=[
        "openai>=1.0.0",
        "helium>=3.0.0",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "browsr=browsr:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
