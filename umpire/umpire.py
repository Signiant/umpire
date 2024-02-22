from maestro.core import execute
from maestro.aws import s3
from maestro.tools import path
import logging
import logging.handlers
import logging.config
import argparse

__version__ = "0.5.5"

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

        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        parser = argparse.ArgumentParser(description='Umpire reads a properly formatted JSON deployment file to deploy files.')
        parser.add_argument('-c', '--clear-cache', help='Clear umpire cache', dest='clear', action='store_true', required=False)
        parser.add_argument('-r', '--repair-cache', help='Removes lock files from the cache', dest='repair', action='store_true', required=False)
        parser.add_argument('-v', '--version', help='Displays the current version of Umpire', dest='version',  action='store_true', required=False)
        parser.add_argument('UMPIRE_FILE', help='Umpire json manifest file', nargs='?')
        parser.add_argument('-d', '--debpug', help='Run without creating keys or updating keys', dest='debug', action='store_true',
                            required=False)
        args = parser.parse_args()


        log_level = logging.INFO
        if args.debug:
            print('DEBUG logging requested')
            log_level = logging.DEBUG
            self.debug = True

        logger = logging
        FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
        logger.basicConfig(format=FORMAT, stream=sys.stdout, level=log_level)

        if args.clear:
            import shutil
            logger.info("Clearing cache...")
            shutil.rmtree(get_umpire_root())
            logger.info("Completed")
            sys.exit(0)

        if args.repair:
            logger.info("Repairing cache...")
            path.purge(config.LOCK_FILENAME, get_umpire_root())
            logger.info("Completed")
            sys.exit(0)

        if args.version:
            from subprocess import call
            call(["pip3","show","umpire"])
            sys.exit(0)
        # elif item == "-s" or item == "--skip-update":
        #     self.skip_update = True


        if args.UMPIRE_FILE:
            self.deployment_file = args.UMPIRE_FILE
        else:
            parser.print_help()
            sys.exit(0)
        logger.info("Welcome!")
        self.register_dependencies()
        if not self.skip_update:
            updater = self.getObject("update")
            try:
                #Check if there's an update available
                with open(os.path.join(config.REMOTE_VERSION_FILENAME), "r") as f:
                    version = f.read()
                    rmajor, rminor, rrev = update.parse_version_string(version)
                    major, minor, rev = update.parse_version_string(__version__)
                    logger.info (str(rmajor) + str(rminor) + str(rrev))
                    logger.info (str(major) + str(minor) + str(rev))
                    if (rmajor > major) or ((rminor > minor) and (rmajor == rmajor)) or ((rrev > rev) and (rminor == minor) and (rmajor == rmajor)):
                        if config.autoupdate:
                            logger.info("\n!!!Update (%s) detected!!!\n" % version[:-1])
                            logger.info("Autoupdating...\n")
                            updater.run({"update":None})
                            sys.exit(0)
                        else:
                            logger.info("!!!Update (%s) detected!!!" % version[:-1])
                            logger.info("Please run pip install umpire --upgrade as an Administrator.\n")
                            updater.start()
            except IOError:
                updater.start()



        #Get the instance of our first module
        deployer = self.getObject("deploy")

        #TODO: Fix to use just RUN
        deployer.cache_root = get_umpire_root()

        deployer.deployment_file = self.deployment_file

        deployer.DEBUG = self.debug

        self.exit_code = deployer.run(kwargs)

def get_umpire_root():
    hardcoded_root = "./umpire_tmp"
    try:
        if not os.path.exists(config.default_umpire_root):
            os.makedirs(config.default_umpire_root)
        return config.default_umpire_root
    except Exception as e:
        logging.error("Umpire: Error obtaining default umpire root location, using local directory './umpire_tmp': " + str(e), file=sys.stderr)
        if not os.path.exists(hardcoded_root):
            os.makedirs(hardcoded_root)
        return hardcoded_root
