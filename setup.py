# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages

setup(
    name="django-naivedatetimefield",
    packages=find_packages(),
    version="1.4.0",
    author=u"Camron Flanders",
    author_email=u"me@camronflanders.com",
    url="https://github.com/camflan/django-naivedatetimefield/",
    license="MIT",
    description="NaiveDateTimeField for storing a naive timestamp. This is "
    "useful for baking in a local timestamp.",
    long_description=open("README.md").read(),
    zip_safe=False,
    include_package_data=True,
    install_requires=["pytz"],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4",
    keywords=["django", "datetime", "field"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.8",
        "Framework :: Django :: 1.9",
        "Framework :: Django :: 1.10",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)
