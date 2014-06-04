#!/usr/bin/env python
from setuptools import setup

VERSION = "0.1"
REPO = "https://github.com/duedil-ltd/python-sloq"
README = "README.rst"

with open(README) as f:
    long_description = f.read()

setup(
    name="sloq",
    version=VERSION,
    description="Rate-limited Queue",
    author="Paul Scott, Duedil Limited",
    author_email="paul@duedil.com",
    url=REPO,
    download_url="%s/tarball/%s" % (REPO, VERSION),
    py_modules=["sloq"],
    test_suite="test_sloq",
    license="MIT",
    long_description=long_description,
    keywords="queue rate limit slow token bucket".split(),
    classifiers=[],
)
