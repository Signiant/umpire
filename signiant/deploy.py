"""deploy.py"""

HELPTEXT = """
                  ----- Deploy Module -----

The deploy module reads a deployment JSON file.

Usage: deploy.py <deployment_file>

"""

import sys, os, urllib2, requests
from multiprocessing import Value
from maestro.internal import module
from maestro.aws import s3

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

        downloaders = list()

        for repo in data:
            repo_url = repo["url"]
            for item in repo["items"]:
                name = item["name"]
                version = item["version"]
                platform = item["platform"]
                destination = item["destination"]

                full_url = s3.join_s3_url(repo_url, platform, name, version)
                print full_url
                downloader = s3.AsyncS3Downloader(None)
                downloader.source_url = full_url
                downloader.destination_path = destination
                downloader.start(None)
                downloaders.append(downloader)

        downloader_count = 0
        while downloader_count < len(downloaders):
            downloader_count = 0
            for downloader in downloaders:
                if downloader.status == module.DONE:
                    downloader_count += 1
            time.sleep(1)
        print "Done!"

if __name__ == "__main__":
    dp = DeploymentModule(None)
    dp.run(None)
