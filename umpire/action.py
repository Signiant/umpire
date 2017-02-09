import sys, shutil
import maestro
from umpire import get_umpire_cache_root
from argparse import Action

### Actions are self contained, they shouldn't affect the rest of the app.
class ClearCache(Action):
    def __call__(self, parser, namespace, values, option_string):
        location = get_umpire_cache_root()
        try:
            shutil.rmtree(location)
        except OSError as e:
            print("Unable to clear cache: " + str(e))
            sys.exit(1)


class RepairLockFiles(Action):
    def __call__(self, parser, namespace, values, option_string, const):
        location = get_umpire_cache_root()
        try:
            maestro.tools.path.purge(location)
        except OSError:
            print("Unable to clear lockfiles: " + str(e))
            sys.exit(1)

