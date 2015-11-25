"""
repo.py contains code to control the local cache for umpire. It is not a module.
"""

import ConfigParser

CONFIG_FILENAME = ".umpire"

def create_local_cache(cache_name, parent_root, remote_url = None):
    """
    Creates a cache and returns a CacheCache object. NOT THREAD-SAFE.
    """
    pass
 
def get_local_cache(cache_name, parent_root, remote_url = None, create = True):
    """
    Returns a repositry in parent_root with cache_name. Will create by default if not found, and you may specify a remote. NOT THREAD SAFE.
    """
    pass

class EntryInfo(object):
    platform = None
    name = None
    version = None
    md5 = None
    path_id = None

class EntryError(Exception):
    pass

class CacheError(Exception):
    pass

class LocalCache(object):
    name = None
    local_path = None
    settings_file = None
    remote_url = None

    #Verifies local existance
    def __init__(self, cache_root):
        if not os.path.exists(cache_root):
            raise CacheError("The path '" + str(cache_root) + "' does not contain a valid umpire cache.")
        
        self.local_path = cache_root

        self.settings_file = os.path.join(cache_root,CONFIG_FILENAME)

        if not os.path.exists(self.settings_file):
            raise CacheError("The specified path does not appear to be a valid Umpire cache")
        config = None
        
        #Get parser
        parser = ConfigParser.SafeConfigParser()
        try:#Read
            config = parser.read(self.settings_file)
        except ConfigParser.ParsingError:
            raise CacheError("Error parsing the cache configuration file. Please contact an administrator for help fixing this problem.")

        #Verify the config has been read 
        if config is None:
            raise CacheError("The config file appears to be empty. Please verify this is the location of a valid umpire cache.")

        #Verify the section we're looking for is there 
        if CONFIG_SECTION_NAME not in config.sections():
            raise CacheError("The config file appears to be missing the [umpire] section. Please verify this is the location of a valid umpire cache.")
        
        #Attempt to parse the data
        try:
            self.remote_url = config.get(CONFIG_SECTION_NAME, "remote_url")
        except ConfigParser.Error:
            raise CacheError("Unable to determine the name of this cache")

        if not self.remote_url:
            raise CacheError("Unable to determine the name of this cache")


    #Gets local entry, returns None if it doesn't exist.
    def get(platform, name, version):
        pass

    #Puts a file into the cache 
    def put(file, platform, name, version, unpack=True, force=False):
        pass

    #Set the repositories remote URL (updates local .umpire_repo file)
    def set_remote(url):
        pass
