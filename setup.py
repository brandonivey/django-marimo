from setuptools import setup, find_packages
import os

os.chdir('py')

setup(
    name = "marimo",
    version = "0.1",
    packages = find_packages(exclude='mtest'),
    author = "Cox Media Group",
    author_email = "opensource@coxinc.com",
    description = "a fast framework for asynchronous widgets",
    license = "MIT",
    url = "https://github.com/coxmediagroup/marimo",
)

