from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="flask_fast",
    version="0.0.1-dev0",
    description="Flask-fast. It's fast.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lucasdurand/flask-fast",
    author="Lucas Durand",
    author_email="lucas@lucasdurand.xyz",
    tests_require=["pytest"],
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.7",
    install_requires=[
        "pandas",
        "dash",
        "flask",
    ],  # dash could be optional here if we re-write the function to action on a flask app
    extras_require={"dev": ["black", "pre-commit"], "test": ["coverage"]},
)
