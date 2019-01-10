import unittest
import responses
import os
import tempfile

from bwapi.bwproject import BWProject


class TestBWProjectUsernameCaseSensitivity(unittest.TestCase):

    USERNAME = "example@Example.com"
    ACCESS_TOKEN = "00000000-0000-0000-0000-000000000000"
    PROJECT_NAME = "Example project"
    PROJECTS = [
        {
            "id": 0,
            "name": PROJECT_NAME,
            "description": "",
            "billableClientId": 0,
            "billableClientName": "My company",
            "timezone": "Africa/Abidjan",
            "billableClientIsPitch": False,
        }
    ]

    def setUp(self):
        self.token_path = tempfile.NamedTemporaryFile(suffix="-tokens.txt").name

        responses.add(
            responses.GET,
            "https://api.brandwatch.com/projects",
            json={
                "resultsTotal": len(self.PROJECTS),
                "resultsPage": -1,
                "resultsPageSize": -1,
                "results": self.PROJECTS,
            },
            status=200,
        )

        responses.add(
            responses.POST,
            "https://api.brandwatch.com/oauth/token",
            json={"access_token": self.ACCESS_TOKEN},
            status=200,
        )

    def tearDown(self):
        os.unlink(self.token_path)
        responses.reset()

    @responses.activate
    def test_lowercase_username(self):
        self._test_username("example@example.com")

    @responses.activate
    def test_uppercase_username(self):
        self._test_username("EXAMPLE@EXAMPLE.COM")

    @responses.activate
    def test_mixedcase_username(self):
        self._test_username("eXaMpLe@ExAmPlE.cOm")

    def _test_username(self, username):

        responses.add(
            responses.GET,
            "https://api.brandwatch.com/me",
            json={"username": username},
            status=200,
        )

        BWProject(
            username=username,
            project=self.PROJECT_NAME,
            password="",
            token_path=self.token_path,
        )
        try:
            BWProject(
                username=username, project=self.PROJECT_NAME, token_path=self.token_path
            )
        except KeyError as e:
            self.fail(e)


if __name__ == "__main__":
    unittest.main()
