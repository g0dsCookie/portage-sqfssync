#!/usr/bin/env python3
import codecs
import os
import re
from distutils.core import setup


def abspath(*args):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


def get_contents(*args):
    with codecs.open(abspath(*args), "r", "utf-8") as handle:
        return handle.read()


def get_version(*args):
    contents = get_contents(*args)
    metadata = dict(re.findall(r'__([a-z]+)__\s+=\s+[\'"]([^\'"]+)', contents))
    return metadata["version"]


setup(
    name="sqfssync",
    version=get_version("sqfssync", "__init__.py"),
    description="Portage plugin to download and mount latest SquashFS snapshot.",
    url="https://github.com/g0dsCookie/portage-sqfssync",
    author="g0dsCookie",
    author_email="g0dscookie@cookieprojects.de",
    packages=["portage.sync.modules.sqfssync"],
    package_dir={
        "portage.sync.modules.sqfssync": "sqfssync",
    },
    license="MIT",
)
