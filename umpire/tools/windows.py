import os
import ctypes
from subprocess import CalledProcessError, check_output


def islink_windows(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
            attributes = ctypes.windll.kernel32.GetFileAttributesW(unicode(path))
            return (attributes & FILE_ATTRIBUTE_REPARSE_POINT) > 0
        else:
            command = ['dir', path]
            try:
                with open(os.devnull, 'w') as NULL_FILE:
                    o0 = check_output(command, stderr=NULL_FILE, shell=True)
            except CalledProcessError as e:
                print e.output
                return False
            o1 = [s.strip() for s in o0.split('\n')]
            if len(o1) < 6:
                return False
            else:
                return 'SYMLINK' in o1[5]
    else:
        return False
