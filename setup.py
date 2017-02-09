from setuptools import setup, find_packages
from distutils.core import setup
import sys, os


install_requires = ['MaestroOps>=0.7.1', 'snapp>=0.1.2']
if sys.version_info >= (3, 0):
    install_requires.append('six>=1.10.0')

setup(name='Umpire',
      version='1.0.0',
      description='Generic dependency resolver.',
      author='Matthew Corner',
      author_email='mcorner@signiant.com',
      url='https://www.signiant.com',
      packages=find_packages(),
      license='MIT',
      install_requires=install_requires,
      entry_points = {
          'console_scripts': [
              'umpire = umpire.umpire:entry'
              ]
          }
     )
