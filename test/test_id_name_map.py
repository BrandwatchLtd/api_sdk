import unittest

from bcr.bwresources import BWQueries

query_id = 1111111111


class StubBWProject:
    """Stub equivalent of BWProject, which can return enough canned responses to create an instance of BWQueries
    Also contains a canned response to allow BWQueries' get() method to be called and get info about a specific query"""

    def __init__(
        self, project="MyProject", username="user@example.com", password="mypassword"
    ):
        self.project = project
        self.username = username
        self.password = password
        self.examples = {
            "queries": {
                "resultsTotal": 1,
                "resultsPage": -1,
                "resultsPageSize": -1,
                "results": [
                    {
                        "id": query_id,
                        "name": "My Query",
                        "description": None,
                        "creationDate": "2019-01-01T00:00:00.000+0000",
                        "lastModificationDate": "2019-01-02T00:00:00.000+0000",
                        "industry": "general-(recommended)",
                        "includedTerms": ["My Query String"],
                        "languages": ["en"],
                        "twitterLimit": 1500,
                        "dailyLimit": 10000,
                        "type": "search string",
                        "twitterScreenName": None,
                        "highlightTerms": ["my", "query", "string"],
                        "samplePercent": 100,
                        "lastModifiedUsername": "user@example.com",
                        "languageAgnostic": False,
                        "lockedQuery": False,
                        "lockedByUsername": None,
                        "lockedTime": None,
                        "createdByWizard": False,
                        "unlimitedHistoricalData": {
                            "backfillMinDate": "2019-01-01T00:00:00.000+0000",
                            "unlimitedHistoricalDataEnabled": False,
                        },
                    }
                ],
            },
            "tags": {
                "resultsTotal": -1,
                "resultsPage": -1,
                "resultsPageSize": -1,
                "results": [],
            },
            "categories": {
                "resultsTotal": -1,
                "resultsPage": -1,
                "resultsPageSize": -1,
                "results": [],
            },
        }
        self.examples["specific_query"] = self.examples["queries"]["results"][0]
        self.apiurl = "https://api.brandwatch.com/"
        self.token = 2222222222

    def get(self, endpoint, params={}):
        """get without the need for responses library to be used"""
        if endpoint in ["queries", "tags", "categories"]:
            return self.examples[endpoint]
        elif endpoint.startswith("queries/"):  # e.g. the call is for queries/query_id
            return self.examples["specific_query"]
        else:
            print(endpoint)
            raise NotImplementedError


class TestBWQueriesCreation(unittest.TestCase):
    """
    Used to run tests on BWQueries, using the real BWQueries class, but the stubbed version of BWProject
    """

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(
            self, *args, **kwargs
        )  # prevent this __init__ from overriding unittest testcase's original __init__
        self.project = StubBWProject()
        self.queries = self.test_create_queries()

    def test_create_queries(self):
        test_queries = BWQueries(self.project)
        return test_queries

    def test_query_get_provide_string(self):
        return self.queries.get("My Query")

    def test_query_get_provide_id(self):
        """
      this is the function that before the fix would return TypeError: must be str, not int
      """
        return self.queries.get(query_id)

    def test_query_id_get_equal(self):
        actual = self.test_query_get_provide_string()
        expected = self.test_query_get_provide_id()
        self.assertEqual(actual, expected)

    def test_query_get_provide_None(self):
        """
      can a user pass nothing into queries.get()
      """
        actual = self.queries.get()
        expected = self.project.examples["queries"]["results"][0]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
