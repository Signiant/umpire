from setuptools import setup, find_packages
from distutils.core import setup

setup(name='Umpire',
      version='0.5.0a2',
      description='Generic dependency resolver.',
      author='Matthew Corner',
      author_email='mcorner@signiant.com',
      url='https://www.signiant.com',
      packages=find_packages(),
      license='MIT',
      install_requires=['MaestroOps>=0.4.1,<0.5'],
      entry_points = {
          'console_scripts': [
              'umpire = umpire.umpire:entry'
              ]
          }
     )
