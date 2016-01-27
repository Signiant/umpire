from __future__ import print_function
from maestro.core import execute
from maestro.aws import s3
from maestro.tools import path

import sys,os

#Internal Modules
from . import fetch, unpack, deploy

#Config
from . import config

#Entry point for Umpire
def entry():
    exit_code = Umpire().exit_code
    sys.exit(exit_code)

class Umpire(execute.ModuleExecuter):

    #
    # !!!Register all the dependencies of this program here.!!!
    #
    def register_dependencies(self):
        self.register(s3.AsyncS3Downloader())
        self.register(fetch.FetchModule())
        self.register(unpack.UnpackModule())
        self.register(deploy.DeploymentModule())

    def run(self, kwargs):
        #TODO: Add these as modules
        for index, item in enumerate(sys.argv):
            if index == 0:
                continue
            if item == "-c" or item == "--clear-cache":
                import shutil
                shutil.rmtree(self.get_umpire_root())
                sys.exit(0)
            elif item == "-r" or item == "--repair-cache":
                path.purge(".umplock", self.get_umpire_root())
                sys.exit(0)

        self.register_dependencies()

        #Get the instance of our first module
        deployer = self.getObject("deploy")

        #TODO: Fix to use just RUN
        deployer.cache_root = self.get_umpire_root()

        try:
            #Run it
            self.exit_code = deployer.run(kwargs)
        except KeyboardInterrupt:
            print("Got KeyboardInterrupt. Cleaning lock files.")
            path.purge(".umplock", self.get_umpire_root())
            sys.exit(1)


    def get_umpire_root(self):
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
