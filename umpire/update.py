import urllib2
import sys

from .umpire import __version__
from . import config
import umpire, os
from maestro.core import module

HELP_KEYS = ["h", "help"]
UPDATE_KEYS = ["u", "update"]

def parse_version_string(version):
    """
    Returns a tuple containing the major, minor, revision integers
    """
    nums = version.split(".")
    return int(nums[0]), int(nums[1]), int(nums[2])

def __run_pip__():
    from subprocess import call
    call(["pip","install","umpire", "--upgrade"])

def __restart_umpire__():
    from subprocess import call
    args = list(sys.argv)
    args.insert(1, "--skip-update")
    call(args)

class UpdateModule(module.AsyncModule):
    # Required ID of this module
    id = "update"

    def help(self):
        print(self.help_text)
        exit(0)

    def write_remote_version(self, version):
        with open(os.path.join(umpire.get_umpire_root(),"remote_version"), "w+") as f:
            f.write(version)

    def get_remote_version(self):
        return urllib2.urlopen(config.REMOTE_VERSION_URL).read()

    def run(self,kwargs):
        version = self.get_remote_version()
        self.write_remote_version(version)
        for key in UPDATE_KEYS:
            if key in kwargs.keys():
                __run_pip__()
                __restart_umpire__()
