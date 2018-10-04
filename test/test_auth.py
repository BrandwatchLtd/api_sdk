# coding=utf-8
import unittest
import os

import credentials
from bwproject import BWProject


class TestCredentialsStore(unittest.TestCase):

    def test_auth(self):
        username = os.getenv("BWAPI_USERNAME")
        project = os.getenv("BWAPI_PROJECT")
        _ = BWProject(username=username, project=project, token_path=credentials.DEFAULT_CREDENTIALS_PATH)
