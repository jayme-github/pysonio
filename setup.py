#!/usr/bin/env python

from setuptools import setup


def parse_requirements(path):
    with open(path, 'r') as infile:
        return [l.strip() for l in infile.readlines()]


setup(
    name='pysonio',
    version='0.1',
    description='incomplete library to personio time tracking',
    long_description=open('README.rst', 'r').read(),
    platforms=['any'],
    keywords='personio',
    author='Jayme',
    author_email='tuxnet@gmail.com',
    url='https://github.com/jayme-github/pysonio',
    packages=['pysonio'],
    license='GNU Affero General Public License v3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=parse_requirements('requirements.txt'),
    # tests_require=parse_requirements('requirements-test.txt'),
    # test_suite='test',
    # scripts=['demo.py'],
)
