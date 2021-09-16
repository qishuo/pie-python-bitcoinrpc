#!/usr/bin/env python

from distutils.core import setup

setup(
    name='pie-python-bitcoinrpc',
    version='2.0',
    description='Enhanced version of python-jsonrpc for use with Bitcoin',
    long_description_content_type='text/markdown',
    long_description=open('README.rst').read(),
    author='qishuo',
    author_email='<me@qishuo.net>',
    maintainer='qishuo',
    maintainer_email='<me@qishuo.net>',
    url='https://www.github.com/qishuo/pie-python-bitcoinrpc',
    packages=['bitcoinrpc'],
    classifiers=[
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)', 'Operating System :: OS Independent'
    ]
)
