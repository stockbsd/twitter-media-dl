# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here,'requirements.txt')) as fh:
    requirements = [line.strip() for line in fh.readlines()]

with open(os.path.join(here,'README.md')) as fh:
    Readme = fh.read()

def get_version():
    version_file = os.path.join(here, "twitter_dl", "__init__.py")
    for line in open(version_file):
        if line.startswith("version"):
            version = line.split("=")[1].strip().replace("'", "").replace('"', '')
            return version
    raise RuntimeError("Unable to find version string in %s" % version_file)

git_repo = "https://github.com/stockbsd/twitter-media-dl"

setup(
    name="twitter-dl",  #distribution name
    version=get_version(),
    description="Download tweet images and videos",
    long_description=Readme,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    entry_points={
        "console_scripts": [
            "twitter-dl=twitter_dl.__main__:main"
        ]
    },
    url=git_repo,
    author="stockbsd",
    author_email="stockbsd@gmail.com",
    keywords="twitter, asyncio, media",
    project_urls={"Bug Reports": git_repo, "Source": git_repo},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
