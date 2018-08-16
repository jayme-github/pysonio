#!/usr/bin/env python

import setuptools


def parse_requirements(path):
    with open(path, 'r') as infile:
        return [l.strip() for l in infile.readlines()]


with open("README.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name='pysonio',
    version='0.0.4',
    description='incomplete library to personio time tracking',
    long_description=long_description,
    long_description_content_type='text/markdown',
    platforms=['any'],
    keywords='personio',
    author='Jayme',
    author_email='tuxnet@gmail.com',
    url='https://github.com/jayme-github/pysonio',
    packages=setuptools.find_packages(),
    license='GNU Affero General Public License v3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
    ],
    install_requires=parse_requirements('requirements.txt'),
    # tests_require=parse_requirements('requirements-test.txt'),
    # test_suite='test',
    # scripts=['demo.py'],
)
