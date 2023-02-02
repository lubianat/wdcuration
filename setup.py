#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "requests",
    "SPARQLWrapper",
    "tqdm",
    "inflect",
    "pandas",
    "aiohttp",
]

test_requirements = []

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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Utils for curating unstructured data into Wikidata",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="wdcuration",
    name="wdcuration",
    packages=find_packages(include=["wdcuration", "wdcuration.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/lubianat/wdcuration",
    version="0.2.0",
    zip_safe=False,
)
