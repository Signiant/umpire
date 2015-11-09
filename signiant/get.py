"""get.py"""

HELPTEXT = """
                  ----- Get Module -----

The get module locates a "package" using arbitrary identifiers. It will return a local directory. 

-c, --cache-location <root>:    Specify the local cache directory (must exist)
                                    (required)
-m, --max-threads <#>:          Specify the maximum amount of download threads
                                    (default 5)
-n, --name <name>:              Specify the dependency name
                                    (default source file name)
-p, --platform <platform>:      Specify the target platform
                                    (required)
-r, --repository <url>:          Specify the root of the repository to obtain files.
                                    (required)
-v, --version <version>:        Specify the target version
                                    (default latest)

"""

import sys, os, urllib2, requests
from multiprocessing import Value
from maestro.internal.module import *
from maestro.tools.file import read_blocks

CACHE_LOCATION_KEYS = ["c", "cache-location"]
MAX_THREAD_KEYS = ["m", "max-threads"]
DEPENDENCY_NAME_KEYS = ["n", "name"]
DEPENDENCY_PLATFORM_KEYS = ["p", "platform"]
DEPENDENCY_REPOSITORY_KEYS = ["r", "repository"]
DEPENDENCY_VERSION_KEYS = ["v", "version"]
HELP_KEYS = ["h", "help"]


class GetModule(AsyncModule):
    # Required ID of this module
    id = "get"
    
    #Initialize shm value
    progress = Value('d', 0.0)

    # Required help text
    help_text = HELPTEXT

    # Maximum amount of download threads (for downloading folders)
    max_threads = 5

    cache_location = None
    max_threads = 5
    dependency_name = None
    dependency_platform = None
    dependency_repo = None
    dependency_version = None

    def run(self,kwargs):
        #Catch all exceptions since we need to set self.exception
        try:
            self.__parse_kwargs__(kwargs)
            self.__verify_arguments__()
            self.__download__()
            if self.verify_md5 is True:
                self.__verify_md5__()
        except Exception as e:
            return e
        return True

    def __parse_kwargs__(self,kwargs):
        for key, val in kwargs.iteritems():
            if key in CACHE_LOCATION_KEYS:
                self.cache_location = val
            elif key in MAX_THREAD_KEYS:
                self.max_threads = int(val)
            elif key in DEPENDENCY_NAME_KEYS:
                self.dependency_name = val
            elif key in DEPENDENCY_PLATFORM_KEYS:
                self.dependency_platform = val
            elif key in DEPENDENCY_REPOSITORY_KEYS:
                self.dependency_repo = val
            elif key in DEPENDENCY_VERSION_KEYS:
                self.dependency_version = val

    def __verify_arguments__(self):
        if self.source_url is None or not isinstance(self.source_url, basestring):
            raise TypeError("The source URL must be a valid string!")

        if self.dest_path is None:
            self.dest_path = os.path.abspath('.')

        if self.dest_filename is None:
            from urlparse import urlsplit
            path = urlsplit(self.source_url).path
            self.dest_filename = os.path.basename(path)
        
    def __verify_md5__(self):
        from urllib2 import urlopen
        from hashlib import md5
        remote_md5 = urlopen(target_url + ".md5").readlines()
        local_md5 = md5(open(os.path.join(self.dest_path,self.dest_filename),'rb').read()).hexdigest()
        
        if remote_md5.strip() == local_md5.strip():
            return True
        else:
            return False

    def __download__(self):
        response = requests.get(self.source_url, stream=True)
        if response.headers["content-type"] != 'application/octet-stream':
            pass #Possibly do something with the headers in the future, for now binary!
        try:
            total_size = int(response.headers["Content-Length"])
        except KeyError:
            total_size = -1
            self.progress.value = -1.0


        with open(os.path.join(self.dest_path, self.dest_filename), "wb") as file:
            bytes_read = 0
            for data in response.iter_content(chunk_size=self.block_size):
                bytes_read += self.block_size
                file.write(data)
                if total_size > 0:
                    self.progress.value = float(bytes_read) / float(total_size) * 100
        if not os.path.exists(os.path.join(self.dest_path, self.dest_filename)):
            raise DownloadError("The file failed to download.")
            
if __name__ == "__main__":
    import time
    current_key = None
    keyvals = dict()
    for arg in sys.argv[1:]:
        if current_key is None:
            current_key = arg.lstrip('-')
            continue
        if not arg.startswith("-"):
            keyvals[current_key] = arg
            current_key = None
        else:
            keyvals[current_key] = None
            current_key = arg.lstrip('-')
    if current_key is not None and current_key not in keyvals.keys():
        keyvals[current_key] = ""
    static_dl = DownloadModule(None)
    #static_dl.run(keyvals)
    dl = DownloadModule(None)
    dl.start(keyvals)
    while dl.status != DONE:
        if dl.exception is not None:
            raise dl.exception
        print "Progress: " + str(dl.progress.value)
        time.sleep(1)
    if dl.exception is not None:
        raise dl.exception
