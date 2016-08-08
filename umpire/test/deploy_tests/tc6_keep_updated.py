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
                "version":"test_tgz",
                "platform":"test",
                "keep_updated":true,
                "link":false,
                "destination":"$tc6/testA"
            },
            {
                "name":"test",
                "version":"test_zip",
                "platform":"test",
                "keep_updated":true,
                "destination":"$tc6/testB"
            }
        ]
    }
]
"""

class TC6(unittest.TestCase):
    """
    1. Modify local and check against remote
    - Run deployment file
    """

    #Currently only on linux
    tempdir = os.path.join(tempfile.gettempdir(), "tc6")
    cache_root = os.path.join(tempdir,"./tc6_cache")
    deployment_file = os.path.join(tempdir,"./tc6_deploy")
    environment_variables = { "tc6" : os.path.join(tempdir,"deployment") }

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

        #A: Verify content is good
        self.assertFalse(os.path.islink(os.path.join(self.tempdir,"./deployment/testA/this_is_test_data")))
        with open(os.path.join(self.tempdir,"./deployment/testA/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"HI!\n")

        #A: Change content
        with open(os.path.join(self.tempdir,"./deployment/testA/this_is_test_data"), "w+") as f:
            f.write("BLAHBLAHBLAH\n")

        #A: Verify content change is good
        with open(os.path.join(self.tempdir,"./deployment/testA/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"BLAHBLAHBLAH\n")

        #B: Verify content is good
        self.assertTrue(os.path.islink(os.path.join(self.tempdir,"./deployment/testB/this_is_test_data")))
        with open(os.path.join(self.tempdir,"./deployment/testB/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"HI!\n")

        #B: Change content
        with open(os.path.join(self.tempdir,"./deployment/testB/this_is_test_data"), "w+") as f:
            f.write("BLAHBLAHBLAH\n")

        #B: Verify content change is good
        with open(os.path.join(self.tempdir,"./deployment/testB/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"BLAHBLAHBLAH\n")

        #Modify checksums of ONLY the first one
        import fileinput, re
        for line in fileinput.input(os.path.join(self.cache_root,"./umpire-test.s3/test/test/test_tgz/.umpire"), inplace = True):
            print re.sub("md5 = ([^\s]+)","md5 = aaaaaaaaa",line)

        #Rerun deploy
        print("Getting deployment module")
        deploy = DeploymentModule()
        deploy.cache_root = self.cache_root
        deploy.deployment_file = self.deployment_file
        deploy.DEBUG = True
        print("Starting deploy and waiting for finish.")
        deploy.run(None)

        #A: Verify content is good
        self.assertFalse(os.path.islink(os.path.join(self.tempdir,"./deployment/testA/this_is_test_data")))
        with open(os.path.join(self.tempdir,"./deployment/testA/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"HI!\n")

        #B: Verify content is good
        self.assertTrue(os.path.islink(os.path.join(self.tempdir,"./deployment/testB/this_is_test_data")))
        with open(os.path.join(self.tempdir,"./deployment/testB/this_is_test_data")) as f:
            lines = f.readlines()
            self.assertEqual(lines[0],"BLAHBLAHBLAH\n")

