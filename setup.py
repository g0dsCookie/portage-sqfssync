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


def get_info(*args):
    contents = get_contents(*args)
    metadata = dict(re.findall(r'__([a-z]+)__\s+=\s+[\'"]([^\'"]+)', contents))
    return (metadata["version"], metadata["doc"])


mod_info = get_info("sqfssync", "__init__.py")


setup(
    name="sqfssync",
    version=mod_info[0],
    description="Portage plugin to download and mount latest SquashFS snapshot.",
    long_description=mod_info[1],
    url="https://github.com/g0dsCookie/portage-sqfssync",
    author="g0dsCookie",
    author_email="g0dscookie@cookieprojects.de",
    packages=["portage.sync.modules.sqfssync"],
    package_dir={
        "portage.sync.modules.sqfssync": "sqfssync",
    },
    license="MIT",
)
