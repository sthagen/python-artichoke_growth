import pathlib
from setuptools import find_packages, setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()
README += "\n"
README += (HERE / "docs" / "index.md").read_text()

# This call to setup() does all the work
setup(
    name="artichoke-growth",
    version="0.0.1",
    description="Document some binary repository management storage.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/sthagen/python-artichoke_growth",
    author="Stefan Hagen",
    author_email="stefan@hagen.link",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="brm hash storage proxy index file development",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=[
        "beautifulsoup4",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "artichoke-growth=artichoke_growth.cli:main",
        ]
    },
)
