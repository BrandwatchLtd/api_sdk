# coding=utf-8
import unittest
import os

import credentials
from bwproject import BWProject


class TestCredentialsStore(unittest.TestCase):

    def test_travis_in_env(self):
        travis = os.getenv("TRAVIS")
        self.assertIsNotNone(travis)

    def test_username_in_env(self):
        username = os.getenv("BWAPI_USERNAME")
        self.assertIsNotNone(username)

    def test_project_in_env(self):
        project_name = os.getenv("BWAPI_PROJECT")
        self.assertIsNotNone(project_name)

    def test_auth(self):
        username = os.getenv("BWAPI_USERNAME")
        project_name = os.getenv("BWAPI_PROJECT")
        project = BWProject(username=username, project=project_name, token_path=credentials.DEFAULT_CREDENTIALS_PATH)
        self.assertIsNotNone(project)
