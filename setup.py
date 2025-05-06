from setuptools import setup, find_packages

setup(
    name="onstar",
    version="2.6.5",
    description="Unofficial package for making OnStar API requests",
    author="Ruben Medina, BigThunderSR",
    author_email="dev@rubenmedina.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pyjwt>=2.8.0",
        "python-dotenv>=1.0.0",
        "uuid>=1.30",
        "pyotp>=2.9.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 