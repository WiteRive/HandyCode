#!/usr/bin/env python3
"""Скрипт установки HandyCode"""

from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="handycode",
    version="2.0.0",
    author="HandyCode Team",
    author_email="hello@handycode.dev",
    description="AI Ассистент для разработки - аналог Claude Code для командной строки",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/handycode",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "handycode=handycode.main:main",
            "hc=handycode.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)