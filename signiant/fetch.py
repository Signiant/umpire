"""fetch.py"""


import sys, os, urllib
from multiprocessing import Value
from maestro.internal.module import *
from maestro.aws.s3 import AsyncS3Downloader

CACHE_LOCATION_KEYS = ["c", "cache-location"]
DEPENDENCY_NAME_KEYS = ["n", "name"]
DEPENDENCY_PLATFORM_KEYS = ["p", "platform"]
DEPENDENCY_REPOSITORY_KEYS = ["r", "repository"]
DEPENDENCY_VERSION_KEYS = ["v", "version"]
HELP_KEYS = ["h", "help"]

class EntryError(Exception):
    pass

class FetchModule(AsyncModule):

    HELPTEXT = """
                  ----- Fetch Module -----

The fetch module locates a "package" using arbitrary identifiers. It will return a local directory. 

-c, --cache-location <root>:    Specify the local cache directory (must exist)
                                    (required)
-n, --name <name>:              Specify the dependency name
                                    (default source file name)
-p, --platform <platform>:      Specify the target platform
                                    (required)
-r, --repository <url>:          Specify the root of the repository to obtain files.
                                    (required)
-v, --version <version>:        Specify the target version
                                    (default latest)

"""

    # Required ID of this module
    id = "fetch"
    
    #Initialize shm value
    progress = Value('d', 0.0)

    # Version of dependency (Default latest)
    dependency_version = None

    ### Required Variables ###
    #Location of the cache
    cache_location = None

    #Name of dependency to fetch
    dependency_name = None

    #Name of platform of dependency to fetch
    dependency_platform = None

    #The repository to fetch the dependency, or to verify the integrity from
    dependency_repo = None

    def run(self,kwargs):
        #Catch all exceptions since we need to return the exception
        try:
            pass            
        except Exception as e:
            return e
        return True

    def __check_local_cache__(self):
        if not os.path.exists(self.cache_location):
            raise EntryError("The cache location provided does not exist.")
        try:
            found_location = maestro.tools.path.get_case_insensitive_path(__get_entry_cache_location__())
            return found_location
        except OSError:
            return None #Not found in cache

    def __get_entry_cache_location__(self):
        """
        Returns a concatination of the path elements where the entry should be located in the cache. DOES NOT CHECK IF IT EXISTS!
        """
        return os.path.join(self.cache_location, self.dependency_platform, self.dependency_name, self.dependency_version, "/")

    def __get_entry_remote_location__(self):
        return urllib.parse.urlunsplit(self.dependency_repo, self.dependency_platform, self.dependency_name, self.dependency_version, "/")
    
    def __download_entry__(self):
        """
        Downloads the file to the cache
        """
        s3dl = AsyncS3Downloader(None)
        s3dl.start({"source" : __get_entry_remote_location__(), "destination" : __get_entry_cache_location__(), "case-insensitive" : ""})
        

    def __check_remote_repository__(self):
        pass

    def __parse_kwargs__(self,kwargs):
        if kwargs is None:
            return
        for key, val in kwargs.iteritems():
            if key in CACHE_LOCATION_KEYS:
                self.cache_location = val
            elif key in DEPENDENCY_NAME_KEYS:
                self.dependency_name = val
            elif key in DEPENDENCY_PLATFORM_KEYS:
                self.dependency_platform = val
            elif key in DEPENDENCY_REPOSITORY_KEYS:
                self.dependency_repo = val
            elif key in DEPENDENCY_VERSION_KEYS:
                self.dependency_version = val

    def __verify_arguments__(self):
        if self.cache_location is None:
            raise TypeError("You must specify a cache location.")
        if not os.path.exists(self.cache_location):
            raise ValueError("Cache location specified does not exist.")
        if self.dependency_name is None:
            raise TypeError("You must specify a name for the dependency to fetch.")
        if self.dependency_platform is None:
            raise TypeError("You must specify the platform to fetch a dependency for.")
        if self.dependency_repo is None:
            raise TypeError("You must specify a repository to fetch and verify integrity from.")

if __name__ == "__main__":
    pass
