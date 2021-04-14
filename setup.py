# -*- coding: utf-8 -*-
# Copyright 2020 wanghao
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import os
import os.path as osp
import codecs
import sys
import shutil
from subprocess import call
from setuptools import setup, find_packages
from pychariot import __version__

LIBNAME = 'pychariot'


try:
    with codecs.open('README.rst', encoding='utf-8') as f:
        long_description = f.read()
except Exception:
    long_description = ''


def get_subpackages(name):
    """Return subpackages of package *name*"""
    splist = []
    for dirpath, _dirnames, _filenames in os.walk(name):
        if 'tests' not in dirpath:
            if osp.isfile(osp.join(dirpath, '__init__.py')):
                splist.append(".".join(dirpath.split(os.sep)))
    return splist


def get_package_data(name, exclude=[]):
    """Return data files for package *name* with extensions exclude ext in
    *exclude*"""
    flist = []
    # Workaround to replace os.path.relpath (not available until Python 2.6):
    offset = len(name) + len(os.pathsep)
    for dirpath, _dirnames, filenames in os.walk(name):
        if '__pycache__' not in dirpath:
            for fname in filenames:
                if (not fname.startswith('.') and
                        not osp.splitext(fname)[1] in exclude):
                    flist.append(osp.join(dirpath, fname)[offset:])
    return flist


def clean_pychariot32():
    paths = ['build', 'dist', 'pychariot32.egg-info', 'pychariot.egg-info']
    for item in paths:
        if osp.exists(item):
            shutil.rmtree(item)


def compile_pychariot32():
    clean_pychariot32()
    call([sys.executable, 'setup32.py', 'bdist_wheel'])
    whl = [x for x in os.listdir('dist') if x.endswith('.whl')]
    if not whl:
        return
    exist_whl = [x for x in os.listdir('pychariot') if x.endswith('.whl')]
    if exist_whl:
        exist_whl_path = osp.realpath(osp.join('pychariot', whl[0]))
        os.remove(exist_whl_path)
    whl_path = osp.realpath(osp.join('dist', whl[0]))
    shutil.copyfile(whl_path, osp.join('pychariot', osp.basename(whl_path)))
    clean_pychariot32()


compile_pychariot32()


setup(
    name='pychariot',
    version=__version__,
    description='Package of a ixia chariot chrapi.dll python wrapper by rpc',
    long_description=long_description,
    keywords='python any-platform rpc ixia chariot',
    author='wanghao',
    author_email='haoyueshangren@gmail.com',
    url='https://github.com/GodSix/pychariot',
    license='Apache License, Version 2.0',
    packages=find_packages(include=['pychariot'],
                           exclude=['*.contrib', '*.docs', '*.tests']),
    install_requires=[
        'rpyc>=5.0.0',
        'rpcpy32>=3.9.0'
    ],
    platforms="any",
    python_requires='>=3.6',
    package_data={LIBNAME: get_package_data(LIBNAME)},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Natural Language :: Chinese (Simplified)',
        'Operating System :: Microsoft :: Windows'
        'Programming Language :: Python',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Communications',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
