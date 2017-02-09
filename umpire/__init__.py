import os, sys

def get_umpire_cache_root(create_if_missing=True):
    location = os.path.join(get_umpire_home(create_if_missing=create_if_missing),"./cache")
    env_location = None
    try:
        env_location = os.environ['UMPIRE_CACHE_LOCATION']
    except KeyError:
        pass
    finally:
        if env_location:
            location = env_location
    return location

def get_umpire_home(create_if_missing=True):
    location = config.default_umpire_root
    env_location = None
    try:
        env_location =  os.environ['UMPIRE_HOME']
    except KeyError:
        pass
    finally:
        if env_location:
            location = env_location

    if create_if_missing is True:
        create_umpire_home(location)

    return location

def create_umpire_home(location):
    try:
        if not os.path.exists(location):
            os.makedirs(location)
        # Create config, etc... 
    except OSError:
        print("Unable to create umpire home directory in " + str(location) + " Umpire will now close.")
        sys.exit(1)
