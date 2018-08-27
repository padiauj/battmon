import os
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
import subprocess

setup(
    name = "battmon",
    version = "0.11",
    author = "Umesh Padia",
    author_email = "umeshpadia1@gmail.com",
    description = "A simple battery monitoring tool for Linux operating systems",
    license = "GPLv3",
    url = "https://github.com/padiauj/battmon",
    packages=['battmon'],
    entry_points = {
        'gui_scripts' : ['battmon = battmon.battmon:main']
    },
    data_files = [
        ('share/applications/', ['padiauj-battmon.desktop'])
    ],
    classifiers=[
        "License :: GNU GPLv3 License",
    ],
)
