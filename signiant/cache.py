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

    #Verifies local existance
    def __init__(self, cache_root):
        if not os.path.exists(cache_root):
            raise CacheError("The path to the specified cache does not exist.")
        
        self.settings_file = os.path.join(cache_root,CONFIG_FILENAME)

        if not os.path.exists(self.settings_file):
            raise CacheError("The specified path does not appear to be a valid Umpire cache")
        config = None
        
        try:
            parser = ConfigParser.SafeConfigParser()
            config = parser.read(self.settings_file)
        except ConfigParser.ParsingError:
            raise CacheError("Error parsing the cache configuration file. Please contact an administrator for help fixing this problem.")

        if config is None or len(config.sections()) == 0:
            raise CacheError("The config file appears to be empty. Please contact an administrator for help fixing this problem.")

        try:
            parser = 

    
    #Gets local entry, returns None if it doesn't exist.
    def get(platform, name, version):
        pass

    #Puts a file into the cache 
    def put(file, platform, name, version, unpack=True, force=False):
        pass

    #Set the repositories remote URL (updates local .umpire_repo file)
    def set_remote(url):
        pass
