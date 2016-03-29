#!/usr/bin/python
from umpire.deploy import DeploymentModule

import unittest
import os
import shutil
import sys
import tempfile

deployment_json = """
[
    {
        "url":"s3://umpire-test/",
        "items":[
            {
                "name":"test",
                "version":"test",
                "platform":"test",
                "destination":"$tc2/testA"
            },
            {
                "name":"test",
                "version":"test",
                "platform":"test",
                "destination":"$tc2/testB"
            }
        ]
    }
]
"""

class TC2(unittest.TestCase):
    """
    1. Full deploy from install
    - Run deployment file
    """

    #Currently only on linux
    tempdir = os.path.join(tempfile.gettempdir(), "tc2")
    cache_root = os.path.join(tempdir,"./tc2_cache")
    deployment_file = os.path.join(tempdir,"./tc2_deploy")
    environment_variables = { "tc2" : os.path.join(tempdir,"deployment") }

    # preparing to test
    def setUp(self):
        print("Setting up environment")
        for k, v in self.environment_variables.iteritems():
            os.environ[k] = v
        print("Creating tmp folder.. " + str(self.tempdir))
        os.mkdir(self.tempdir)
        print("Creating deployment file..")
        with open(self.deployment_file, "w+") as f:
            f.write(deployment_json)
    # ending the test
    def tearDown(self):
        """Remove deployment folder"""
        print("Removing temporary folder")
        try:
            shutil.rmtree(self.tempdir)
        except:
            print "Warning, cannot clean up tempdir."

    # test routine A
    def test(self):
        print("Running first deploy...")
        self.deploy()
        self.verify_deploy()
        print("Verified files exist")
        print("Deleting deployment directory")
        shutil.rmtree(os.path.join(self.tempdir,"./deployment"))
        print("Running deploy...")
        self.deploy()
        self.verify_deploy()

    def deploy(self):
        print("Getting deployment module")
        deploy = DeploymentModule()
        deploy.cache_root = self.cache_root
        deploy.deployment_file = self.deployment_file
        deploy.DEBUG = True
        print("Starting deploy and waiting for finish.")
        deploy.run(None)

    def verify_deploy(self):
        with open(os.path.join(self.tempdir,"./deployment/testA/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"HI!\n")

        with open(os.path.join(self.tempdir,"./deployment/testB/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"HI!\n")
