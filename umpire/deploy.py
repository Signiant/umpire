"""deploy.py"""

HELPTEXT = """
                  ----- Umpire -----

Umpire reads a properly formatted JSON deployment file to deploy files.
Examples can be found on GitHub: https://github.com/Signiant/umpire

Usage:  umpire <deployment_file>

Options:
--clear-cache, -c:   Clears the default Umpire cache of all packages
--help, -h:          Displays this help text
--repair-cache, -r:  Removes lock files from the cache
--version:           Displays the current version of Umpire

"""

# Define WindowError if we're on Linux
try:
    WindowsError
except NameError:
    WindowsError = None


import sys, os, json, time, traceback, shutil, logging
from distutils import dir_util
from maestro.core import module
from maestro.tools import path
from tqdm import tqdm

#Local modules
from . import fetch, cache
# from cache import CacheError

CACHE_ROOT_KEYS = ["c", "with-cache"]
HELP_KEYS = ["h", "help"]
logger = logging.getLogger(__name__)

## The following code

## The following code backports an islink solution for windows in python 2.7.x
## It gets assigned to a function called "islink"
def islink_windows(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
            attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return (attributes & FILE_ATTRIBUTE_REPARSE_POINT) > 0
        else:
            command = ['dir', path]
            try:
                with open(os.devnull, 'w') as NULL_FILE:
                    o0 = check_output(command, stderr=NULL_FILE, shell=True)
            except CalledProcessError as e:
                logger.error (e.output)
                return False
            o1 = [s.strip() for s in o0.split('\n')]
            if len(o1) < 6:
                return False
            else:
                return 'SYMLINK' in o1[5]
    else:
        return False

islink = os.path.islink
if os.name == "nt":
    import ctypes
    from subprocess import CalledProcessError, check_output
    islink = islink_windows

class DeploymentError(Exception):
    pass

class DeploymentModule(module.AsyncModule):
    # Required ID of this module
    id = "deploy"

    #Cache Root
    cache_root = None

    #Deployment File
    deployment_file = None

    def help(self):
        print(self.help_text)
        exit(0)

    def copyFile(self, src, dst, buffer_size=10485760, perserveFileDate=True):
        #    Check to make sure destination directory exists. If it doesn't create the directory
        dstParent, dstFileName = os.path.split(dst)
        if (not (os.path.exists(dstParent))):
            os.makedirs(dstParent)

        # Optimize the buffer for small files
        buffer_size = min(buffer_size, os.path.getsize(src))
        if (buffer_size == 0):
            buffer_size = 1024

        if shutil._samefile(src, dst):
            raise shutil.Error("`%s` and `%s` are the same file" % (src, dst))
        for fn in [src, dst]:
            try:
                st = os.stat(fn)
            except OSError:
                # File most likely does not exist
                pass
            else:
                # XXX What about other special files? (sockets, devices...)
                if shutil.stat.S_ISFIFO(st.st_mode):
                    raise shutil.SpecialFileError("`%s` is a named pipe" % fn)
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                shutil.copyfileobj(fsrc, fdst, buffer_size)

        if (perserveFileDate):
            shutil.copystat(src, dst)


    def copy_file_with_progress(self, src_file, dst_file):
        # Get the size of the source file
        total_size = os.path.getsize(src_file)

        # Open the source file for reading in binary mode
        with open(src_file, 'rb') as src:
            # Open the destination file for writing in binary mode
            with open(dst_file, 'wb') as dst:
                # Create tqdm instance with total size of the file
                with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024,
                          desc=f'Copying {os.path.basename(src_file)}') as pbar:
                    # Read and write the file in chunks
                    while True:
                        # Read chunk of data from source file
                        data = src.read(4096)
                        if not data:
                            break
                        # Write chunk of data to destination file
                        dst.write(data)
                        # Update progress bar with size of chunk
                        pbar.update(len(data))


    def copy_dir_with_progress(self, src, dst):
        total_size = sum(
            os.path.getsize(os.path.join(root, filename)) for root, _, filenames in os.walk(src) for filename in
            filenames)
        with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc='Copying') as pbar:
            for root, _, filenames in os.walk(src):
                for filename in filenames:
                    src_file = os.path.join(root, filename)
                    dst_file = os.path.join(dst, os.path.relpath(src_file, src))
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy(src_file, dst_file)
                    pbar.update(os.path.getsize(src_file))

    def run(self,kwargs):
        logger.debug("Running Deploy")
        try:
            with open(self.deployment_file) as f:
                data = json.load(f)
        except TypeError:
            print(HELPTEXT)
            sys.exit(1)
        except IOError as e:
            logger.error("Unable to locate file: " + self.deployment_file)
            raise e
            sys.exit(1)

        fetchers = list()

        for repo in data:
            repo_url = repo["url"]
            for item in repo["items"]:

                #Required parameters
                name = item["name"]
                version = item["version"]
                platform = item["platform"]
                destination = os.path.expandvars(item["destination"])

                #Optional parameters
                link = True
                try:
                    link = item["link"]
                except KeyError:
                    #Debugging logging
                    pass
                unpack = True
                try:
                    unpack = item["unpack"]
                except KeyError:
                    #Debugging logging
                    pass
                keep_updated = False
                try:
                    keep_updated = item["keep_updated"]
                except KeyError:
                    pass

                #Configure a Fetch module for each entry
                fetcher = fetch.FetchModule(None)
                fetcher.dependency_name = name
                fetcher.dependency_version = version
                fetcher.dependency_platform = platform
                fetcher.dependency_repo = repo_url
                fetcher.dependency_is_link = link
                fetcher.dependency_unpack = unpack
                fetcher.cache_root = self.cache_root
                fetcher.keep_updated = keep_updated
                # fetcher.DEBUG = self.DEBUG
                #TODO: Figure out how to move this out of deploy
                try:
                    cache_dir =  os.path.join(fetcher.cache_root, fetcher.get_cache_name())
                    cache.create_local_cache(cache_dir, repo_url)
                except cache.CacheError:
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
                    try:
                        os.makedirs(destination)
                    except OSError as e:
                        logger.debug(f"{traceback.print_exc()}")
                        raise DeploymentError(fetcher.format_entry_name() + ": Error attempting to create destination directories.")

                if fetcher.status == module.DONE and fetcher.exception is not None:
                    logger.debug (fetcher.exception.traceback)
                    logger.error (fetcher.format_entry_name() + ": ERROR -- " + str(fetcher.exception))
                    exit_code = 1
                    fetcher.status = module.PROCESSED
                if fetcher.status == module.DONE and fetcher.exception is None:
                    files = fetcher.result[0]
                    state = fetcher.result[1]
                    for entry in files:
                        destination_file = os.path.join(destination,os.path.split(entry)[1])

                        # If the file exists, and points to the same target as the entry
                        if (os.path.exists(destination_file) and islink(destination_file) and state == fetch.EntryState.CACHE and os.path.realpath(entry) == os.path.realpath(destination_file)):
                            logger.info(fetcher.format_entry_name() + ": Already deployed.")
                            fetcher.status = module.PROCESSED
                            break

                        # If the file exists, but something changed between the entry and the destination_file
                        elif (os.path.exists(destination_file) and (state == fetch.EntryState.UPDATED or state == fetch.EntryState.CACHE or state == fetch.EntryState.DOWNLOADED)):
                            logger.info(fetcher.format_entry_name() + ": Updating " + destination_file)
                            self.__remove_and_deploy_to_destination__(fetcher, entry, destination_file)

                        # Wasn't in the cache, or updated.
                        else:
                            logger.info(fetcher.format_entry_name() + ": Deploying " + destination_file)
                            self.__remove_and_deploy_to_destination__(fetcher, entry, destination_file)
                        #TODO: Kinda hacky, no significance other than to make it not DONE
                        fetcher.status = module.PROCESSED

                if fetcher.status == module.PROCESSED:
                    done_count += 1
            time.sleep(0.1)
        return exit_code

    def __remove_and_deploy_to_destination__(self, fetcher, entry, destination_file):
        if os.path.exists(destination_file):
            try:
                if os.path.isdir(destination_file) and not islink(destination_file):
                    try:
                        os.rmdir(destination_file)
                    except OSError as e:
                        shutil.rmtree(destination_file)
                else:
                    os.unlink(destination_file)
            except OSError as e:
                logger.debug(f"{traceback.print_exc()}")
                raise DeploymentError(fetcher.format_entry_name() + ": Unable to remove previously deployed file: " + str(destination_file))
        try:
            if fetcher.dependency_is_link:
                path.symlink(entry, destination_file)
            elif os.path.isdir(entry):
                logger.debug("Copying with tree copy")
                # dir_util.copy_tree(entry, destination_file)
                # shutil.copytree(entry, destination_file, dirs_exist_ok=True)
                self.copy_dir_with_progress(entry, destination_file)
            else:
                logger.debug("Copying with file copy")
                self.copy_file_with_progress(entry, destination_file)
                # self.copy_with_progress(entry, destination_file)
        # except WindowsError as e:
        #     logger.debug(f"{traceback.print_exc()}")
        #     raise DeploymentError(fetcher.format_entry_name() + ": Unable to create symlink. Ensure you are running Umpire as an administrator or otherwise enabled your user to create symlinks. Contact your system administrator if this problem persists.")
        except OSError as e:
            logger.debug(f"{traceback.print_exc()}")
            raise DeploymentError(fetcher.format_entry_name() + ": Unable to deploy: " + str(e))

