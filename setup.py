#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
from shutil import rmtree
from setuptools import setup, Command, find_packages

# Package meta-data.
NAME = 'permon'
DESCRIPTION = 'A tool to monitor everything you want. Clean, simple, extensible and in one place.'  # noqa: E501
URL = 'https://github.com/bminixhofer/permon'
EMAIL = 'bminixhofer@gmail.com'
AUTHOR = 'Benjamin Minixhofer'
REQUIRES_PYTHON = '>=3.6.0'

REQUIRED = [
    'psutil',  # required for measuring RAM, CPU etc
    'appdirs',  # required to find out user config and data directorires
    'jupyter',  # required to measure ram usage in a jupyter notebook
    'pympler'  # required to measure the size of the variables in the notebook
]

here = os.path.abspath(os.path.dirname(__file__))
package_root = os.path.join(here, 'permon')
VERSION = open(os.path.join(package_root, 'VERSION')).read()


with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'
                  .format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(VERSION))
        os.system('git push --tags')

        sys.exit()


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['permon=permon:main'],
    },
    install_requires=REQUIRED,
    package_data={
        'permon': [
            'VERSION',
            'backend/stats/*.py',
            'frontend/assets/*',
            'frontend/assets/**/*',
            'frontend/native/qml/*',
            'frontend/browser/dist/*',
            'frontend/browser/static/*.html',
            'frontend/browser/templates/*.html'
        ]
    },
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)
