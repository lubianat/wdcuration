#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = [
    "requests",
    "SPARQLWrapper",
    "tqdm",
    "inflect",
    "pandas",
    "aiohttp",
]

test_requirements = ["pytest"]

docs_requirements = ["mkdocs", "mkdocstrings", "mkdocstrings.python"]

setup(
    author="Tiago Lubiana",
    author_email="tiago.lubiana.alves@usp.br",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    description="Utils for curating unstructured data into Wikidata",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="wdcuration",
    name="wdcuration",
    packages=find_packages(include=["wdcuration", "wdcuration.*"]),
    extras_require={"tests": test_requirements, "docs": docs_requirements},
    url="https://github.com/lubianat/wdcuration",
    version="0.2.1",
    zip_safe=False,
)
