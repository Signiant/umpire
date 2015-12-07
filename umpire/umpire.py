from __future__ import print_function
from maestro.core import execute
from maestro.aws import s3

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
        self.register_dependencies()

        #Get the instance of our first module
        deployer = self.getObject("deploy")

        #TODO: Fix to use just RUN
        deployer.cache_root = self.get_cache_root()

        #Run it
        self.exit_code = deployer.run(kwargs)


    def get_cache_root(self):
        hardcoded_root = "./umpirecache_tmp"
        try:
            if not os.path.exists(config.default_cache_location):
                os.makedirs(config.default_cache_location)
            return config.default_cache_location
        except Exception as e:
            print("Umpire: Error creating default cache location, using local directory './umpirecache_tmp': " + str(e), file=sys.stderr)
            if not os.path.exists(hardcoded_root):
                os.makedirs(hardcoded_root)
            return hardcoded_root

