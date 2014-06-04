#!/usr/bin/env python
from setuptools import setup

VERSION = "0.5"
REPO = "https://github.com/duedil-ltd/python-sloq"

setup(
    name="sloq",
    version=VERSION,
    description="Rate-limited Queue",
    author="Paul Scott",
    author_email="paul@duedil.com",
    url=REPO,
    download_url="%s/tarball/%s" % (REPO, VERSION),
    py_modules=["sloq"],
    test_suite="test_sloq",
    license="MIT",
    keywords=["queue rate limit slow token bucket".split()],
    classifiers=[],
)
