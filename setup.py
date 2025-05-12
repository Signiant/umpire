from setuptools import setup, find_packages
from os import path

setup(name='Umpire',
      version='0.8.2',
      description='Generic dependency resolver.',
      long_description='',
      long_description_content_type='text/markdown',
      author='Signiant SRE',
      author_email='sre@signiant.com',
      url='https://www.signiant.com',
      packages=find_packages(),
      license='MIT',
      install_requires=[
          'MaestroOps>=0.9',
          'tqdm>=4.64.1'
      ],
      entry_points = {
          'console_scripts': [
              'umpire = umpire.umpire:entry'
              ]
          }
     )
