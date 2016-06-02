from __future__ import print_function
from maestro.core import execute
from maestro.aws import s3
from maestro.tools import path

__version__ = "0.4.2"

import sys,os

#Internal Modules
from . import fetch, unpack, deploy, update

from .deploy import HELPTEXT

#Config
from . import config

#Entry point for Umpire
def entry():
    exit_code = Umpire().exit_code
    sys.exit(exit_code)

class Umpire(execute.ModuleExecuter):

    #Defaults for command line flags
    skip_update = True
    debug = False
    deployment_file = None

    #
    # !!!Register all the dependencies of this program here.!!!
    #
    def register_dependencies(self):
        self.register(s3.AsyncS3Downloader())
        self.register(fetch.FetchModule())
        self.register(unpack.UnpackModule())
        self.register(deploy.DeploymentModule())
        self.register(update.UpdateModule())

    def run(self, kwargs):

        for index, item in enumerate(sys.argv):
            if index == 0:
                continue
            if item == "-c" or item == "--clear-cache":
                import shutil
                shutil.rmtree(get_umpire_root())
                sys.exit(0)
            elif item == "-r" or item == "--repair-cache":
                path.purge(config.LOCK_FILENAME, get_umpire_root())
                sys.exit(0)
            elif item == "-h" or item == "--help":
                print(deploy.HELPTEXT)
                sys.exit(0)
            elif item == "--version":
                from subprocess import call
                call(["pip","show","umpire"])
            elif item == "-s" or item == "--skip-update":
                self.skip_update = True
            elif item == "-d" or item == "--debug":
                self.debug = True
            else:
                self.deployment_file = item


        self.register_dependencies()
        if not self.skip_update:
            updater = self.getObject("update")
            try:
                #Check if there's an update available
                with open(os.path.join(config.REMOTE_VERSION_FILENAME), "r") as f:
                    version = f.read()
                    rmajor, rminor, rrev = update.parse_version_string(version)
                    major, minor, rev = update.parse_version_string(__version__)
                    print (str(rmajor) + str(rminor) + str(rrev))
                    print (str(major) + str(minor) + str(rev))
                    if (rmajor > major) or ((rminor > minor) and (rmajor == rmajor)) or ((rrev > rev) and (rminor == minor) and (rmajor == rmajor)):
                        if config.autoupdate:
                            print("\n!!!Update (%s) detected!!!\n" % version[:-1])
                            print("Autoupdating...\n")
                            updater.run({"update":None})
                            sys.exit(0)
                        else:
                            print("!!!Update (%s) detected!!!" % version[:-1])
                            print("Please run pip install umpire --upgrade as an Administrator.\n")
                            updater.start()
            except IOError:
                updater.start()



        #Get the instance of our first module
        deployer = self.getObject("deploy")

        #TODO: Fix to use just RUN
        deployer.cache_root = get_umpire_root()

        deployer.deployment_file = self.deployment_file

        deployer.DEBUG = self.debug

        try:
            #Run it
            self.exit_code = deployer.run(kwargs)
        except KeyboardInterrupt:
            print("Got KeyboardInterrupt. Cleaning lock files.")
            path.purge(".umplock", get_umpire_root())
            sys.exit(1)

def get_umpire_root():
    hardcoded_root = "./umpire_tmp"
    try:
        if not os.path.exists(config.default_umpire_root):
            os.makedirs(config.default_umpire_root)
        return config.default_umpire_root
    except Exception as e:
        print("Umpire: Error obtaining default umpire root location, using local directory './umpire_tmp': " + str(e), file=sys.stderr)
        if not os.path.exists(hardcoded_root):
            os.makedirs(hardcoded_root)
        return hardcoded_root
