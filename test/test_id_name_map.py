import unittest

from bwapi.bwresources import BWQueries
from bwapi.bwproject import BWProject

class StubBWProject():
    '''Stub equivalent of BWProject, which can return enough canned responses to create an instance of BWQueries
    Also contains a canned response to allow BWQueries' get() method to be called and get info about a specific query'''
    def __init__(self, 
                 project = 'MyProject',
                 username = 'user@example.com',
                 password = 'mypassword'
                ):
        self.project = project
        self.username = username
        self.password = password
        self.examples = {'queries':{'resultsTotal': 1,
                          'resultsPage': -1,
                          'resultsPageSize': -1,
                          'results': [{'id': 1111111111,
                            'name': 'My Query',
                            'description': None,
                            'creationDate': '2019-01-01T00:00:00.000+0000',
                            'lastModificationDate': '2019-01-02T00:00:00.000+0000',
                            'industry': 'general-(recommended)',
                            'includedTerms': ['My Query String'],
                            'languages': ['en'],
                            'twitterLimit': 1500,
                            'dailyLimit': 10000,
                            'type': 'search string',
                            'twitterScreenName': None,
                            'highlightTerms': ['my', 'query', 'string'],
                            'samplePercent': 100,
                            'lastModifiedUsername': 'user@example.com',
                            'languageAgnostic': False,
                            'lockedQuery': False,
                            'lockedByUsername': None,
                            'lockedTime': None,
                            'createdByWizard': False,
                            'unlimitedHistoricalData': {'backfillMinDate': '2019-01-01T00:00:00.000+0000',
                            'unlimitedHistoricalDataEnabled': False}}]},
                         'tags':{'resultsTotal': -1,
                              'resultsPage': -1,
                              'resultsPageSize': -1,
                              'results': []},
                         'categories':{'resultsTotal': -1,
                              'resultsPage': -1,
                              'resultsPageSize': -1,
                              'results': []},
        }
        self.examples['specific_query']=self.examples['queries']['results'][0]
        self.apiurl="https://api.brandwatch.com/"
        self.token = 2222222222
    def test_print_project(self):
        '''testing'''
        return self.project

    def get(self, endpoint, params={}):
        '''get without the need for responses library to be used'''
        if endpoint in ['queries', 'tags', 'categories']:
            return self.examples[endpoint]
        elif endpoint.startswith('queries/'): #e.g. the call is for queries/1111111111
            return self.examples['specific_query']  
        else:
            print(endpoint)
            raise NotImplementedError   

class TestBWQueriesCreation(unittest.TestCase):
    '''
    Used to run tests on BWQueries, using the real BWQueries class, but the stubbed version of BWProject
    '''
    def test_create_queries(self):
        test_project = StubBWProject()
        test_queries = BWQueries(test_project)
        return test_queries
    def test_query_get_provide_string(self):
        test_queries = self.test_create_queries()
        return test_queries.get('My Query')
    def test_query_get_provide_id(self):
      '''
      this is the function that before the fix would return TypeError: must be str, not int
      '''
      test_queries = self.test_create_queries()
      return test_queries.get(1111111111) 
 
if __name__ == '__main__':
  unittest.main()	