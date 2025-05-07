from setuptools import setup, find_packages

setup(
    name="pyonstar",
    version="0.0.1",
    description="Unofficial package for making OnStar API requests",
    author="Bryan Leboff",
    author_email="leboff@gmail.com",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
        "pyjwt>=2.8.0",
        "pyotp>=2.9.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 