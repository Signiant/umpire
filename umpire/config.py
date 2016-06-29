import os,sys

umpire_root = os.path.join(os.path.expanduser("~"), ".umpire")

if not os.path.exists(os.path.join(umpire_root, "config.py")):
    from shutil import copyfile
    copyfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.py"), os.path.join(umpire_root,"config.py"))
sys.path.insert(0,umpire_root)

from config import *
