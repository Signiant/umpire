"""deploy.py"""

HELPTEXT = """
                  ----- Umpire -----

The deploy module reads an umpire deployment JSON file.

Usage: umpire <deployment_file>

"""

import sys, os, json, time
from maestro.core import module
from maestro.tools import path

#Local modules
import fetch, cache
from cache import CacheError

CACHE_ROOT_KEYS = ["c", "with-cache"]
HELP_KEYS = ["h", "help"]

class DeploymentError(Exception):
    pass

class DeploymentModule(module.AsyncModule):
    # Required ID of this module
    id = "deploy"

    #Cache Root
    cache_root = None

    #Set to true to view tracebacks for exceptions
    DEBUG = False

    def help(self):
        print(self.help_text)
        exit(0)

    def run(self,kwargs):
        json_index = 1
        try:
            for index, item in enumerate(sys.argv):
                if index == 0:
                    continue
                if item == "-d" or item == "--debug":
                    self.DEBUG = True
                elif item.startswith("-"):
                    pass #ignore
                else:
                    json_index = index

            with open(sys.argv[json_index]) as f:
                data = json.load(f)
        except IndexError:
            print(HELPTEXT)
            sys.exit(1)
        except IOError as e:
            if not self.DEBUG:
                print("Unable to locate file: " + sys.argv[json_index])
            else:
                raise e
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
                fetcher.cache_root = self.cache_root

                #TODO: Figure out how to move this out of deploy
                try:
                    cache_dir =  os.path.join(fetcher.cache_root, fetcher.get_cache_name())
                    cache.create_local_cache(cache_dir, repo_url)
                except CacheError:
                    pass #Cache already exists
                fetcher.start()
                fetchers.append((fetcher,destination))

        done_count = 0
        exit_code = 0
        while done_count < len(fetchers):
            done_count = 0
            for fetcher, destination in fetchers:
                if fetcher.status == module.PROCESSED:
                    done_count += 1
                    continue
                if not os.path.exists(destination):
                    os.makedirs(destination)
                if fetcher.status == module.DONE and fetcher.exception is not None:
                    if self.DEBUG:
                        print (fetcher.exception.traceback)
                    else:
                        print (fetcher.format_entry_name() + ": ERROR -- " + str(fetcher.exception))
                    exit_code = 1
                    fetcher.status = module.PROCESSED
                if fetcher.status == module.DONE and fetcher.exception is None:
                    files = fetcher.result[0]
                    state = fetcher.result[1]
                    for entry in files:
                        destination_file = os.path.join(destination,os.path.split(entry)[1])
                        if (os.path.exists(destination_file) or os.path.islink(destination_file)) and state == fetch.EntryState.CACHE:
                            print (fetcher.format_entry_name() + ": Already deployed at latest.")
                            fetcher.status = module.PROCESSED
                            break
                        elif (os.path.exists(destination_file) or os.path.islink(destination_file)) and state == fetch.EntryState.DOWNLOADED:
                            print (fetcher.format_entry_name() + ": Re-deploying " + destination_file)
                            os.remove(destination_file)
                            path.symlink(entry, destination_file)
                        elif (os.path.exists(destination_file) or os.path.islink(destination_file)) and state == fetch.EntryState.UPDATED:
                            print (fetcher.format_entry_name() + ": Updating " + destination_file)
                            os.remove(destination_file)
                            path.symlink(entry, destination_file)
                        else:
                            print (fetcher.format_entry_name() + ": Linking " + destination_file)
                            path.symlink(entry, destination_file)

                        #TODO: Kinda hacky, no significance other than to make it not DONE
                        fetcher.status = module.PROCESSED

                if fetcher.status == module.PROCESSED:
                    done_count += 1
            time.sleep(0.1)
        return exit_code
