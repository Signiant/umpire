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
                "link":false,
                "unpack":false,
                "destination":"$tc5/testA"
            }
        ]
    }
]
"""

class tc5(unittest.TestCase):
    """
    1. Full deploy from install
    - Run deployment file
    """

    #Currently only on linux
    tempdir = os.path.join(tempfile.gettempdir(), "tc5")
    cache_root = os.path.join(tempdir,"./tc5_cache")
    deployment_file = os.path.join(tempdir,"./tc5_deploy")
    environment_variables = { "tc5" : os.path.join(tempdir,"deployment") }

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
        print("Getting deployment module")
        deploy = DeploymentModule()
        deploy.cache_root = self.cache_root
        deploy.deployment_file = self.deployment_file
        deploy.DEBUG = True
        print("Starting deploy and waiting for finish.")
        deploy.run(None)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir,"./deployment/testA/test_package.tar.gz")))
        self.assertFalse(os.path.islink(os.path.join(self.tempdir,"./deployment/testA/test_package.tar.gz")))
