"""unpack.py"""

HELPTEXT = """
     ----- Unpack Module -----

The unpack module unpacks a tar gz or zip file.

Usage: Currently N/A

"""

import sys, os
from maestro.core import module

HELP_KEYS = ["h", "help"]

class UnpackError(Exception):
    pass

class UnpackModule(module.AsyncModule):
    # Required ID of this module
    id = "unpack"
    file_path = None
    destination_path = None
    delete_archive = False

    def help(self):
        print(self.help_text)
        exit(0)

    def untar_gzip(self):
        import tarfile
        with tarfile.open(self.file_path, "r:gz") as f:
            f.extractall(self.destination_path)
        if self.delete_archive is True:
            os.remove(self.file_path)

    def unzip(self):
        import zipfile
        with zipfile.ZipFile(self.file_path) as zf:
            for member in zf.infolist():
                # Path traversal defense copied from
                # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
                words = member.filename.split('/')
                path = self.destination_path
                for word in words[:-1]:
                    drive, word = os.path.splitdrive(word)
                    head, word = os.path.split(word)
                    if word in (os.curdir, os.pardir, ''): continue
                    path = os.path.join(path, word)
                zf.extract(member, path)

    def run(self,kwargs):
        if self.file_path.endswith("tar.gz") or self.file_path.endswith("tgz"):
            self.untar_gzip()
        elif self.file_path.endswith(".zip"):
            self.unzip()
        else:
            raise UnpackError("Unable to unpack this type of file: " + os.path.split(self.file_path)[1])
