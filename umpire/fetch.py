"""fetch.py"""

import sys, os, urllib, time, traceback
from cache import LocalCache
from multiprocessing import Value
from maestro.core import module
from maestro.aws import s3

CACHE_LOCATION_KEYS = ["c", "cache-location"]
DEPENDENCY_NAME_KEYS = ["n", "name"]
DEPENDENCY_PLATFORM_KEYS = ["p", "platform"]
DEPENDENCY_REPOSITORY_KEYS = ["r", "repository"]
DEPENDENCY_VERSION_KEYS = ["v", "version"]
HELP_KEYS = ["h", "help"]

class EntryError(Exception):
    pass

class FetchModule(module.AsyncModule):

    HELPTEXT = """
                  ----- Fetch Module -----

The fetch module locates a "package" using arbitrary identifiers. It will return a local directory.

-c, --cache-root <path>:        Specify the local root cache directory (must exist)
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

    #Initialize shm value #TODO: Near future
    progress = Value('d', 0.0)

    # Version of dependency (Default latest) #TODO: Future
    dependency_version = None

    ### Required Variables for this Module ###
    #Location of the cache root folder (r+w by every user)
    cache_root = None

    #Name of dependency to fetch
    dependency_name = None

    #Name of platform of dependency to fetch
    dependency_platform = None

    #The repository to fetch the dependency, or to verify the integrity from
    dependency_repo = None

    def run(self,kwargs):
        if kwargs is not None:
            pass #TODO: Near future

        #Verify argument validity
        self.__verify_arguments__()

        #Get cache name from remote url
        cache_name = self.get_cache_name()

        #Get cache path
        cache_path = os.path.join(self.cache_root, cache_name)

        #Get cache object (will raise an exception if it doesn't exist)
        cache = LocalCache(cache_path)

        #Try to get entry from cache
        entry = cache.get(self.dependency_platform, self.dependency_name, self.dependency_version)

        if entry is None:
            print (self.format_entry_name() + ": Not in cache")
            full_url = s3.join_s3_url(self.dependency_repo, self.dependency_platform, self.dependency_name, self.dependency_version)

            print (self.format_entry_name() + ": Downloading " + full_url)

            #Get Downloader
            downloader = s3.AsyncS3Downloader(None)

            #Set Downloader arguments
            downloader.source_url = full_url
            downloader.destination_path = os.path.join(self.cache_root, "downloading") + os.sep
            downloader.start()

            #Wait for downloader to finish #TODO: Do something with the reported progress
            while downloader.status != module.DONE:
                time.sleep(0.5)

            #Check for an exception, if so bubble it up
            if downloader.exception is not None:
                raise downloader.exception

            print self.format_entry_name() + ": Download complete"

            if downloader.result is None or len(downloader.result) == 0:
                raise EntryError(self.format_entry_name() + ": Unable to find remote entry '" + full_url + "'")

            #Iterate of the result (downloaded files)
            for item in downloader.result:
                #TODO: MD5 verification
                print (self.format_entry_name() + ": Unpacking...")
                cache.put(item,self.dependency_platform, self.dependency_name, self.dependency_version)
            entry = cache.get(self.dependency_platform, self.dependency_name, self.dependency_version)
            if entry is None:
                raise EntryError(self.format_entry_name() + ": Error retrieving entry from cache.")
        #Entry is not None, return all the files listed in the entry that aren't the configuration files
        return [os.path.abspath(os.path.join(entry.path,f)) for f in os.listdir(entry.path) if f != ".umpire"]


    def format_entry_name(self):
        return str(self.dependency_platform) + "/" + str(self.dependency_name) + " v" + str(self.dependency_version)

    def __verify_arguments__(self):
        if not self.dependency_repo:
            raise ValueError("You must specify a valid repository URL.")
        if not self.dependency_name:
            raise ValueError("You must specify a valid name for the dependency.")
        if not self.dependency_platform:
            raise ValueError("You must specify a valid platform for the dependency.")
        if not self.dependency_version:
            raise ValueError("You must specify a valid version for the dependency.")

    def get_cache_name(self):
        try:
            bucket, prefix = s3.parse_s3_url(self.dependency_repo)
            return bucket + ".s3"
        except ValueError:
            raise ValueError("Only URLs formatted as: s3://{bucket}/ are currently accepted.")

    def __parse_kwargs__(self,kwargs):
        if kwargs is None:
            return
        for key, val in kwargs.iteritems():
            if key in CACHE_LOCATION_KEYS:
                self.cache_repo = val
            elif key in DEPENDENCY_NAME_KEYS:
                self.dependency_name = val
            elif key in DEPENDENCY_PLATFORM_KEYS:
                self.dependency_platform = val
            elif key in DEPENDENCY_REPOSITORY_KEYS:
                self.dependency_repo = val
            elif key in DEPENDENCY_VERSION_KEYS:
                self.dependency_version = val

if __name__ == "__main__":
    from cache import create_local_cache

    remote_url = "s3://thirdpartydependencies/"
    create_local_cache("./test_cache/thirdpartydependencies.s3", remote_url)
    fetcher = FetchModule(None)
    fetcher.dependency_repo = remote_url
    fetcher.cache_root = "./test_cache"
    fetcher.dependency_name = "zlib"
    fetcher.dependency_version = "1.2.8"
    fetcher.dependency_platform = "win64"

    fetcher.start()
    while fetcher.status != module.DONE:
        time.sleep(0.5)

    if fetcher.exception is not None:
        print (str(fetcher.exception))
    for item in fetcher.result:
        print (item)
    print ("Done!")
