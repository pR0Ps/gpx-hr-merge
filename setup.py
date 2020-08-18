#!/usr/bin/env python

from setuptools import setup

setup(
    name="gpx-hr-merge",
    version="0.0.1",
    description="Merge heart rate data from a Fitbit into a GPX file",
    url="https://github.com/pR0Ps/gpx-hr-merge",
    license="GPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    py_modules=["gpx_hr_merge"],
    entry_points={"console_scripts": ["gpx-hr-merge=gpx_hr_merge:main"]},
)
