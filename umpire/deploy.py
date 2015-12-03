"""deploy.py"""

HELPTEXT = """
                  ----- Umpire -----

The deploy module reads an umpire deployent JSON file.

Usage: umpire <deployment_file>

"""

import sys, os, json
from maestro.internal import module
from maestro.tools import path

#Local modules
import fetch, cache
from cache import CacheError
from config import default_cache_location

HELP_KEYS = ["h", "help"]
    
#TODO: Settings file from setup.py
def get_cache_root():
    hardcoded_root = "./cache"
    try:
        if not os.path.exists(default_cache_location):
            os.makedirs(default_cache_location)
        return default_cache_location
    except Exception as e:
        print "Error creating default cache location, using local directory './cache': " + str(e) 
        if not os.path.exists(hardcoded_root):
            os.makedirs(hardcoded_root)
        return hardcoded_root

class DeploymentModule(module.AsyncModule):
    # Required ID of this module
    id = "deploy"

    #Set to true to view tracebacks for exceptions
    DEBUG = False

    def help(self):
        print self.help_text
        exit(0)


    def run(self,kwargs):
        import json, time
        data = None
        
        try:
            with open(sys.argv[1]) as f:
                data = json.load(f)
        except:
            print HELPTEXT
            sys.exit(1)

        fetchers = list()

        for repo in data:
            repo_url = repo["url"]
            for item in repo["items"]:
                name = item["name"]
                version = item["version"]
                platform = item["platform"]
                destination = item["destination"]

                fetcher = fetch.FetchModule(None)
                fetcher.dependency_name = name
                fetcher.dependency_version = version
                fetcher.dependency_platform = platform
                fetcher.dependency_repo = repo_url
                fetcher.cache_root = get_cache_root()

                #TODO: Figure out how to move this out of deploy
                try:
                    cache_dir =  os.path.join(fetcher.cache_root, fetcher.get_cache_name())
                    cache.create_local_cache(cache_dir, repo_url)
                except CacheError:
                    pass #Cache already exists
                fetcher.start()
                fetchers.append((fetcher,destination))

        done_count = 0
        while done_count < len(fetchers):
            done_count = 0
            for fetcher, destination in fetchers:
                if not os.path.exists(destination):
                    os.makedirs(destination)
                if fetcher.status == module.DONE:
                    #Check for an exception, raise the full trace if in debug
                    if fetcher.exception is not None:
                        if self.DEBUG:
                            raise fetcher.exception
                        else:
                            print fetcher.format_entry_name() + ": ERROR -- " + str(fetcher.exception)
                        #TODO: Kinda hacky, no significance other than to make it not DONE
                        fetcher.status = -22

                    for entry in fetcher.result:
                        destination_file = os.path.join(destination,os.path.split(entry)[1])
                        if os.path.exists(destination_file) or os.path.islink(destination_file):
                            print fetcher.format_entry_name() + ": Already deployed."
                            fetcher.status = -22
                            break
                        print fetcher.format_entry_name() + ": Linking " + destination_file
                        path.symlink(entry, destination_file)
                        #TODO: Kinda hacky, no significance other than to make it not DONE
                        fetcher.status = -22

                if fetcher.status == -22:
                    done_count += 1

if __name__ == "__main__":
    dp = DeploymentModule(None)
    dp.run(None)
