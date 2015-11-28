"""deploy.py"""

HELPTEXT = """
                  ----- Deploy Module -----

The deploy module reads a deployment JSON file.

Usage: deploy.py <deployment_file>

"""

import sys, os, json
from maestro.internal import module
from maestro.aws import s3

#Local modules
import unpack

HELP_KEYS = ["h", "help"]

class DeploymentModule(module.AsyncModule):
    # Required ID of this module
    id = "deploy"

    def help(self):
        print self.help_text
        exit(0)

    def run(self,kwargs):
        import json, time
        data = None

        with open(sys.argv[1]) as f:
            data = json.load(f)

        fetchers = list()

        for repo in data:
            repo_url = repo["url"]
            for item in repo["items"]:
                name = item["name"]
                version = item["version"]
                platform = item["platform"]
                destination = item["destination"]

                full_url = s3.join_s3_url(repo_url, platform, name, version)
                
                downloader = s3.AsyncS3Downloader(None)
                downloader.source_url = full_url
                downloader.destination_path = destination
                print "Downloading " + full_url
                downloader.start(None)
                downloaders.append(downloader)

        unpacker_count = 0
        unpackers = list()

        downloader_count = 0
        while downloader_count < len(downloaders):
            downloader_count = 0
            for downloader in downloaders:
                if downloader.status == module.DONE:
                    for item in downloader.result:
                        if item.endswith(".tar.gz"):
                            unpacker = unpack.UnpackModule(None)
                            unpacker.file_path = item
                            unpacker.destination_path = os.path.split(item)[0]
                            unpacker.delete_archive = True
                            print "Unpacking " + item
                            unpacker.start(None)
                            unpackers.append(unpacker)
                            downloader.status = 123
                if downloader.status == 123:
                    downloader_count += 1
            time.sleep(0.1)

        while unpacker_count < len(downloaders):
            unpacker_count = 0
            for unpacker in unpackers:
                if unpacker.exception is not None:
                    print "Error in unpacker: " + str(unpacker.exception)
                if unpacker.status == module.DONE:
                    unpacker_count += 1
            time.sleep(0.1)
            
        print "Done!"

if __name__ == "__main__":
    dp = DeploymentModule(None)
    dp.run(None)
