from setuptools import setup, find_packages
from distutils.core import setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='Umpire',
      version='0.6.2',
      description='Generic dependency resolver.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Matthew Corner',
      author_email='mcorner@signiant.com',
      url='https://www.signiant.com',
      packages=find_packages(),
      license='MIT',
      install_requires=['MaestroOps>=0.8.6,<0.9'],
      entry_points = {
          'console_scripts': [
              'umpire = umpire.umpire:entry'
              ]
          }
     )
