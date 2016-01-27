import os.path

default_umpire_root = os.path.join(os.path.expanduser("~"), ".umpire")

#Cache config
CONFIG_FILENAME = ".umpire"
CONFIG_REPO_SECTION_NAME = "umpire"
CONFIG_ENTRY_SECTION_NAME = "entry"
LOCK_FILENAME = ".umplock"
CURRENT_ENTRY_CONFIG_VERSION = "0.1"
CURRENT_REPO_CONFIG_VERSION = "0.1"
