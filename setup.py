from setuptools import setup, find_packages

requirements = ["requests>=2.22.0"]

setup_requirements = ["pytest-runner", "setuptools>=38.6.0", "wheel>=0.31.0"]

test_requirements = ["pytest", "responses"]

with open("README.md") as infile:
    long_description = infile.read()


setup(
    name="bcr",
    version="1.0.0",
    description="A client library for the Brandwatch Consumer Research API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BrandwatchLtd/api_sdk",
    author="Paul Siegel, Matthew Franglen, Colin Sullivan, Hamish Morgan and Peter Fairfax",
    author_email="paul@brandwatch.com, matthew@brandwatch.com, csullivan@brandwatch.com, peterf@brandwatch.com",
    license="License :: OSI Approved :: MIT License",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages(where="src", include=["bcr"]),
    package_dir={"": "src"},
    entry_points={"console_scripts": ["bcr-authenticate = bcr.authenticate:main"]},
    install_requires=requirements,
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    python_requires=">=3.5",
    test_suite="tests",
)
