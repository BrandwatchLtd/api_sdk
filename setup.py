from setuptools import setup, find_packages

requirements = ["requests>=2.22.0"]

setup_requirements = ["pytest-runner", "setuptools>=38.6.0", "wheel>=0.31.0"]

test_requirements = ["pytest", "responses"]

with open("README.md") as infile:
    long_description = infile.read()


setup(
    name="bwapi",
    version="4.1.0",
    description="A software development kit for the Brandwatch API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BrandwatchLtd/api_sdk",
    author="Amy Barker, Jamie Lebovics, Paul Siegel and Jessica Bowden",
    author_email="amyb@brandwatch.com, paul@brandwatch.com, jess@brandwatch.com",
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
    packages=find_packages(where="src", include=["bwapi"]),
    package_dir={"": "src"},
    entry_points={"console_scripts": ["bwapi-authenticate = bwapi.authenticate:main"]},
    install_requires=requirements,
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    python_requires=">=3.5",
    test_suite="tests",
)
