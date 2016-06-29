import os.path

default_umpire_root = os.path.join(os.path.expanduser("~"), ".umpire")

# Enable on build nodes, or anywhere that doesn't need SUDO
autoupdate = False

#Cache config
CONFIG_FILENAME = ".umpire"
CONFIG_REPO_SECTION_NAME = "umpire"
CONFIG_ENTRY_SECTION_NAME = "entry"
LOCK_FILENAME = ".umplock"
CURRENT_ENTRY_CONFIG_VERSION = "0.1"
CURRENT_REPO_CONFIG_VERSION = "0.1"
CONFIG_FILENAME = ".umpire"
REMOTE_VERSION_FILENAME = os.path.join(default_umpire_root,"remote_version")
REMOTE_VERSION_URL = "http://s3.amazonaws.com/umpire/version"
LOCKFILE_TIMEOUT = 600 # 10 minutes
