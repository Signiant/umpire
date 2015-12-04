"""download.py contains a versatile asynchronous downloader"""

#TODO move to maestro and merge with s3downloader (make this the parent)
#TODO remove name and make destination behave like s3

HELPTEXT = """
                  ----- Download Module -----

The download module will retrieve a file from a specified remote url and
optionally verify the md5. Remote md5 files MUST have the same file path with
.md5 appended to use this feature.

-s, --source <src_url>:         Specify the source URL
                                    (required)
-d, --destination <dest_path>:   Specify the destination file path
                                    (default current directory)
-n, --name <name>:              Specify the destination file name
                                    (default source file name)
-m, --md5:                      Verify the integrity of the remote file

"""

import sys, os, urllib2, requests
from multiprocessing import Value
from maestro.internal.module import *
from maestro.tools.file import read_blocks

SOURCE_URI_KEYS = ["s", "source"]
DESTINATION_URI_KEYS = ["d", "destination"]
DESTINATION_FILENAME_KEYS = ["n", "name"]
CHECK_MD5_KEYS = ["m", "md5"]
HELP_KEYS = ["h", "help"]

class MD5Error(Exception):
    pass

class DownloadError(Exception):
    pass

class DownloadModule(AsyncModule):
    # Required ID of this module
    id = "download"
    
    #Initialize shm value
    progress = Value('d', 0.0)

    #Default block size
    block_size = 8192

    source_url = None
    dest_path = None
    source_md5 = None
    dest_md5 = None
    dest_filename = None
    verify_md5 = False

    def help(self):
        print self.help_text
        exit(0)

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
            if key in HELP_KEYS:
                self.help()
            elif key in SOURCE_URI_KEYS:
                self.source_url = val
            elif key in DESTINATION_URI_KEYS:
                self.dest_url = val
            elif key in DESTINATION_FILENAME_KEYS:
                self.dest_filename = val
            elif key in MD5_CHECK_KEYS:
                self.verify_md5 = True

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
