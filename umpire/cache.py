"""
repo.py contains code to control the local cache for umpire. It is not a module.
"""
#TODO: Add support for zip, tbz/tar.bz
#TODO: Write command line module

import os, shutil, time, traceback
import ConfigParser
import maestro.tools.path
import maestro.tools.file
import maestro.core.module
from urlparse import urlparse
from unpack import UnpackModule
from maestro.tools.os_tools import check_pid
from . import config

# Cache constants
CONFIG_FILENAME = config.CONFIG_FILENAME
CONFIG_REPO_SECTION_NAME = config.CONFIG_REPO_SECTION_NAME
CONFIG_ENTRY_SECTION_NAME = config.CONFIG_ENTRY_SECTION_NAME
LOCK_FILENAME = config.LOCK_FILENAME
CURRENT_ENTRY_CONFIG_VERSION = config.CURRENT_ENTRY_CONFIG_VERSION
CURRENT_REPO_CONFIG_VERSION = config.CURRENT_REPO_CONFIG_VERSION

def backoff(seconds=5):
    """
    Backoff for a random interval of time up to the amount in seconds provided (default: 5)
    """
    import random
    backoff_time = int(random.random() * seconds * 10)
    time.sleep(backoff_time)

def create_local_cache(local_path, remote_url):
    """
    Creates a cache and returns a LocalCache object. NOT THREAD-SAFE.
    """
    cache_config = os.path.join(local_path, CONFIG_FILENAME)
    if os.path.exists(cache_config):
        raise CacheError("A cache already exists in the specified location: " + local_path)

    try:
        os.makedirs(local_path)
    except OSError as e:
        pass #Directories exist

    ## Start creating config
    config = ConfigParser.SafeConfigParser()
    config.add_section(CONFIG_REPO_SECTION_NAME)

    config.set(CONFIG_REPO_SECTION_NAME, "remote_url", remote_url)
    config.set(CONFIG_REPO_SECTION_NAME, "config_version", CURRENT_REPO_CONFIG_VERSION)

    with open(cache_config, "w+") as f:
        config.write(f)

    return LocalCache(local_path)

def get_lockfile_info(lockfile):
    with open(lockfile, 'r') as lf:
        try:
            lockfile_line = lf.readline()
            lockfile_content = lockfile_line.split("::")
            lockfile_host_id = lockfile_content[0]
            lockfile_pid = int(lockfile_content[1])
            return lockfile_host_id, lockfile_pid
        except IndexError, ValueError:
            #Lockfile seems like it might be corrupted. We'll back off. The writing process(es) should have detected this, and will remove and backoff
            raise EntryLockError("Lockfile appears corrupted. Try running 'umpire -r' and retrying.")

def read_entry(file_location):
    if not os.path.exists(file_location):
        raise EntryError("Unable to find entry file under: " + file_location)

    #Get parser
    parser = ConfigParser.SafeConfigParser()
    try:#Read
        config = parser.read(file_location)
    except ConfigParser.ParsingError:
        raise EntryError("Error parsing the entry configuration file: " + file_location + " Please contact an administrator for help fixing this problem.")

    #Verify the config has been read
    if config is None:
        raise EntryError("The config file: " + file_location + " appears to be empty. Please verify this is the location of a valid umpire cache entry.")

    #Verify the section we're looking for is there
    if CONFIG_ENTRY_SECTION_NAME not in parser.sections():
        raise EntryError("The config file " + file_location + " appears to be missing the [umpire] section. Please verify this is the location of a valid umpire cache entry, or delete the containing folder and try again.")

    entry = EntryInfo()

    #Set file location
    entry.path = os.path.split(file_location)[0]

    #Attempt to parse the md5
    try:
        entry.md5 = parser.get(CONFIG_ENTRY_SECTION_NAME, "md5")
    except ConfigParser.Error:
        pass #TODO: Future
    if not entry.md5:
        pass #TODO: Future

    #Attempt to parse the entry product name
    try:
        entry.name = parser.get(CONFIG_ENTRY_SECTION_NAME, "name")
    except ConfigParser.Error:
        raise EntryError("Unable to parse name from entry file: " + file_location)
    if not entry.name:
        raise EntryError("Unable to parse name from entry file: " + file_location)

    #Attempt to parse the entry platform name
    try:
        entry.platform = parser.get(CONFIG_ENTRY_SECTION_NAME, "platform")
    except ConfigParser.Error:
        raise EntryError("Unable to parse platform from entry file: " + file_location)
    if not entry.name:
        raise EntryError("Unable to parse platform from entry file: " + file_location)

    #Attempt to parse the entry version
    try:
        entry.version = parser.get(CONFIG_ENTRY_SECTION_NAME, "version")
    except ConfigParser.Error:
        raise EntryError("Unable to parse version from entry file: " + file_location)
    if not entry.name:
        raise EntryError("Unable to parse version from entry file: " + file_location)

    #Attempt to parse the entry config version
    try:
        entry.config_version = parser.get(CONFIG_ENTRY_SECTION_NAME, "config_version")
    except ConfigParser.Error:
        raise EntryError("Unable to parse config_version from entry file: " + file_location)
    if not entry.config_version:
        raise EntryError("Unable to parse config_version from entry file: " + file_location)

    try:
        entry.config_version = parser.get(CONFIG_ENTRY_SECTION_NAME, "md5")
    except ConfigParser.Error:
        entry.md5 = None

    return entry

