#!/usr/bin/env python

from distutils.core import setup
import os

DATAROOTDIR = 'share'
PKGNAME = 'picc'

setup(name=PKGNAME,
      version='0.2.2',
      description='A linker for PIC relocatable objects in COFF format',
      author='Antonio Serrano Hernandez',
      author_email='toni.serranoh@gmail.com',
      url='https://github.com/aserranoh/picc',
      license='GPLv3',
      requires=['intelhex'],
      packages=['picc'],
      scripts=['bin/picc', 'bin/picc-objdump'],
      data_files=[(os.path.join(DATAROOTDIR, PKGNAME),
          ['data/processors.xml'])],
     )