def write_entry(entry):

        ## Start creating config
        config = ConfigParser.SafeConfigParser()
        config_path = os.path.join(entry.path, CONFIG_FILENAME)
        config.add_section(CONFIG_ENTRY_SECTION_NAME)

        config.set(CONFIG_ENTRY_SECTION_NAME, "name", entry.name)
        config.set(CONFIG_ENTRY_SECTION_NAME, "platform", entry.platform)
        config.set(CONFIG_ENTRY_SECTION_NAME, "version", entry.version)
        config.set(CONFIG_ENTRY_SECTION_NAME, "config_version", CURRENT_ENTRY_CONFIG_VERSION)

        if entry.md5:
            config.set(CONFIG_ENTRY_SECTION_NAME, "md5", entry.md5)

        with open(os.path.join(entry.path, CONFIG_FILENAME), "w+") as f:
            return config.write(f)

class EntryInfo(object):
    config_version = None
    md5 = None
    name = None
    path = None
    platform = None
    version = None

class EntryError(Exception):
    pass

class EntryLockError(Exception):
    pass

class EntryLockTimeoutError(Exception):
    pass

class CacheError(Exception):
    pass

class LocalCache(object):
    local_path = None
    settings_file = None
    remote_url = None
    config_version = None
    host_id = None

    #Lock timeout in seconds
    lock_timeout = None

    #Verifies local existance
    def __init__(self, cache_root, lock_timeout = 1800, host_id="localhost"):
        if not os.path.exists(cache_root):
            raise CacheError("The path '" + str(cache_root) + "' does not contain a valid umpire cache.")

        self.local_path = cache_root
        self.lock_timeout = lock_timeout
        self.host_id = host_id
        self.settings_file = os.path.join(cache_root,CONFIG_FILENAME)

        if not os.path.exists(self.settings_file):
            raise CacheError("The path '" + str(cache_root) + "' does not appear to be a valid umpire cache")
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
        if CONFIG_REPO_SECTION_NAME not in parser.sections():
            raise CacheError("The config file appears to be missing the [umpire] section. Please verify this is the location of a valid umpire cache.")

        #Attempt to parse the data
        try:
            self.remote_url = parser.get(CONFIG_REPO_SECTION_NAME, "remote_url")
        except ConfigParser.Error:
            raise CacheError("Unable to determine the remote URL of this cache" + self.local_path)

        if not self.remote_url:
            raise CacheError("Unable to determine the remote URL of this cache:" + self.local_path)

        try:
            self.config_version = parser.get(CONFIG_REPO_SECTION_NAME, "config_version")
        except ConfigParser.Error:
            raise CacheError("Unable to determine the version of this cache: " + self.local_path)

        if not self.config_version:
            raise CacheError("Unable to determine the version of this cache: " + self.local_path)

    #Gets EntryInfo object, returns None if it doesn't exist.
    def get(self, platform, name, version):
        cs_entry_file = os.path.join(self.local_path, platform, name, version, ".umpire")
        entry_file = maestro.tools.path.get_case_insensitive_path(path=cs_entry_file)
        if entry_file is None:
            return None
        else:
            return read_entry(entry_file)

    #Locks a local entry
    def lock(self, path, retry_count=5):
        """
        Locks a cache entry in order to perform actions on the cache.
        """

        lockfile = os.path.join(path, LOCK_FILENAME)
        timeout_counter = 0
        while(True):
            #Attempt to make parent directories (we don't care if this w/ OSError, which means the folders likely already exist)
            try:
                os.makedirs(path)
            except OSError as e:
                pass
            #Big ol' try, anything we catch in here we want to retry up to retry_count
            try:
                #See if we're already locked
                if(os.path.exists(lockfile)):
                    lock_id,lock_pid = get_lockfile_info(lockfile)
                    #Determine if the lockfile is from this host
                    if lock_id == self.host_id:
                        #... is it me?
                        if lock_pid == os.getpid():
                            if self.DEBUG:
                                print("WARN: Found a lockfile that apparently belongs to this process... unlocking.")
                            self.unlock(path)
                        #It's not us, but we can wait if the process is still running
                        elif check_pid(lock_pid):
                            if self.DEBUG:
                                print("INFO: Umpire is waiting " + str((int(config.LOCKFILE_TIMEOUT)-int(timeout_counter)))  + " for an entry to unlock.")
                        #Otherwise we're busting open..
                        else:
                            print("WARN: Removing lockfile from previous Umpire run")
                            self.unlock(path, force=True)
                            continue
                    else: #We really don't know what's going on with this entry, we'll wait the timeout at most before forcing an unlock
                        if self.DEBUG:
                            print("INFO: Umpire is waiting " + str((int(config.LOCKFILE_TIMEOUT)-int(timeout_counter)))  + " for an entry to unlock.")

                    if timeout_counter >= config.LOCKFILE_TIMEOUT:
                        raise EntryLockTimeoutError("Timed out trying to unlock lockfile: " + str(lockfile))

                    timeout_counter += 10
                    time.sleep(10)

                #Write lockfile
                with open(lockfile, 'w') as lf:
                    lf.write(str(self.host_id) + "::" + str(os.getpid()))
                    lf.close()

                #Read back lockfile
                lock_id,lock_pid = get_lockfile_info(lockfile)
                if lock_id == self.host_id and lock_pid == os.getpid():
                    return
                else:
                    raise EntryLockError("Expected to have lock, but lockfile does not contain the correct information.")
            except Exception as e:
                if retry_count <= 0:
                    print("ERROR: Unable to unlock cache entry after several attempts: ")
                    raise e
                else:
                    backoff()
                    if self.DEBUG:
                        print("ERROR: Caught the following exception: " + str(e))
                        traceback.print_exc()
                    retry_count -= 1

    def unlock(self, path, force=False):
        lockfile = os.path.join(path, LOCK_FILENAME)
        pid = -1
        #Read back lockfile
        lock_id,lock_pid = get_lockfile_info(lockfile)
        if (lock_id == self.host_id and lock_pid == os.getpid()) or force is True:
            os.remove(lockfile)
        else:
            raise EntryLockError("This process (" + str(os.getpid()) + ") is not the owner (" + str(pid) + ") of the lockfile it's trying to unlock: " + str(lockfile))

    #Puts an archive of files into the cache
    def put(self, archive_path, platform, name, version, unpack=True, force=False, keep_archive = False, keep_original = False):

        #Generate md5
        local_checksum = maestro.tools.file.md5_checksum(archive_path)

        #Get Archive filename
        archive_filename = os.path.split(archive_path)[1]

        #Get path it would exist in the repo
        full_path = os.path.join(self.local_path, platform, name, version, archive_filename)
        entry_root = os.path.join(self.local_path, platform, name, version)
        case_insensitive_path = maestro.tools.path.get_case_insensitive_path(entry_root)

        #Create directories for lock file if needed
        try:
            os.makedirs(entry_root)
        except OSError as e:
            pass

        #Copy archive to cache location
        shutil.copy(archive_path, entry_root)

        #Remove original if we want
        if keep_original is False:
            os.remove(archive_path)

        unpacker = UnpackModule(None)

       #Unpack if necessary
        if unpack is True:
            unpacker.destination_path = entry_root
            unpacker.file_path = full_path
            unpacker.delete_archive = not keep_archive
            unpacker.start()

        entry = EntryInfo()
        entry.name = name
        entry.version = version
        entry.platform = platform
        entry.path = entry_root
        entry.md5 = local_checksum

        #Write the entry
        write_entry(entry)
        if unpack is True:
            while unpacker.status != maestro.core.module.DONE:
                time.sleep(0.2)

            if unpacker.exception is not None:
                pass #Hack for now in case whatever it is isn't an archive
                #raise unpacker.exception

    #Set the repositories remote URL (updates local .umpire file)
    def set_remote(url):
        pass #TODO: Future


#TODO: Write command line module
if __name__ == "__main__":
    try:
        cache = create_local_cache("./test", "s3://bucketname")
        cache.put("../../poco-1.4.6p2-win64.tar.gz", "win64","poco","1.4.6p2", keep_original = True)
        cache.get("win64","poco","1.4.6p2")
    finally:
        #pass
        shutil.rmtree("./test")
